# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Brave Search API Provider adapter."""

from typing import Optional, Any
import httpx
from senda.providers.base import SearchProvider, SearchResultItem


class BraveSearchProvider(SearchProvider):
    """Adapter for official Brave Search API. Enforces zero client IP forwarding and honest labelling."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""

    @property
    def name(self) -> str:
        return "Brave Search"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search(
        self,
        query: str,
        category: str = "all",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        lang: Optional[str] = None,
        **kwargs: Any,
    ) -> list[SearchResultItem]:
        if not self.is_configured:
            return []

        # Brave Search API endpoint
        url = "https://api.search.brave.com/res/v1/news/search" if category == "news" else "https://api.search.brave.com/res/v1/web/search"

        clean_headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
            # No user identity, no cookies, no tracking headers
        }

        safe_map = {"off": "off", "moderate": "moderate", "strict": "strict"}
        params = {
            "q": query,
            "count": min(page_size, 20),
            "offset": (page - 1) * page_size,
            "safesearch": safe_map.get(safe_search, "off"),
        }
        if region:
            params["country"] = region
        if lang:
            params["search_lang"] = lang
        if time_filter:
            params["freshness"] = time_filter

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params, headers=clean_headers)
                if resp.status_code != 200:
                    return []
                data = resp.json()
        except Exception:
            return []

        items: list[SearchResultItem] = []
        raw_results = data.get("results", []) if category == "news" else data.get("web", {}).get("results", [])

        for r in raw_results[:page_size]:
            res_url = r.get("url")
            if not res_url:
                continue

            meta_url = r.get("meta_url") or {}
            domain = meta_url.get("netloc") or meta_url.get("hostname")
            source_name = domain or "Brave News" if category == "news" else "Brave Search"

            if category == "news":
                why = (
                    f"Noticia obtenida vía la API oficial de Brave Search para «{source_name}». "
                    "Enlace directo al medio emisor con consulta canalizada por el servidor de Senda sin cookies ni telemetría."
                )
                doc_t = "news"
                src_t = "noticia"
            else:
                why = (
                    "Resultado obtenido vía Brave Search API. Índice web independiente de Brave. "
                    "La consulta fue enviada por el servidor de Senda sin reenviar tu IP ni cookies."
                )
                doc_t = "web"
                src_t = "web"

            items.append(
                SearchResultItem(
                    title=r.get("title", ""),
                    url=res_url,
                    snippet=r.get("description", ""),
                    source=source_name,
                    source_domain=domain,
                    date=r.get("age") or r.get("page_age"),
                    published_date=r.get("age") or r.get("page_age"),
                    language=r.get("language") or lang,
                    doc_type=doc_t,
                    source_type=src_t,
                    content_type=src_t,
                    canonical_url=res_url,
                    is_sponsored=bool(r.get("is_sponsored", False)),
                    score=90.0 if category == "news" else 0.0,
                    why_seen=why,
                )
            )

        return items
