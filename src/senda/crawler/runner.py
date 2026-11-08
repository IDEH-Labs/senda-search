# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Crawler Runner: Coordinates Frontier, RFC 9309 Politeness, Fetcher, and Storage."""

import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import urlparse

from senda.config import settings
from senda.crawler.fetcher import SafeFetcher, FetchError
from senda.crawler.network_guard import SSRFSecurityViolation
from senda.crawler.robots import RobotsPolicyManager
from senda.extractor.parser import DocumentExtractor
from senda.frontier.queue import FrontierQueue
from senda.indexer.storage import StorageEngine

logger = logging.getLogger(__name__)


class CrawlerRunner:
    """Manages an ethical, disciplined web crawling execution."""

    def __init__(
        self,
        storage: Optional[StorageEngine] = None,
        fetcher: Optional[SafeFetcher] = None,
        robots_manager: Optional[RobotsPolicyManager] = None,
        frontier: Optional[FrontierQueue] = None,
    ):
        self.storage = storage or StorageEngine()
        self.fetcher = fetcher or SafeFetcher()
        self.robots_manager = robots_manager or RobotsPolicyManager()
        self.frontier = frontier or FrontierQueue(
            default_crawl_delay=settings.DEFAULT_CRAWL_DELAY_SECONDS,
            max_depth=settings.MAX_PATH_DEPTH
        )

    async def _fetch_robots_if_needed(self, domain: str, scheme: str = "https") -> None:
        """Fetch and cache RFC 9309 robots.txt for domain if not already cached."""
        if self.robots_manager.has_policy(domain):
            return

        robots_url = f"{scheme}://{domain}/robots.txt"
        try:
            doc = await self.fetcher.fetch(robots_url)
            if doc.status_code == 200:
                self.robots_manager.register_policy(domain, doc.text)
            else:
                self.robots_manager.register_empty_policy(domain)
        except (FetchError, SSRFSecurityViolation):
            # If robots.txt cannot be reached or triggers SSRF, register empty policy (default allow)
            self.robots_manager.register_empty_policy(domain)

    async def crawl_seed(
        self,
        seed_url: str,
        max_pages: int = 10,
        max_depth: int = 2,
        on_page_indexed: Optional[Callable[[str, str, int], None]] = None,
    ) -> int:
        """Execute a breadth-first crawl starting from seed_url.

        Returns total number of successfully indexed documents.
        """
        self.frontier.max_depth = max_depth
        self.frontier.add_url(seed_url, depth=0)
        indexed_count = 0

        while self.frontier.pending_count() > 0 and indexed_count < max_pages:
            item = self.frontier.get_next()
            if not item:
                # All pending URLs are waiting on politeness delays; sleep briefly
                await asyncio.sleep(0.2)
                continue

            current_url = item.url
            current_depth = item.depth
            parsed = urlparse(current_url)
            domain = parsed.netloc.lower()
            scheme = parsed.scheme.lower() or "https"

            # 1. Fetch & evaluate robots.txt
            await self._fetch_robots_if_needed(domain, scheme)

            if not self.robots_manager.is_allowed(current_url, user_agent=self.fetcher.user_agent):
                logger.info(f"Robots disallows: {current_url}")
                continue

            # Update frontier delay if robots declared Crawl-delay
            declared_delay = self.robots_manager.get_crawl_delay(domain, user_agent=self.fetcher.user_agent)
            if declared_delay:
                self.frontier.set_domain_delay(domain, max(declared_delay, settings.DEFAULT_CRAWL_DELAY_SECONDS))

            # 2. Safely fetch document
            try:
                doc = await self.fetcher.fetch(current_url)
            except (FetchError, SSRFSecurityViolation) as e:
                logger.warning(f"Failed to fetch {current_url}: {e}")
                continue

            if doc.status_code != 200:
                continue

            # 3. Extract content and metadata
            extracted = DocumentExtractor.extract(doc.url, doc.text)

            # 4. Store and index
            was_indexed = self.storage.upsert_document(extracted, status_code=doc.status_code)
            if was_indexed:
                indexed_count += 1
                if on_page_indexed:
                    on_page_indexed(extracted.url, extracted.title, indexed_count)

            # 5. Enqueue outgoing links if depth permits
            if current_depth < max_depth:
                for link in extracted.outgoing_links:
                    self.frontier.add_url(link, depth=current_depth + 1)

        return indexed_count
