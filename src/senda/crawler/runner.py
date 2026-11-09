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
from senda.security.threat_guard import threat_guard

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

        # 1. Check persistent SQLite cache first
        cached_policy = self.storage.get_robots_policy(domain)
        if cached_policy is not None:
            self.robots_manager.register_policy(domain, cached_policy)
            return

        # 2. Fetch over network if not in database
        robots_url = f"{scheme}://{domain}/robots.txt"
        try:
            doc = await self.fetcher.fetch(robots_url)
            if doc.status_code == 200:
                self.robots_manager.register_policy(domain, doc.text)
                self.storage.save_robots_policy(domain, doc.text)
            else:
                empty_policy = "User-agent: *\nAllow: /\n"
                self.robots_manager.register_empty_policy(domain)
                self.storage.save_robots_policy(domain, empty_policy)
        except (FetchError, SSRFSecurityViolation):
            empty_policy = "User-agent: *\nAllow: /\n"
            self.robots_manager.register_empty_policy(domain)
            self.storage.save_robots_policy(domain, empty_policy)

    async def crawl_seed(
        self,
        seed_url: str,
        max_pages: int = 10,
        max_depth: int = 2,
        concurrency: int = 5,
        on_page_indexed: Optional[Callable[[str, str, int], None]] = None,
    ) -> int:
        """Execute a breadth-first crawl starting from a single seed_url."""
        return await self.crawl_seeds(
            seed_urls=[seed_url],
            max_pages=max_pages,
            max_depth=max_depth,
            concurrency=concurrency,
            on_page_indexed=on_page_indexed,
        )

    async def crawl_seeds(
        self,
        seed_urls: list[str],
        max_pages: int = 10,
        max_depth: int = 2,
        concurrency: int = 5,
        on_page_indexed: Optional[Callable[[str, str, int], None]] = None,
    ) -> int:
        """Execute a concurrent, multi-domain polite crawl across seed_urls.

        Uses an asynchronous worker pool distributed across distinct host domains,
        strictly respecting per-domain RFC 9309 delays with single-connection domain isolation.
        Returns total number of successfully indexed documents.
        """
        self.frontier.max_depth = max_depth

        # Enqueue all seeds in memory and persistent storage
        for seed_url in seed_urls:
            parsed_seed = urlparse(seed_url)
            seed_domain = parsed_seed.netloc.lower()
            if seed_domain:
                self.frontier.add_url(seed_url, depth=0)
                self.storage.enqueue_frontier_url(seed_url, seed_domain, depth=0)

        # Restore any pending URLs from database to resume interrupted crawls
        pending_records = self.storage.get_pending_frontier_urls(limit=200)
        for row in pending_records:
            if row["depth"] <= max_depth:
                self.frontier.add_url(row["url"], depth=row["depth"])

        indexed_count = 0
        stop_event = asyncio.Event()
        lock = asyncio.Lock()

        async def worker(worker_id: int):
            nonlocal indexed_count
            consecutive_idles = 0

            while not stop_event.is_set():
                async with lock:
                    if indexed_count >= max_pages:
                        stop_event.set()
                        break

                item = self.frontier.get_next()
                if not item:
                    # Check if frontier has any pending work or active workers left
                    if self.frontier.pending_count() == 0:
                        stop_event.set()
                        break
                    consecutive_idles += 1
                    await asyncio.sleep(min(0.1 * consecutive_idles, 0.5))
                    continue

                consecutive_idles = 0
                current_url = item.url
                current_depth = item.depth
                domain = item.domain
                parsed = urlparse(current_url)
                scheme = parsed.scheme.lower() or "https"

                try:
                    # 0. Objective Harm Safety Gate
                    is_blocked, cat, exp = threat_guard.check_url(current_url)
                    if is_blocked:
                        logger.warning(f"CrawlerRunner: URL bloqueada por daño objetivo ({cat}): {current_url}.")
                        self.storage.mark_frontier_url_failed(current_url)
                        continue

                    # 1. Fetch & evaluate robots.txt
                    await self._fetch_robots_if_needed(domain, scheme)

                    if not self.robots_manager.is_allowed(current_url, user_agent=self.fetcher.user_agent):
                        logger.info(f"Robots disallows: {current_url}")
                        self.storage.mark_frontier_url_failed(current_url)
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
                        self.storage.mark_frontier_url_failed(current_url)
                        continue

                    if doc.status_code != 200:
                        self.storage.mark_frontier_url_failed(current_url)
                        continue

                    # 3. Extract content and metadata
                    extracted = DocumentExtractor.extract(doc.url, doc.text)

                    # 3.1 Respect meta robots noindex directive
                    if not extracted.is_indexable:
                        logger.info(f"CrawlerRunner: Respetando meta robots noindex en: {current_url}")
                        self.storage.mark_frontier_url_completed(current_url)
                        continue

                    # 4. Store and index
                    was_indexed = self.storage.upsert_document(extracted, status_code=doc.status_code)
                    self.storage.mark_frontier_url_completed(current_url)

                    if was_indexed:
                        async with lock:
                            indexed_count += 1
                            current_total = indexed_count
                        if on_page_indexed:
                            on_page_indexed(extracted.url, extracted.title, current_total)

                    # 5. Enqueue outgoing links if depth permits
                    if current_depth < max_depth:
                        for link in extracted.outgoing_links:
                            parsed_link = urlparse(link)
                            link_domain = parsed_link.netloc.lower()
                            if self.frontier.add_url(link, depth=current_depth + 1):
                                self.storage.enqueue_frontier_url(link, link_domain, depth=current_depth + 1)
                finally:
                    self.frontier.release_domain(domain)

        worker_tasks = [
            asyncio.create_task(worker(i))
            for i in range(max(1, concurrency))
        ]

        await asyncio.gather(*worker_tasks)
        return indexed_count
