# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Domain Clustering & Diversity Engine
Prevents monopolization of search results by single large domains (Mojeek-inspired diversity).
Ensures a balanced, organic spread of primary sources and diverse perspectives.
Works 100% server-side with zero JavaScript required.
"""

from __future__ import annotations

from collections import defaultdict
from typing import List, Optional
import urllib.parse

from senda.providers.base import SearchResultItem


def extract_base_domain(url: str) -> str:
    """Extract normalized base domain (hostname) from a URL."""
    try:
        netloc = urllib.parse.urlparse(url).netloc.lower().strip()
        # Strip common port numbers or www prefix for clustering grouping
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def apply_domain_clustering(
    items: List[SearchResultItem],
    max_per_domain: int = 2,
) -> List[SearchResultItem]:
    """
    Reorder items to guarantee domain diversity in top rankings.
    Preserves highest-scoring items from each domain up to `max_per_domain`.
    Surplus items are moved behind diverse results instead of being completely lost.
    """
    if not items or max_per_domain <= 0:
        return items

    primary_items: List[SearchResultItem] = []
    overflow_items: List[SearchResultItem] = []
    domain_counts: defaultdict[str, int] = defaultdict(int)

    for item in items:
        domain = extract_base_domain(item.url) or "unknown"
        current_count = domain_counts[domain]

        if current_count < max_per_domain:
            domain_counts[domain] += 1
            primary_items.append(item)
        else:
            # Domain quota reached for top tier; hold for overflow
            overflow_items.append(item)

    # Return primary diverse results followed by overflow results
    return primary_items + overflow_items
