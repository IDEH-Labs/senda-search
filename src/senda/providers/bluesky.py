# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Ethical ATProto (Bluesky) Search Provider for Senda.

Strictly queries public ATProto directory search endpoints without tracking,
cookies, or personal account requirements. Isolated to 'social' vertical or opt-in.
"""

from typing import List, Optional
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance


class BlueskyProvider(SearchProvider):
    """ATProto public directory post search provider."""

    def __init__(
        self,
        endpoint: str = "https://api.bsky.app",
        enabled: bool = True,
        timeout: float = 6.0,
    ):
        self.endpoint = endpoint.strip().rstrip("/")
        self.enabled = enabled
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "bluesky"

    @property
    def is_configured(self) -> bool:
        return bool(self.enabled and self.endpoint)

    async def search(
        self,
        query: str,
        category: str = "social",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> List[SearchResultItem]:
        """Query public ATProto searchPosts endpoint."""
        if not self.is_configured:
            return []

        clean_q = query.strip()
        if not clean_q:
            return []

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        search_url = f"{self.endpoint}/xrpc/app.bsky.feed.searchPosts"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    search_url,
                    params={"q": clean_q, "limit": page_size},
                    headers=headers,
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
        except Exception:
            return []

        posts = data.get("posts", [])
        return self._parse_posts(posts)[:page_size]

    def _parse_posts(self, posts: List[dict]) -> List[SearchResultItem]:
        """Convert ATProto post items into SearchResultItems."""
        items: List[SearchResultItem] = []
        for p in posts:
            if not isinstance(p, dict):
                continue

            author = p.get("author") or {}
            handle = author.get("handle") or "usuario"
            display_name = author.get("displayName") or handle
            uri = p.get("uri") or ""
            rkey = uri.rsplit("/", 1)[-1] if "/" in uri else uri
            post_url = f"https://bsky.app/profile/{handle}/post/{rkey}"

            record = p.get("record") or {}
            text = record.get("text") or record.get("bridgyOriginalText") or ""
            created_at = record.get("createdAt") or p.get("indexedAt")

            if not text:
                continue

            title_text = f"@{handle}: {text[:70]}"
            if len(text) > 70:
                title_text += "…"

            items.append(
                SearchResultItem(
                    url=post_url,
                    title=title_text,
                    snippet=text,
                    score=65.0,
                    source="ATProto (Bluesky)",
                    why_seen="Publicación pública en protocolo federado abierto (ATProto). Sin cookies publicitarias ni venta de perfiles.",
                    doc_type="social",
                    date=created_at,
                    is_sponsored=False,
                    canonical_url=post_url,
                    source_type="red_abierta",
                    content_type="publicación",
                    published_date=created_at,
                    authors=[f"@{handle} ({display_name})"],
                    provider_origin="ATProto",
                    ai_provenance=AIProvenance(
                        declared_signal=None,
                        status="no determinado",
                    ),
                )
            )
        return items
