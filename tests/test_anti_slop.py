# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for Senda Anti-Slop & Synthetic Farm Detection Engine."""

import pytest
from senda.providers.base import SearchResultItem
from senda.ranking.anti_slop import compute_slop_score, apply_anti_slop_filter


def test_compute_slop_score_human_vs_slop():
    # Authentic human-crafted article
    score_human, reasons_human = compute_slop_score(
        title="Linux Kernel 6.12 Memory Management Improvements",
        snippet="We analyzed the slab allocator changes in Linux 6.12 and benchmarked page allocation latency under heavy load.",
        domain="kernel.org",
        has_author=True,
        has_date=True,
    )
    assert score_human < 0.2
    assert len(reasons_human) == 0

    # Automated synthetic SEO content farm snippet
    score_slop, reasons_slop = compute_slop_score(
        title="Los 10 Mejores Métodos: Guía Definitiva de Productividad",
        snippet="En conclusión, en el vertiginoso mundo actual es fundamental destacar que a continuación te explicamos todo lo que necesitas saber sobre productividad.",
        domain="seo-farm-tips.xyz",
        has_author=False,
        has_date=False,
    )
    assert score_slop >= 0.55
    assert len(reasons_slop) >= 2


def test_apply_anti_slop_filter_demotes_slop():
    high_quality = SearchResultItem(
        url="https://kernel.org/doc",
        title="Kernel Documentation",
        snippet="Official Linux kernel documentation and design guidelines.",
        authors=["Linus Torvalds"],
        published_date="2026-01-01",
        score=80.0,
    )

    slop_item = SearchResultItem(
        url="https://spamcontentfarm.com/article",
        title="Los 10 Mejores Consejos para Programar en Python",
        snippet="En conclusión, en el vertiginoso panorama digital es crucial destacar que a continuación te presentamos todo lo que necesitas saber.",
        score=90.0,  # Initially higher score due to artificial keyword density
    )

    items = [slop_item, high_quality]
    filtered = apply_anti_slop_filter(items, threshold=0.55, demote_penalty=40.0)

    # Slop item score must be demoted: 90 - 40 = 50.0
    # High quality item (80.0) should now rank above slop item (50.0)
    assert filtered[0].url == "https://kernel.org/doc"
    assert filtered[1].url == "https://spamcontentfarm.com/article"
    assert "Anti-Slop" in filtered[1].why_seen
    assert filtered[1].ai_provenance is not None
