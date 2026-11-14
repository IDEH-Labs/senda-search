# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Open Library (Internet Archive) Search Provider for Senda Search Engine.

Allows finding books, classic literature, authors, and digitized public domain texts
without corporate paywalls or tracking intermediaries.
"""

from collections import deque
import logging
import time
from typing import Optional, List, Dict, Tuple, Any
import urllib.parse
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance

logger = logging.getLogger(__name__)


class OpenLibraryProvider(SearchProvider):
    """Adapter for Open Library Search API."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: float = 6.0,
        rate_limit_per_minute: int = 30,
        cache_ttl_seconds: int = 3600,
        enabled: Optional[bool] = None,
    ):
        self.endpoint = (endpoint or getattr(settings, "OPENLIBRARY_ENDPOINT", "https://openlibrary.org")).rstrip("/")
        self.timeout = timeout
        self.rate_limit_per_minute = rate_limit_per_minute or getattr(settings, "OPENLIBRARY_RATE_LIMIT_PER_MINUTE", 30)
        self.cache_ttl_seconds = cache_ttl_seconds or getattr(settings, "OPENLIBRARY_CACHE_TTL_SECONDS", 3600)
        self._enabled = getattr(settings, "OPENLIBRARY_ENABLED", True) if enabled is None else enabled

        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._request_timestamps: deque = deque()

    @property
    def name(self) -> str:
        return "Open Library (Internet Archive)"

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
        **kwargs: Any,
    ) -> List[SearchResultItem]:
        """Search books and literature records in Open Library."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        cache_key = f"openlibrary:{clean_q}:{page}:{page_size}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self._check_rate_limit():
            logger.warning("OpenLibraryProvider: Rate limit excedido para %s", clean_q)
            return []

        params = {
            "q": clean_q,
            "page": str(max(1, page)),
            "limit": str(min(30, max(1, page_size))),
        }

        api_url = f"{self.endpoint}/search.json?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code != 200:
                    logger.debug("OpenLibrary response status: %s", resp.status_code)
                    return []
                data = resp.json()
                items = self.parse_results(data)
                self._save_to_cache(cache_key, items)
                return items
        except Exception as exc:
            logger.debug("OpenLibrary fetch error: %s", exc)
            return []

    def parse_results(self, data: Dict[str, Any]) -> List[SearchResultItem]:
        """Parse Open Library search.json response into normalized SearchResultItems."""
        items: List[SearchResultItem] = []
        if not isinstance(data, dict):
            return items

        docs = data.get("docs", [])
        if not isinstance(docs, list):
            return items

        for doc in docs:
            if not isinstance(doc, dict):
                continue

            key = doc.get("key", "")
            title = (doc.get("title") or "Sin título").strip()
            authors = doc.get("author_name", [])
            if not isinstance(authors, list):
                authors = [str(authors)] if authors else []
            authors_str = ", ".join(authors[:3]) if authors else "Autoría desconocida"

            year = doc.get("first_publish_year")
            year_str = f" ({year})" if year else ""

            book_url = f"https://openlibrary.org{key}" if key.startswith("/") else f"https://openlibrary.org/works/{key}"
            cover_id = doc.get("cover_i")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None

            # Check if digital lending or full text scan is declared
            has_fulltext = doc.get("has_fulltext", False)
            scan_note = " • Escaneo completo disponible" if has_fulltext else ""

            snippet = f"Libro en catálogo Open Library: {title}{year_str}. Autor(es): {authors_str}{scan_note}."

            items.append(
                SearchResultItem(
                    url=book_url,
                    title=f"{title}{year_str}",
                    snippet=snippet,
                    score=85.0,
                    source="Open Library (Internet Archive)",
                    media_url=cover_url,
                    doc_type="library",
                    date=str(year) if year else None,
                    is_sponsored=False,
                    canonical_url=book_url,
                    source_type="académica",
                    content_type="libro",
                    published_date=str(year) if year else None,
                    authors=authors,
                    provider_origin="Open Library",
                    why_seen="Catálogo universal y biblioteca digital de acceso público (Open Library / Internet Archive).",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )

        return items
