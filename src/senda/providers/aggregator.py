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
from senda.providers.wikipedia import WikipediaSearchProvider
from senda.providers.news import RealTimeNewsProvider
from senda.providers.images import FreeCultureImageProvider
from senda.providers.videos import EthicalVideoProvider
from senda.providers.crossref import CrossrefProvider
from senda.providers.doaj import DoajProvider
from senda.providers.arxiv import ArxivProvider
from senda.providers.pubmed import PubMedProvider
from senda.ranking.clustering import apply_domain_clustering
from senda.ranking.goggles import get_preset_goggle, apply_goggle_rules, parse_goggle_dsl
from senda.ranking.anti_slop import apply_anti_slop_filter
from senda.ranking.navigational import NavigationalEngine


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
        wikipedia_search_provider: Optional[WikipediaSearchProvider] = None,
        news_provider: Optional[RealTimeNewsProvider] = None,
        image_provider: Optional[FreeCultureImageProvider] = None,
        video_provider: Optional[EthicalVideoProvider] = None,
        crossref_provider: Optional[CrossrefProvider] = None,
        doaj_provider: Optional[DoajProvider] = None,
        arxiv_provider: Optional[ArxivProvider] = None,
        pubmed_provider: Optional[PubMedProvider] = None,
    ):
        self.internal = internal_provider or InternalStorageProvider()
        self.searxng = searxng_provider or SearXNGProvider()
        self.brave = brave_provider or BraveSearchProvider()
        self.mojeek = mojeek_provider or MojeekProvider()
        self.openalex = openalex_provider or OpenAlexProvider()
        self.fediverse = fediverse_provider or FediverseProvider()
        self.bluesky = bluesky_provider or BlueskyProvider()
        self.wikipedia_search = wikipedia_search_provider
        self.news = news_provider
        self.images = image_provider
        self.videos = video_provider or EthicalVideoProvider()
        self.crossref = crossref_provider
        self.doaj = doaj_provider
        self.arxiv = arxiv_provider
        self.pubmed = pubmed_provider

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
        sort: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        no_ads: bool = True,
        opt_in_academic: bool = False,
        opt_in_social: bool = False,
        boost_domains: Optional[List[str]] = None,
        bury_domains: Optional[List[str]] = None,
        block_domains: Optional[List[str]] = None,
        goggle: Optional[str] = None,
        custom_goggle: Optional[str] = None,
        anti_slop: bool = False,
        clustering: bool = True,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[SearchResultItem]:
        """Query active providers asynchronously, deduplicate, filter ads, and apply lenses."""
        boost_set = set(d.lower().strip() for d in (boost_domains or []))
        bury_set = set(d.lower().strip() for d in (bury_domains or []))
        block_set = set(d.lower().strip() for d in (block_domains or []))

        cat = category.lower().strip()

        # Build list of active tasks based on vertical category
        tasks = []

        if cat == "images":
            if self.images and self.images.is_configured:
                tasks.append(
                    self.images.search(
                        query, category="images", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            tasks.append(
                self.internal.search(
                    query, category="images", page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                )
            )
        elif cat == "news":
            if self.news and self.news.is_configured:
                tasks.append(
                    self.news.search(
                        query, category="news", page=page, page_size=page_size,
                        time_filter=time_filter, sort=sort, region=region, safe_search=safe_search, lang=lang
                    )
                )
            tasks.append(
                self.internal.search(
                    query, category="news", page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                )
            )
        elif cat == "videos":
            if self.videos and self.videos.is_configured:
                tasks.append(
                    self.videos.search(
                        query, category="videos", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.searxng and self.searxng.is_configured:
                tasks.append(
                    self.searxng.search(
                        query, category="videos", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            tasks.append(
                self.internal.search(
                    query, category="videos", page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                )
            )
        elif cat == "library" or opt_in_academic:
            tasks.append(
                self.internal.search(
                    query, category="library", page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                )
            )
            for prov in (self.crossref, self.doaj, self.arxiv, self.pubmed):
                if prov and prov.is_configured:
                    tasks.append(
                        prov.search(
                            query, category="library", page=page, page_size=page_size,
                            time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                        )
                    )
            if self.openalex and self.openalex.is_configured:
                tasks.append(
                    self.openalex.search(
                        query, category="library", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
        elif cat in ("community", "social", "smallweb") or opt_in_social:
            # Unified Community & Fora (Personal blogs, IndieWeb, Fediverse, Bluesky)
            tasks.append(
                self.internal.search(
                    query, category="web", page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                )
            )
            if self.fediverse and self.fediverse.is_configured:
                tasks.append(
                    self.fediverse.search(
                        query, category="social", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.bluesky and self.bluesky.is_configured:
                tasks.append(
                    self.bluesky.search(
                        query, category="social", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.mojeek and self.mojeek.is_configured:
                tasks.append(
                    self.mojeek.search(
                        query, category="all", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.searxng and self.searxng.is_configured:
                tasks.append(
                    self.searxng.search(
                        query, category="all", page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
        else:
            # General Web Search (category='all'): Unified constellation of serious, verified sources
            tasks.append(
                self.internal.search(
                    query, category=category, page=page, page_size=page_size,
                    time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                )
            )
            if self.wikipedia_search and self.wikipedia_search.is_configured:
                tasks.append(
                    self.wikipedia_search.search(
                        query, category=category, page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.crossref and self.crossref.is_configured:
                tasks.append(
                    self.crossref.search(
                        query, category=category, page=page, page_size=3,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.doaj and self.doaj.is_configured:
                tasks.append(
                    self.doaj.search(
                        query, category=category, page=page, page_size=3,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.searxng and self.searxng.is_configured:
                tasks.append(
                    self.searxng.search(
                        query, category=category, page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.brave and self.brave.is_configured:
                tasks.append(
                    self.brave.search(
                        query, category=category, page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
                    )
                )
            if self.mojeek and self.mojeek.is_configured:
                tasks.append(
                    self.mojeek.search(
                        query, category=category, page=page, page_size=page_size,
                        time_filter=time_filter, region=region, safe_search=safe_search, lang=lang
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

        # 1. Apply user Goggle lens or smallweb default lens
        active_goggle = None
        if custom_goggle and custom_goggle.strip():
            active_goggle = parse_goggle_dsl(custom_goggle.strip(), name="Lente Personalizada")
        elif goggle:
            active_goggle = get_preset_goggle(goggle)

        if cat in ("community", "smallweb") and not active_goggle:
            active_goggle = get_preset_goggle("small_web")

        if active_goggle:
            merged = apply_goggle_rules(merged, active_goggle)

        # 2. Apply anti-slop synthetic farm detector
        if anti_slop and cat not in ("images", "videos"):
            merged = apply_anti_slop_filter(merged)

        # 3. Sort: internal score descending
        merged.sort(key=lambda x: x.score, reverse=True)

        # 4. Domain clustering: guarantee diversity (max 2 per domain in top tier)
        if clustering and cat not in ("images", "videos"):
            merged = apply_domain_clustering(merged, max_per_domain=2)

        # 5. Direct Navigational Site Resolution (Instant direct address for domains & verified portals)
        if cat in ("all", "web") and page == 1 and query:
            nav_item = NavigationalEngine.resolve(query)
            if nav_item:
                nav_norm = nav_item.url.rstrip("/").lower()
                merged = [it for it in merged if it.url.rstrip("/").lower() != nav_norm]
                merged.insert(0, nav_item)

        return merged[:page_size]
