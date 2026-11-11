# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Mojeek API Provider adapter."""

from typing import Optional, Any
import httpx
from senda.providers.base import SearchProvider, SearchResultItem


class MojeekProvider(SearchProvider):
    """Adapter for Mojeek independent search API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""

    @property
    def name(self) -> str:
        return "Mojeek"

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

        url = "https://api.mojeek.com/search"
        params = {
            "api_key": self.api_key,
            "q": query,
            "s": (page - 1) * page_size,
            "n": page_size,
            "fmt": "json",
        }
        if safe_search in ("moderate", "strict"):
            params["safe"] = "1"
        if lang:
            params["lb"] = lang

        clean_headers = {
            "Accept": "application/json",
            "User-Agent": "SendaProxy/0.1 (Mojeek Integration; Privacy-First)",
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params, headers=clean_headers)
                if resp.status_code != 200:
                    return []
                data = resp.json()
        except Exception:
            return []

        items: list[SearchResultItem] = []
        raw_results = data.get("response", {}).get("results", [])

        for r in raw_results[:page_size]:
            res_url = r.get("url")
            if not res_url:
                continue

            why = (
                "Índice independiente de Mojeek Ltd. "
                "Consulta anonimizada y canalizada a través del proxy ético de Senda."
            )

            items.append(
                SearchResultItem(
                    title=r.get("title", ""),
                    url=res_url,
                    snippet=r.get("desc", ""),
                    source="Mojeek",
                    date=r.get("date"),
                    doc_type="web",
                    is_sponsored=False,
                    score=0.0,
                    why_seen=why,
                )
            )

        return items
