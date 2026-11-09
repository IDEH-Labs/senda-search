# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Self-hosted SearXNG Meta-Search Provider adapter."""

from typing import Optional
import httpx
from senda.providers.base import SearchProvider, SearchResultItem


class SearXNGProvider(SearchProvider):
    """Adapter for self-hosted SearXNG instances. Strips headers and normalizes."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or "").rstrip("/")

    @property
    def name(self) -> str:
        return "SearXNG"

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url)

    async def search(
        self,
        query: str,
        category: str = "all",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> list[SearchResultItem]:
        if not self.is_configured:
            return []

        # Map vertical categories to SearXNG format
        cat_map = {
            "all": "general",
            "web": "general",
            "images": "images",
            "news": "news",
            "videos": "videos",
            "library": "science",
        }
        searx_cat = cat_map.get(category.lower(), "general")

        safe_map = {"off": 0, "moderate": 1, "strict": 2}
        safesearch_val = safe_map.get(safe_search, 0)

        params = {
            "q": query,
            "format": "json",
            "categories": searx_cat,
            "pageno": page,
            "safesearch": safesearch_val,
        }
        if time_filter:
            params["time_range"] = time_filter
        if region:
            params["language"] = region

        # Clean sanitized client without identifying headers
        clean_headers = {
            "User-Agent": "SendaProxy/0.1 (Libre Search Engine; No-Tracking)",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=clean_headers,
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
        except Exception:
            return []

        items: list[SearchResultItem] = []
        raw_results = data.get("results", [])

        for r in raw_results[:page_size]:
            url = r.get("url")
            if not url:
                continue
            engine = r.get("engine", "searxng")
            why = (
                f"Obtenido a través de SearXNG (motor de origen: '{engine}'). "
                f"La consulta fue anonimizada por el proxy de Senda."
            )
            items.append(
                SearchResultItem(
                    title=r.get("title", ""),
                    url=url,
                    snippet=r.get("content", ""),
                    source=f"SearXNG ({engine})",
                    date=r.get("publishedDate"),
                    doc_type=category if category != "all" else "web",
                    media_url=r.get("thumbnail_src") or r.get("img_src"),
                    is_sponsored=False,
                    score=float(r.get("score") or 0.0),
                    why_seen=why,
                )
            )
        return items
