# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Provider Aggregator and Bang Operator Dispatcher for Senda Search."""

import asyncio
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import quote_plus, urlparse

from senda.providers.base import SearchProvider, SearchResultItem
from senda.providers.internal import InternalStorageProvider
from senda.providers.searxng import SearXNGProvider
from senda.providers.brave import BraveSearchProvider
from senda.providers.mojeek import MojeekProvider
from senda.providers.openalex import OpenAlexProvider
from senda.providers.fediverse import FediverseProvider
from senda.providers.bluesky import BlueskyProvider


BANG_SHORTCUTS: Dict[str, Tuple[str, str]] = {
    "!w": ("https://es.wikipedia.org/w/index.php?search={query}", "Wikipedia"),
    "!wen": ("https://en.wikipedia.org/w/index.php?search={query}", "Wikipedia (EN)"),
    "!osm": ("https://www.openstreetmap.org/search?query={query}", "OpenStreetMap"),
    "!ia": ("https://archive.org/search?query={query}", "Internet Archive"),
    "!oa": ("https://openalex.org/works?search={query}", "OpenAlex (Ciencia Abierta)"),
    "!arxiv": ("https://arxiv.org/search/?query={query}&searchtype=all", "arXiv.org"),
    "!gut": ("https://www.gutenberg.org/ebooks/search/?query={query}", "Project Gutenberg"),
    "!fsf": ("https://directory.fsf.org/wiki?search={query}", "Free Software Directory"),
    "!codeberg": ("https://codeberg.org/explore/repos?q={query}", "Codeberg"),
    "!masto": ("https://mastodon.social/search?q={query}", "Mastodon / Fediverso"),
    "!bsky": ("https://bsky.app/search?q={query}", "Bluesky / ATProto"),
    "!ddg": ("https://html.duckduckgo.com/html/?q={query}", "DuckDuckGo (HTML)"),
}


class ProviderAggregator:
    """Aggregates and normalizes multiple SearchProviders with zero-tracking proxying."""

    def __init__(
        self,
        internal_provider: Optional[InternalStorageProvider] = None,
        searxng_provider: Optional[SearXNGProvider] = None,
        brave_provider: Optional[BraveSearchProvider] = None,
        mojeek_provider: Optional[MojeekProvider] = None,
        openalex_provider: Optional[OpenAlexProvider] = None,
        fediverse_provider: Optional[FediverseProvider] = None,
        bluesky_provider: Optional[BlueskyProvider] = None,
    ):
        self.internal = internal_provider or InternalStorageProvider()
        self.searxng = searxng_provider or SearXNGProvider()
        self.brave = brave_provider or BraveSearchProvider()
        self.mojeek = mojeek_provider or MojeekProvider()
        self.openalex = openalex_provider or OpenAlexProvider()
        self.fediverse = fediverse_provider or FediverseProvider()
        self.bluesky = bluesky_provider or BlueskyProvider()

    @staticmethod
    def detect_bang(query: str) -> Optional[Tuple[str, str]]:
        """Detect bang operator shortcut (e.g. !w search term) and return redirect URL."""
        parts = query.strip().split(maxsplit=1)
        if not parts:
            return None
        prefix = parts[0].lower()
        if prefix in BANG_SHORTCUTS:
            term = parts[1] if len(parts) > 1 else ""
            template, service_name = BANG_SHORTCUTS[prefix]
            return template.format(query=quote_plus(term)), service_name
        return None

    async def aggregate(
        self,
        query: str,
        category: str = "all",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        no_ads: bool = True,
        opt_in_academic: bool = False,
        opt_in_social: bool = False,
        boost_domains: Optional[List[str]] = None,
        bury_domains: Optional[List[str]] = None,
        block_domains: Optional[List[str]] = None,
    ) -> List[SearchResultItem]:
        """Query active providers asynchronously, deduplicate, filter ads, and apply lenses."""
        boost_set = set(d.lower().strip() for d in (boost_domains or []))
        bury_set = set(d.lower().strip() for d in (bury_domains or []))
        block_set = set(d.lower().strip() for d in (block_domains or []))

        # Build list of active tasks
        tasks = [
            self.internal.search(
                query, category=category, page=page, page_size=page_size,
                time_filter=time_filter, region=region, safe_search=safe_search
            )
        ]

        if self.searxng.is_configured:
            tasks.append(
                self.searxng.search(
                    query, category=category, page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search
                )
            )

        if self.brave.is_configured:
            tasks.append(
                self.brave.search(
                    query, category=category, page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search
                )
            )

        if self.mojeek.is_configured:
            tasks.append(
                self.mojeek.search(
                    query, category=category, page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search
                )
            )

        # OpenAlex: deactivated in general search by default; strictly isolated to 'library' or explicit opt-in
        should_query_openalex = (category == "library") or (opt_in_academic is True)
        if should_query_openalex and self.openalex.is_configured:
            tasks.append(
                self.openalex.search(
                    query, category=category, page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search
                )
            )

        # Open Social Protocols (Fediverse & Bluesky): isolated strictly to 'social' vertical or explicit opt-in
        should_query_social = (category == "social") or (opt_in_social is True)
        if should_query_social:
            if self.fediverse.is_configured:
                tasks.append(
                    self.fediverse.search(
                        query, category=category, page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search
                    )
                )
            if self.bluesky.is_configured:
                tasks.append(
                    self.bluesky.search(
                        query, category=category, page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search
                    )
                )

        results_batches = await asyncio.gather(*tasks, return_exceptions=True)

        merged: List[SearchResultItem] = []
        seen_urls: set[str] = set()

        for batch in results_batches:
            if isinstance(batch, Exception) or not batch:
                continue
            for item in batch:
                # Deduplication by canonical URL
                norm_url = item.url.rstrip("/").lower()
                if norm_url in seen_urls:
                    continue
                seen_urls.add(norm_url)

                # Ads filtering
                if no_ads and item.is_sponsored:
                    continue

                # Domain filtering (block list)
                try:
                    domain = urlparse(item.url).netloc.lower()
                except Exception:
                    domain = ""

                is_blocked = domain in block_set or any(domain.endswith("." + b) for b in block_set)
                if is_blocked:
                    continue

                # User ranking modification (Lentes / Goggles)
                is_boosted = domain in boost_set or any(domain.endswith("." + b) for b in boost_set)
                is_buried = domain in bury_set or any(domain.endswith("." + b) for b in bury_set)

                if is_boosted:
                    item.score += 50.0
                    item.why_seen += " [Reordenado: Dominio promovido según tus lentes personales]"
                elif is_buried:
                    item.score -= 50.0
                    item.why_seen += " [Reordenado: Dominio relegado según tus lentes personales]"


                merged.append(item)

        # Sort: internal score descending
        merged.sort(key=lambda x: x.score, reverse=True)

        return merged[:page_size]
