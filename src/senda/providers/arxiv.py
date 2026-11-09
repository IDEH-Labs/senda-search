# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""arXiv Open Access Scholarly Search Provider adapter.

Accesses non-peer-reviewed scientific preprints across physics, math, CS, biology and quantitative finance.
Strictly adheres to arXiv API Terms of Use: maximum 1 request per 3 seconds.
Explicitly labels all items as 'Preprint' and 'revisión por pares no verificada'.
"""

from collections import deque
import logging
import time
from typing import Optional, List, Dict, Tuple
import xml.etree.ElementTree as ET
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem
from senda.security.retractions import retraction_registry

logger = logging.getLogger(__name__)

# XML namespaces used by arXiv Atom feed
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivProvider(SearchProvider):
    """Adapter for arXiv preprint repository API."""

    def __init__(
        self,
        email_contact: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
        min_request_interval_seconds: float = 3.0,
        enabled: bool = False,
    ):
        self._enabled = enabled
        self.email_contact = email_contact or getattr(settings, "CONTACT_EMAIL", "contact@ideh.top")
        self.cache_ttl_seconds = cache_ttl_seconds
        self.min_request_interval_seconds = min_request_interval_seconds

        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._last_request_time: float = 0.0

        if not self._enabled:
            logger.info("ArxivProvider: Inactivo por defecto según directriz de gobernanza.")

    @property
    def name(self) -> str:
        return "arXiv (Preprints)"

    @property
    def is_configured(self) -> bool:
        return self._enabled

    def _wait_for_rate_limit(self) -> None:
        """Ensure at least min_request_interval_seconds (3s) between outbound requests."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.min_request_interval_seconds:
            time.sleep(self.min_request_interval_seconds - elapsed)
        self._last_request_time = time.monotonic()

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
    ) -> List[SearchResultItem]:
        if not self.is_configured or not query.strip():
            return []

        clean_q = query.strip()
        cache_key = f"arxiv:{clean_q.lower()}:{page}:{page_size}"

        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        self._wait_for_rate_limit()

        start = (max(page, 1) - 1) * page_size
        max_res = min(max(page_size, 1), 25)

        api_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{clean_q}",
            "start": start,
            "max_results": max_res,
        }

        headers = {
            "User-Agent": f"SendaSearch/1.0 (+https://ideh.top/senda-search; mailto:{self.email_contact})",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"ArxivProvider: Respuesta no exitosa (HTTP {resp.status_code}).")
                    return []
                xml_text = resp.text
        except Exception as e:
            logger.warning(f"ArxivProvider: Error de comunicación: {e}")
            return []

        items = self.parse_response(xml_text, category=category, page_size=page_size)
        self._save_to_cache(cache_key, items)
        return items

    def parse_response(self, xml_text: str, category: str = "library", page_size: int = 10) -> List[SearchResultItem]:
        items: List[SearchResultItem] = []
        try:
            root = ET.fromstring(xml_text)
        except Exception as e:
            logger.warning(f"ArxivProvider: Error al parsear XML: {e}")
            return []

        entries = root.findall("atom:entry", ATOM_NS)
        for entry in entries[:page_size]:
            title_elem = entry.find("atom:title", ATOM_NS)
            if title_elem is None or not title_elem.text:
                continue
            title = " ".join(title_elem.text.split())

            id_elem = entry.find("atom:id", ATOM_NS)
            target_url = id_elem.text.strip() if (id_elem is not None and id_elem.text) else ""
            if not target_url:
                continue

            summary_elem = entry.find("atom:summary", ATOM_NS)
            summary_raw = " ".join(summary_elem.text.split()) if (summary_elem is not None and summary_elem.text) else ""

            published_elem = entry.find("atom:published", ATOM_NS)
            pub_date = published_elem.text[:10] if (published_elem is not None and published_elem.text) else None
            pub_year = pub_date[:4] if pub_date else None

            # Authors
            author_names: List[str] = []
            for author_node in entry.findall("atom:author", ATOM_NS):
                name_node = author_node.find("atom:name", ATOM_NS)
                if name_node is not None and name_node.text:
                    author_names.append(name_node.text.strip())

            if len(author_names) > 3:
                author_summary = ", ".join(author_names[:3]) + " et al."
            elif author_names:
                author_summary = ", ".join(author_names)
            else:
                author_summary = "Autores no especificados"

            # Check DOI if present
            doi_elem = entry.find("arxiv:doi", ATOM_NS)
            doi = doi_elem.text.strip() if (doi_elem is not None and doi_elem.text) else None
            retraction_info = retraction_registry.check(doi) if doi else None

            peer_review_status = "revisión por pares no verificada"
            metadata_header = f"[Preprint | {peer_review_status}]"
            date_str = f"({pub_year}) " if pub_year else ""
            retract_badge = "[OBRA RETRACTADA] " if (retraction_info and retraction_info.status == "retractada") else ""

            snippet = f"{retract_badge}{metadata_header} {date_str}arXiv — {author_summary}. {summary_raw[:160]}..."

            why = (
                f"Preprint científico de acceso abierto obtenido de arXiv. "
                f"Tipo: Preprint. {peer_review_status}."
            )
            if retraction_info and retraction_info.status == "retractada":
                why += f" AVISO: Obra formalmente retractada registrada por {retraction_info.source}."

            items.append(
                SearchResultItem(
                    title=title,
                    url=target_url,
                    canonical_url=target_url,
                    snippet=snippet,
                    source="arXiv (Preprints)",
                    date=pub_year,
                    doc_type="library",
                    source_type="académica",
                    content_type="preprint",
                    published_date=pub_date,
                    authors=author_names,
                    retraction=retraction_info,
                    score=35.0 if category == "library" else 15.0,
                    why_seen=why,
                    provider_origin="arXiv",
                )
            )

        return items
