# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""DOAJ (Directory of Open Access Journals) Search Provider adapter.

Accesses verified peer-reviewed open access articles indexed in DOAJ under CC BY-SA 4.0 terms.
Provides auditable verification of peer review through DOAJ's curation criteria.
"""

from collections import deque
import logging
import time
from typing import Optional, List, Dict, Tuple
import urllib.parse
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem
from senda.security.retractions import retraction_registry

logger = logging.getLogger(__name__)


class DoajProvider(SearchProvider):
    """Adapter for DOAJ API v2."""

    def __init__(
        self,
        email_contact: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
        rate_limit_per_minute: int = 30,
        enabled: bool = False,
    ):
        self._enabled = enabled
        self.email_contact = email_contact or getattr(settings, "CONTACT_EMAIL", "contact@ideh.top")
        self.cache_ttl_seconds = cache_ttl_seconds
        self.rate_limit_per_minute = rate_limit_per_minute

        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._request_timestamps: deque = deque()

        if not self._enabled:
            logger.info("DoajProvider: Inactivo por defecto según directriz de gobernanza.")

    @property
    def name(self) -> str:
        return "DOAJ (Revistas Revisadas por Pares)"

    @property
    def is_configured(self) -> bool:
        return self._enabled

    def _check_rate_limit(self) -> bool:
        now = time.monotonic()
        while self._request_timestamps and now - self._request_timestamps[0] > 60.0:
            self._request_timestamps.popleft()

        if len(self._request_timestamps) >= self.rate_limit_per_minute:
            return False

        self._request_timestamps.append(now)
        return True

    def _get_from_cache(self, cache_key: str) -> Optional[List[SearchResultItem]]:
        if cache_key in self._cache:
            ts, items = self._cache[cache_key]
            if time.time() - ts < self.cache_ttl_seconds:
                return items
            del self._cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, items: List[SearchResultItem]) -> None:
        if len(self._cache) > 500:
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
    ) -> List[SearchResultItem]:
        if not self.is_configured or not query.strip():
            return []

        clean_q = query.strip()
        cache_key = f"doaj:{clean_q.lower()}:{page}:{page_size}"

        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self._check_rate_limit():
            logger.warning("DoajProvider: Límite de tasa alcanzado.")
            return []

        encoded_q = urllib.parse.quote(clean_q)
        page_size_clamped = min(max(page_size, 1), 25)
        api_url = f"https://doaj.org/api/v2/search/articles/{encoded_q}?page={max(page, 1)}&pageSize={page_size_clamped}"

        headers = {
            "User-Agent": f"SendaSearch/1.0 (+https://ideh.top/senda-search; mailto:{self.email_contact})",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"DoajProvider: Respuesta no exitosa (HTTP {resp.status_code}).")
                    return []
                data = resp.json()
        except Exception as e:
            logger.warning(f"DoajProvider: Error de comunicación: {e}")
            return []

        items = self.parse_response(data, category=category, page_size=page_size)
        self._save_to_cache(cache_key, items)
        return items

    def parse_response(self, data: dict, category: str = "library", page_size: int = 10) -> List[SearchResultItem]:
        items: List[SearchResultItem] = []
        results = data.get("results", [])

        for res in results[:page_size]:
            bibjson = res.get("bibjson", {})
            title = bibjson.get("title", "").strip()
            if not title:
                continue

            # Link
            links = bibjson.get("link", [])
            target_url = None
            for lnk in links:
                if lnk.get("type") == "fulltext":
                    target_url = lnk.get("url")
                    break
            if not target_url and links:
                target_url = links[0].get("url")
            if not target_url:
                continue

            year = bibjson.get("year")
            journal_info = bibjson.get("journal", {})
            journal_title = journal_info.get("title") or "Revista indexada en DOAJ"

            # Authors
            authorships = bibjson.get("author", [])
            author_names: List[str] = [a.get("name", "").strip() for a in authorships if a.get("name")]

            if len(author_names) > 3:
                author_summary = ", ".join(author_names[:3]) + " et al."
            elif author_names:
                author_summary = ", ".join(author_names)
            else:
                author_summary = "Autores no especificados"

            # Check DOI
            identifiers = bibjson.get("identifier", [])
            doi = None
            for ident in identifiers:
                if ident.get("type") == "doi":
                    doi = ident.get("id")
                    break

            retraction_info = retraction_registry.check(doi) if doi else None

            # DOAJ index requires peer review as eligibility criteria
            peer_review_status = "revisada por pares (verificada en DOAJ)"
            retract_badge = "[OBRA RETRACTADA] " if (retraction_info and retraction_info.status == "retractada") else ""
            date_str = f"({year}) " if year else ""
            snippet = f"{retract_badge}[Artículo | {peer_review_status}] {date_str}{journal_title} — {author_summary}."

            why = (
                f"Artículo científico de acceso abierto verificado en el catálogo DOAJ ({journal_title}). "
                f"Revisión por pares formal verificada según rúbrica DOAJ."
            )
            if retraction_info and retraction_info.status == "retractada":
                why += f" AVISO: Obra formalmente retractada registrada por {retraction_info.source}."

            items.append(
                SearchResultItem(
                    title=title,
                    url=target_url,
                    canonical_url=f"https://doi.org/{doi}" if doi else target_url,
                    snippet=snippet,
                    source="DOAJ (Revistas Revisadas)",
                    date=str(year) if year else None,
                    doc_type="library",
                    source_type="académica",
                    content_type="artículo",
                    published_date=str(year) if year else None,
                    authors=author_names,
                    retraction=retraction_info,
                    score=45.0 if category == "library" else 15.0,
                    why_seen=why,
                    provider_origin="DOAJ",
                )
            )

        return items
