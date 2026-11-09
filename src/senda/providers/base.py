# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Base schemas and interface for interchangeable SearchProviders."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Normalized search result item across all internal and upstream providers."""
    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Canonical URL")
    snippet: str = Field(default="", description="Snippet or highlighted excerpt")
    source: str = Field(default="Senda", description="Originating provider (Senda, SearXNG, Brave, Mojeek)")
    date: Optional[str] = Field(default=None, description="Publication or indexing ISO date")
    language: Optional[str] = Field(default=None, description="Content language code")
    doc_type: str = Field(default="web", description="Vertical category: web, images, news, videos, library")
    media_url: Optional[str] = Field(default=None, description="Direct thumbnail/media URL for media items")
    is_sponsored: bool = Field(default=False, description="Strict boolean flag. Ads are visually separated and never mixed with organic results.")
    score: float = Field(default=0.0, description="Ranking or BM25 relevance score")
    why_seen: str = Field(default="", description="Honest, transparent explanation of why this result was included and ranked.")


class SearchProvider(ABC):
    """Abstract search provider adapter enforcing zero tracking and header neutralization."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/endpoints are set."""
        pass

    @abstractmethod
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
        """Execute search, strip identifying headers, and normalize output."""
        pass
