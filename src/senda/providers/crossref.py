# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Crossref REST API Scholarly Search Provider adapter.

Accesses global metadata for academic works, theses, and preprints.
Uses Polite Pool with contact email, enforces client-side rate limiting and caching.
Cross-references Retraction Watch / Crossref retraction data.
Strictly prohibits claiming unverified peer review.
"""

from collections import deque
import logging
import os
import time
from typing import Optional, List, Dict, Any, Tuple
import httpx

from senda.config import settings
from senda.providers.base import (
    SearchProvider,
    SearchResultItem,
    RetractionInfo,
    SourceScoreInfo,
)
from senda.security.retractions import retraction_registry

logger = logging.getLogger(__name__)

# Crossref work types mapped to Spanish
CROSSREF_TYPE_MAP: Dict[str, str] = {
    "journal-article": "Artículo de revista",
    "posted-content": "Preprint",
    "dissertation": "Tesis doctoral / Maestría",
    "dataset": "Dataset",
    "book": "Libro",
    "book-chapter": "Capítulo de libro",
    "proceedings-article": "Ponencia / Conferencia",
    "report": "Informe técnico",
    "standard": "Estándar técnico",
    "editorial": "Editorial",
}


class CrossrefProvider(SearchProvider):
    """Adapter for Crossref REST API under CC0 metadata terms."""

    def __init__(
        self,
        email_contact: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
        rate_limit_per_minute: int = 40,
        enabled: bool = False,
    ):
        self._enabled = enabled
        self.email_contact = email_contact or getattr(settings, "CONTACT_EMAIL", "contact@ideh.top")
        self.cache_ttl_seconds = cache_ttl_seconds
        self.rate_limit_per_minute = rate_limit_per_minute

        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._request_timestamps: deque = deque()

        if not self._enabled:
            logger.info("CrossrefProvider: Inactivo por defecto según directriz de gobernanza.")

    @property
    def name(self) -> str:
        return "Crossref (Ciencia Abierta)"

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
    ) -> List[SearchResultItem]:
        if not self.is_configured or not query.strip():
            return []

        clean_q = query.strip()
        cache_key = f"crossref:{clean_q.lower()}:{page}:{page_size}"

        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self._check_rate_limit():
            logger.warning("CrossrefProvider: Límite de tasa alcanzado. Protegiendo cuota.")
            return []

        api_url = "https://api.crossref.org/works"
        rows = min(max(page_size, 1), 25)
        offset = (max(page, 1) - 1) * rows
        params = {
            "query": clean_q,
            "rows": rows,
            "offset": offset,
        }

        # Polite pool header including contact email
        headers = {
            "User-Agent": f"SendaSearch/1.0 (+https://ideh.top/senda-search; mailto:{self.email_contact})",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                if resp.status_code == 429:
                    logger.warning("CrossrefProvider: Tasa excedida (HTTP 429).")
                    return []
                elif resp.status_code != 200:
                    logger.warning(f"CrossrefProvider: Respuesta no exitosa (HTTP {resp.status_code}).")
                    return []
                data = resp.json()
        except Exception as e:
            logger.warning(f"CrossrefProvider: Error de comunicación: {e}")
            return []

        items = self.parse_response(data, category=category, page_size=page_size)
        self._save_to_cache(cache_key, items)
        return items

    def parse_response(self, data: dict, category: str = "library", page_size: int = 10) -> List[SearchResultItem]:
        items: List[SearchResultItem] = []
        message = data.get("message", {})
        works = message.get("items", [])

        for work in works[:page_size]:
            title_list = work.get("title") or []
            if not title_list or not title_list[0]:
                continue
            title = title_list[0].strip()

            doi = work.get("DOI", "")
            resource_url = work.get("resource", {}).get("primary", {}).get("URL")
            target_url = resource_url or (f"https://doi.org/{doi}" if doi else work.get("URL", ""))
            if not target_url:
                continue

            raw_type = (work.get("type") or "").lower().strip()
            type_label = CROSSREF_TYPE_MAP.get(raw_type, "Obra académica")
            content_type = "preprint" if raw_type == "posted-content" else "artículo"

            # Authors
            author_names: List[str] = []
            for a in work.get("author", []):
                given = a.get("given", "").strip()
                family = a.get("family", "").strip()
                if family and given:
                    author_names.append(f"{given} {family}")
                elif family:
                    author_names.append(family)

            if len(author_names) > 3:
                author_summary = ", ".join(author_names[:3]) + " et al."
            elif author_names:
                author_summary = ", ".join(author_names)
            else:
                author_summary = "Autores no especificados"

            # Publication year
            pub_date = None
            date_parts = work.get("published", {}).get("date-parts", [])
            if date_parts and date_parts[0]:
                pub_parts = date_parts[0]
                pub_date = "-".join(str(p).zfill(2) for p in pub_parts)

            container = work.get("container-title") or []
            journal_name = container[0] if container else "Publicación académica"

            # Check retraction in Crossref metadata or retraction registry
            retraction_info = None
            update_to = work.get("update-to", [])
            is_retracted_in_crossref = any(u.get("type") == "retraction" for u in update_to)
            registry_retraction = retraction_registry.check(doi)

            if is_retracted_in_crossref or registry_retraction:
                retraction_info = registry_retraction or RetractionInfo(
                    status="retractada",
                    source="Crossref",
                    date=pub_date,
                    notice_url=target_url,
                )

            peer_review_status = "revisión por pares no verificada"
            retract_badge = "[OBRA RETRACTADA] " if (retraction_info and retraction_info.status == "retractada") else ""
            meta_header = f"[{type_label} | {peer_review_status}]"
            date_str = f"({pub_date[:4]}) " if pub_date else ""
            snippet = f"{retract_badge}{meta_header} {date_str}{journal_name} — {author_summary}."

            why = (
                f"Publicación académica obtenida vía Crossref ({journal_name}). "
                f"Tipo: {type_label}. {peer_review_status}."
            )
            if retraction_info and retraction_info.status == "retractada":
                why += f" AVISO: Obra formalmente retractada registrada por {retraction_info.source}."

            items.append(
                SearchResultItem(
                    title=title,
                    url=target_url,
                    canonical_url=f"https://doi.org/{doi}" if doi else target_url,
                    snippet=snippet,
                    source="Crossref",
                    date=pub_date[:4] if pub_date else None,
                    doc_type="library",
                    source_type="académica",
                    content_type=content_type,
                    published_date=pub_date,
                    authors=author_names,
                    retraction=retraction_info,
                    score=40.0 if category == "library" else 15.0,
                    why_seen=why,
                    provider_origin="Crossref",
                )
            )

        return items
