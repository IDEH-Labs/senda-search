# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Crawl Frontier and Politeness Coordinator.

Manages URL queuing, priority, canonical deduplication, and per-domain
politeness schedules.
"""

import collections
import hashlib
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from senda.frontier.canonical import canonicalize_url, is_spider_trap


@dataclass
class CrawlItem:
    url: str
    depth: int
    domain: str
    priority: int = 0
    added_at: float = 0.0


class FrontierQueue:
    """Thread-safe / async-friendly polite crawl frontier."""

    def __init__(self, default_crawl_delay: float = 2.0, max_depth: int = 3):
        self.default_crawl_delay = default_crawl_delay
        self.max_depth = max_depth

        # Set of seen URL hashes for memory-efficient deduplication
        self._seen_hashes: set[str] = set()

        # Per-domain FIFO queues
        self._domain_queues: dict[str, collections.deque[CrawlItem]] = collections.defaultdict(collections.deque)

        # Domains currently being crawled by active workers
        self._active_domains: set[str] = set()

        # Domain last access timestamps
        self._domain_last_crawled: dict[str, float] = {}

        # Custom per-domain crawl delays (from robots.txt)
        self._domain_delays: dict[str, float] = {}

    @staticmethod
    def hash_url(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def set_domain_delay(self, domain: str, delay_seconds: float) -> None:
        """Register a domain-specific crawl delay parsed from robots.txt."""
        self._domain_delays[domain] = max(delay_seconds, 0.5)

    def get_domain_delay(self, domain: str) -> float:
        return self._domain_delays.get(domain, self.default_crawl_delay)

    def add_url(self, raw_url: str, depth: int = 0, priority: int = 0) -> bool:
        """Add a URL to the frontier after canonicalization and safety checks.

        Returns True if the URL was accepted and enqueued; False if rejected or already seen.
        """
        if depth > self.max_depth:
            return False

        canonical = canonicalize_url(raw_url)
        if not canonical:
            return False

        if is_spider_trap(canonical):
            return False

        url_hash = self.hash_url(canonical)
        if url_hash in self._seen_hashes:
            return False

        parsed = urlparse(canonical)
        domain = parsed.netloc.lower()
        if not domain:
            return False

        self._seen_hashes.add(url_hash)
        item = CrawlItem(
            url=canonical,
            depth=depth,
            domain=domain,
            priority=priority,
            added_at=time.time()
        )
        self._domain_queues[domain].append(item)
        return True

    def get_next(self) -> Optional[CrawlItem]:
        """Fetch the next available CrawlItem whose domain has satisfied its politeness interval."""
        now = time.time()

        for domain, queue in list(self._domain_queues.items()):
            if not queue or domain in self._active_domains:
                continue

            last_time = self._domain_last_crawled.get(domain, 0.0)
            required_delay = self.get_domain_delay(domain)

            if now - last_time >= required_delay:
                item = queue.popleft()
                self._active_domains.add(domain)
                self._domain_last_crawled[domain] = now
                if not queue:
                    del self._domain_queues[domain]
                return item

        return None

    def release_domain(self, domain: str) -> None:
        """Release active domain lock after crawl worker finishes processing it."""
        self._active_domains.discard(domain)
        self._domain_last_crawled[domain] = time.time()

    def pending_count(self) -> int:
        return sum(len(q) for q in self._domain_queues.values()) + len(self._active_domains)

    def seen_count(self) -> int:
        return len(self._seen_hashes)
