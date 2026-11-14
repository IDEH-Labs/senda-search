# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Lemmy Federated Forum Search Provider for Senda Search Engine.

Connects to decentralized, federated ActivityPub forums (Lemmy / Kbin)
without corporate tracking, dark patterns, or algorithmic engagement slop.
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


class LemmyProvider(SearchProvider):
    """Adapter for Lemmy API v3 Search."""

    def __init__(
        self,
        instance: Optional[str] = None,
        timeout: float = 6.0,
        rate_limit_per_minute: int = 30,
        cache_ttl_seconds: int = 1800,
        enabled: Optional[bool] = None,
    ):
        self.instance = (instance or getattr(settings, "LEMMY_INSTANCE", "lemmy.world")).strip()
        self.timeout = timeout
        self.rate_limit_per_minute = rate_limit_per_minute or getattr(settings, "LEMMY_RATE_LIMIT_PER_MINUTE", 30)
        self.cache_ttl_seconds = cache_ttl_seconds or getattr(settings, "LEMMY_CACHE_TTL_SECONDS", 1800)
        self._enabled = getattr(settings, "LEMMY_ENABLED", True) if enabled is None else enabled

        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._request_timestamps: deque = deque()

    @property
    def name(self) -> str:
        return "Lemmy (Foros Federados)"

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
        category: str = "community",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        lang: Optional[str] = None,
        **kwargs: Any,
    ) -> List[SearchResultItem]:
        """Search federated discussions in Lemmy network."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        cache_key = f"lemmy:{self.instance}:{clean_q}:{page}:{page_size}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self._check_rate_limit():
            logger.warning("LemmyProvider: Rate limit excedido para %s", clean_q)
            return []

        params = {
            "q": clean_q,
            "type_": "Posts",
            "sort": "TopMonth",
            "page": str(max(1, page)),
            "limit": str(min(25, max(1, page_size))),
        }

        api_url = f"https://{self.instance}/api/v3/search?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code != 200:
                    logger.debug("Lemmy response status: %s", resp.status_code)
                    return []
                data = resp.json()
                items = self.parse_results(data)
                self._save_to_cache(cache_key, items)
                return items
        except Exception as exc:
            logger.debug("Lemmy fetch error: %s", exc)
            return []

    def parse_results(self, data: Dict[str, Any]) -> List[SearchResultItem]:
        """Parse Lemmy API v3 search response into normalized SearchResultItems."""
        items: List[SearchResultItem] = []
        if not isinstance(data, dict):
            return items

        posts = data.get("posts", [])
        if not isinstance(posts, list):
            return items

        for post_view in posts:
            if not isinstance(post_view, dict):
                continue

            post_data = post_view.get("post", {})
            creator = post_view.get("creator", {})
            community = post_view.get("community", {})
            counts = post_view.get("counts", {})

            title = (post_data.get("name") or "Publicación comunitaria").strip()
            body = (post_data.get("body") or "").strip()
            published = post_data.get("published")
            post_id = post_data.get("id")

            # Canonical URL is ActivityPub URL or local web instance URL
            target_url = post_data.get("ap_id") or f"https://{self.instance}/post/{post_id}"

            community_name = community.get("name") or "comunidad"
            author_name = creator.get("name") or "anónimo"
            score = counts.get("score", 0)
            comments = counts.get("comments", 0)

            body_preview = body[:200].replace("\n", " ") if body else ""
            snippet = f"En !{community_name} por @{author_name} ({score} votos, {comments} comentarios): {body_preview}".strip()

            items.append(
                SearchResultItem(
                    url=target_url,
                    title=title,
                    snippet=snippet,
                    score=75.0,
                    source=f"Lemmy (!{community_name})",
                    doc_type="community",
                    date=published,
                    is_sponsored=False,
                    canonical_url=target_url,
                    source_type="red_abierta",
                    content_type="opinión",
                    published_date=published,
                    authors=[f"@{author_name}@{self.instance}"],
                    provider_origin="Lemmy",
                    why_seen=f"Discusión comunitaria en red federada ActivityPub (Lemmy en {self.instance}), sin algoritmos de adicción ni rastreo corporativo.",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )

        return items
