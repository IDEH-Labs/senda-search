# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""PubMed / NCBI E-utilities Scholarly Search Provider adapter.

Accesses biomedical literature indexed in MEDLINE/PubMed.
Adheres strictly to NCBI E-utilities requirements: mandatory 'tool' and 'email' parameters.
Enforces client-side rate limit (3 requests/second).
"""

from collections import deque
import logging
import time
from typing import Optional, List, Dict, Tuple
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem
from senda.security.retractions import retraction_registry

logger = logging.getLogger(__name__)


class PubMedProvider(SearchProvider):
    """Adapter for NCBI E-utilities (PubMed)."""

    def __init__(
        self,
        email_contact: Optional[str] = None,
        tool_name: str = "SendaSearch",
        cache_ttl_seconds: int = 3600,
        min_request_interval_seconds: float = 0.35,  # ~3 req/s
        enabled: bool = False,
    ):
        self._enabled = enabled
        self.email_contact = email_contact or getattr(settings, "CONTACT_EMAIL", "contact@ideh.top")
        self.tool_name = tool_name
        self.cache_ttl_seconds = cache_ttl_seconds
        self.min_request_interval_seconds = min_request_interval_seconds

        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._last_request_time: float = 0.0

        if not self._enabled:
            logger.info("PubMedProvider: Inactivo por defecto según directriz de gobernanza.")

    @property
    def name(self) -> str:
        return "PubMed (Biomedicina)"

    @property
    def is_configured(self) -> bool:
        return self._enabled

    def _wait_for_rate_limit(self) -> None:
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
        cache_key = f"pubmed:{clean_q.lower()}:{page}:{page_size}"

        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        self._wait_for_rate_limit()

        # Step 1: E-search to get PMIDs
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        esearch_params = {
            "db": "pubmed",
            "term": clean_q,
            "retmode": "json",
            "retmax": min(max(page_size, 1), 20),
            "retstart": (max(page, 1) - 1) * page_size,
            "tool": self.tool_name,
            "email": self.email_contact,
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp1 = await client.get(esearch_url, params=esearch_params)
                if resp1.status_code != 200:
                    return []
                id_list = resp1.json().get("esearchresult", {}).get("idlist", [])
                if not id_list:
                    return []

                self._wait_for_rate_limit()

                # Step 2: E-summary to get document metadata
                esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                esummary_params = {
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "retmode": "json",
                    "tool": self.tool_name,
                    "email": self.email_contact,
                }
                resp2 = await client.get(esummary_url, params=esummary_params)
                if resp2.status_code != 200:
                    return []
                data = resp2.json()
        except Exception as e:
            logger.warning(f"PubMedProvider: Error de comunicación: {e}")
            return []

        items = self.parse_response(data, category=category, page_size=page_size)
        self._save_to_cache(cache_key, items)
        return items

    def parse_response(self, data: dict, category: str = "library", page_size: int = 10) -> List[SearchResultItem]:
        items: List[SearchResultItem] = []
        result_dict = data.get("result", {})
        uids = result_dict.get("uids", [])

        for uid in uids[:page_size]:
            doc = result_dict.get(uid, {})
            title = doc.get("title", "").strip().rstrip(".")
            if not title:
                continue

            target_url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
            source_journal = doc.get("source", "Revista biomédica")
            pub_date = doc.get("pubdate", "")
            year = pub_date[:4] if pub_date else None

            # Authors
            authors_raw = doc.get("authors", [])
            author_names: List[str] = [a.get("name", "").strip() for a in authors_raw if a.get("name")]
            if len(author_names) > 3:
                author_summary = ", ".join(author_names[:3]) + " et al."
            elif author_names:
                author_summary = ", ".join(author_names)
            else:
                author_summary = "Autores biomédicos"

            # Check DOI
            article_ids = doc.get("articleids", [])
            doi = None
            for aid in article_ids:
                if aid.get("idtype") == "doi":
                    doi = aid.get("value")
                    break

            retraction_info = retraction_registry.check(doi) if doi else None

            peer_review_status = "revisión por pares no verificada"
            retract_badge = "[OBRA RETRACTADA] " if (retraction_info and retraction_info.status == "retractada") else ""
            date_str = f"({year}) " if year else ""
            snippet = f"{retract_badge}[Artículo biomédico | {peer_review_status}] {date_str}{source_journal} — {author_summary}."

            why = (
                f"Publicación biomédica obtenida de PubMed/NCBI ({source_journal}). "
                f"PMID: {uid}. {peer_review_status}."
            )
            if retraction_info and retraction_info.status == "retractada":
                why += f" AVISO: Obra formalmente retractada registrada por {retraction_info.source}."

            items.append(
                SearchResultItem(
                    title=title,
                    url=target_url,
                    canonical_url=f"https://doi.org/{doi}" if doi else target_url,
                    snippet=snippet,
                    source="PubMed (Biomedicina)",
                    date=year,
                    doc_type="library",
                    source_type="académica",
                    content_type="artículo",
                    published_date=pub_date,
                    authors=author_names,
                    retraction=retraction_info,
                    score=40.0 if category == "library" else 15.0,
                    why_seen=why,
                    provider_origin="PubMed",
                )
            )

        return items
