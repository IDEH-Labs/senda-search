# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Local sovereign SQLite FTS5 Storage Provider adapter."""

from typing import Optional
from senda.indexer.storage import StorageEngine
from senda.ranking.retriever import SearchRetriever
from senda.providers.base import SearchProvider, SearchResultItem


class InternalStorageProvider(SearchProvider):
    """Adapter for Senda's local SQLite FTS5 database and BM25 ranking."""

    def __init__(self, storage: Optional[StorageEngine] = None):
        self.storage = storage or StorageEngine()
        self.retriever = SearchRetriever(self.storage)

    @property
    def name(self) -> str:
        return "Senda Local"

    @property
    def is_configured(self) -> bool:
        return True

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
        cat = category.lower().strip()
        if cat in ("all", "web", "news", "images", "library"):
            search_cat = cat
        else:
            search_cat = "all"

        raw_results = self.retriever.search(
            query=query,
            page=page,
            page_size=page_size,
            category=search_cat,
        )

        items: list[SearchResultItem] = []
        for it in raw_results.items:
            density_str = ""
            why = (
                f"Índice local Senda. Relevancia léxica BM25: {it.relevance_score:.2f}. "
                f"Ordenado por densidad de texto y coincidencia exacta. Cero perfiles o rastreo."
            )
            items.append(
                SearchResultItem(
                    title=it.title,
                    url=it.url,
                    snippet=it.snippet,
                    source="Senda Local",
                    date=it.published_at,
                    doc_type=it.doc_type,
                    media_url=it.media_url,
                    is_sponsored=False,
                    score=it.relevance_score,
                    why_seen=why,
                )
            )
        return items
