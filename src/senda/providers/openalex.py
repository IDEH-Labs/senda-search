# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""OpenAlex Open Access Scholarly Search Provider adapter.

Accesses peer-reviewed and preprint scientific literature via the OpenAlex global catalog.
Strictly requires OPENALEX_API_KEY from environment to operate.
Enforces client-side caching (1 credit per list query), rate-limiting, and error handling for 409/429.
"""

from collections import deque
import logging
import os
import time
from typing import Optional, List, Dict, Any, Tuple
import httpx
from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, RetractionInfo
from senda.security.retractions import retraction_registry

logger = logging.getLogger(__name__)


# Real document types mapped to Spanish
TYPE_MAP: Dict[str, str] = {
    "article": "Artículo",
    "preprint": "Preprint",
    "dissertation": "Tesis doctoral / Maestría",
    "dataset": "Dataset",
    "book": "Libro",
    "book-chapter": "Capítulo de libro",
    "editorial": "Editorial",
    "letter": "Carta académica",
    "report": "Informe técnico",
    "standard": "Estándar técnico",
    "peer-review": "Revisión formal",
}

# Open access document versions
VERSION_MAP: Dict[str, str] = {
    "publishedversion": "Versión publicada",
    "acceptedversion": "Versión aceptada",
    "submittedversion": "Versión enviada / Preprint",
}


class OpenAlexProvider(SearchProvider):
    """Adapter for OpenAlex global open access scholarly catalog.
    
    Accesses scientific works, theses, and preprints.
    Requires OPENALEX_API_KEY from environment to prevent unauthenticated credit exhaustion.
    Never logs or persists API credentials.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        email_contact: Optional[str] = None,
        cache_ttl_seconds: Optional[int] = None,
        rate_limit_per_minute: Optional[int] = None,
        enabled: bool = True,
    ):
        self._enabled = enabled
        # 1. Read API key exclusively from explicit argument or environment
        env_key = os.environ.get("OPENALEX_API_KEY") or getattr(settings, "OPENALEX_API_KEY", "") or ""
        resolved_key = (api_key if api_key is not None else env_key).strip()

        self._api_key = resolved_key if enabled else ""
        self.email_contact = email_contact or getattr(settings, "CONTACT_EMAIL", "contact@ideh.top")
        self.cache_ttl_seconds = cache_ttl_seconds or getattr(settings, "OPENALEX_CACHE_TTL_SECONDS", 3600)
        self.rate_limit_per_minute = rate_limit_per_minute or getattr(settings, "OPENALEX_RATE_LIMIT_PER_MINUTE", 30)

        # In-memory response cache: cache_key -> (timestamp, list[SearchResultItem])
        self._cache: Dict[str, Tuple[float, list[SearchResultItem]]] = {}
        # Sliding-window rate limiting timestamps
        self._request_timestamps: deque = deque()

        if not self._api_key and self._enabled:
            logger.warning(
                "OpenAlexProvider: Variable de entorno OPENALEX_API_KEY no configurada. "
                "El proveedor de ciencia abierta permanecerá inactivo para evitar agotamiento de créditos compartidos."
            )

    @property
    def name(self) -> str:
        return "OpenAlex (Ciencia Abierta)"

    @property
    def is_configured(self) -> bool:
        """Provider is active exclusively when enabled and a valid API key is present."""
        return self._enabled and bool(self._api_key)

    def _check_rate_limit(self) -> bool:
        """Enforce credit budget rate limiting (1 list query = 1 credit).
        
        Returns True if request is allowed, False if limit exceeded.
        """
        now = time.monotonic()
        # Evict timestamps older than 60 seconds
        while self._request_timestamps and now - self._request_timestamps[0] > 60.0:
            self._request_timestamps.popleft()

        if len(self._request_timestamps) >= self.rate_limit_per_minute:
            return False

        self._request_timestamps.append(now)
        return True

    def _get_from_cache(self, cache_key: str) -> Optional[list[SearchResultItem]]:
        """Retrieve cached results if fresh within TTL."""
        if cache_key in self._cache:
            ts, items = self._cache[cache_key]
            if time.time() - ts < self.cache_ttl_seconds:
                return items
            del self._cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, items: list[SearchResultItem]) -> None:
        """Cache results to avoid credit re-consumption."""
        # Evict old entries if cache grows beyond 1000 items
        if len(self._cache) > 1000:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[cache_key] = (time.time(), items)

    async def search(
        self,
        query: str,
        category: str = "library",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        lang: Optional[str] = None,
        **kwargs,
    ) -> list[SearchResultItem]:
        """Query OpenAlex for verified Open Access scientific publications."""
        if not self.is_configured or not query.strip():
            return []

        clean_q = query.strip()
        cache_key = f"{clean_q.lower()}:{page}:{page_size}:{category}:{time_filter or ''}"

        # 1. Check local TTL cache to avoid burning 1 credit
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # 2. Check rate limit
        if not self._check_rate_limit():
            logger.warning(
                f"OpenAlexProvider: Límite de tasa alcanzado ({self.rate_limit_per_minute} consultas/min). "
                "Protegiendo presupuesto de créditos de la API."
            )
            return []

        # OpenAlex works endpoint
        api_url = "https://api.openalex.org/works"

        # Parameters enforcing strictly Open Access (no toll-walls, no paywalls)
        params = {
            "search": clean_q,
            "filter": "is_oa:true",
            "select": "id,doi,title,publication_year,type,open_access,primary_location,authorships",
            "per_page": min(max(page_size, 1), 25),
            "page": max(page, 1),
            "api_key": self._api_key,
        }

        clean_headers = {
            "User-Agent": f"SendaSearch/0.1 (+https://ideh.top/senda-search; mailto:{self.email_contact})",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(api_url, params=params, headers=clean_headers)

                # Error handling for rate limits and conflicts
                if resp.status_code == 429:
                    logger.warning("OpenAlexProvider: Límite de créditos/tasa excedido (HTTP 429 Too Many Requests).")
                    return []
                elif resp.status_code == 409:
                    logger.warning("OpenAlexProvider: Conflicto en la consulta (HTTP 409 Conflict).")
                    return []
                elif resp.status_code != 200:
                    logger.warning(f"OpenAlexProvider: Respuesta no exitosa (HTTP {resp.status_code}).")
                    return []

                data = resp.json()
        except httpx.TimeoutException:
            logger.warning("OpenAlexProvider: Tiempo de espera agotado al consultar OpenAlex.")
            return []
        except Exception as e:
            logger.warning(f"OpenAlexProvider: Error de red o comunicación: {e}")
            return []

        items = self.parse_response(data, category=category, page_size=page_size)

        # Cache successfully parsed items
        self._save_to_cache(cache_key, items)
        return items

    def parse_response(self, data: dict, category: str = "library", page_size: int = 10) -> list[SearchResultItem]:
        """Parse and normalize OpenAlex JSON response into SearchResultItem objects."""
        items: list[SearchResultItem] = []
        works = data.get("results", [])

        for work in works[:page_size]:
            title = work.get("title")
            if not title:
                continue

            # Determine best canonical URL (priority: direct OA link -> PDF -> DOI -> landing page)
            oa_data = work.get("open_access") or {}
            prim_loc = work.get("primary_location") or {}
            source_info = prim_loc.get("source") or {}

            best_url = (
                oa_data.get("oa_url")
                or prim_loc.get("pdf_url")
                or prim_loc.get("landing_page_url")
                or work.get("doi")
                or work.get("id")
            )
            if not best_url:
                continue

            year = work.get("publication_year")
            journal_name = source_info.get("display_name") or "Repositorio Abierto"

            # 2. Real document type and version (No generic peer-reviewed claim)
            raw_type = (work.get("type") or "").lower().strip()
            type_label = TYPE_MAP.get(raw_type, raw_type.capitalize() if raw_type else "Obra académica")

            raw_version = (oa_data.get("version") or prim_loc.get("version") or "").lower().strip()
            version_label = VERSION_MAP.get(raw_version, "Versión no especificada")

            # Rigorous transparency: explicit peer review verification status
            peer_review_status = "revisión por pares no verificada"

            # Format authors snippet
            authorships = work.get("authorships") or []
            author_names: List[str] = []
            for a in authorships[:3]:
                auth = a.get("author") or {}
                name = auth.get("display_name")
                if name:
                    author_names.append(name)

            if len(authorships) > 3:
                author_summary = ", ".join(author_names) + " et al."
            elif author_names:
                author_summary = ", ".join(author_names)
            else:
                author_summary = "Autores académicos"

            # Retraction detection via OpenAlex flag or RetractionRegistry
            doi = work.get("doi")
            is_retracted = work.get("is_retracted", False)
            reg_retraction = retraction_registry.check(doi) if doi else None

            retraction_info = None
            if is_retracted or reg_retraction:
                retraction_info = reg_retraction or RetractionInfo(
                    status="retractada",
                    source="OpenAlex / Retraction Watch",
                    date=str(year) if year else None,
                    notice_url=best_url,
                )

            # Construct informative, honest snippet
            year_str = f"({year}) " if year else ""
            has_pdf = bool(oa_data.get("oa_url") or prim_loc.get("pdf_url"))
            badge_pdf = "[PDF Abierto] " if has_pdf else ""
            retract_badge = "[OBRA RETRACTADA] " if (retraction_info and retraction_info.status == "retractada") else ""
            
            # Format: [Tipo | Versión | Estado de revisión]
            metadata_header = f"[{type_label} | {version_label} | {peer_review_status}]"
            snippet = f"{retract_badge}{metadata_header} {badge_pdf}{year_str}{journal_name} — {author_summary}."

            why = (
                f"Publicación académica ({type_label}, {version_label}, {peer_review_status}). "
                f"Obtenida a través de OpenAlex ({journal_name}). Consulta anónima canalizada por Senda."
            )
            if retraction_info and retraction_info.status == "retractada":
                why += f" AVISO: Obra formalmente retractada registrada por {retraction_info.source}."

            # Assign score: in 'library' vertical give priority
            base_score = 45.0 if category == "library" else 15.0

            content_type_val = "preprint" if raw_type == "preprint" else ("tesis" if "dissertation" in raw_type else "artículo")

            items.append(
                SearchResultItem(
                    title=title,
                    url=best_url,
                    canonical_url=doi if doi else best_url,
                    snippet=snippet,
                    source="Ciencia Abierta (OpenAlex)",
                    date=str(year) if year else None,
                    doc_type="library",
                    source_type="académica",
                    content_type=content_type_val,
                    published_date=str(year) if year else None,
                    authors=author_names,
                    retraction=retraction_info,
                    media_url=None,
                    is_sponsored=False,
                    score=base_score,
                    why_seen=why,
                    provider_origin="OpenAlex",
                )
            )

        return items
