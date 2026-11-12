# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Unit tests for Senda Content Style & SEO Cliché Inspection Engine.
Verifies strict adherence to Section 4.3 of POLITICA_ETICA.md:
- Zero ranking alterations (ranking order and scores remain 100% stable).
- Zero manufactured AIProvenance labels without authentic declared signals.
- Transparent audit trail in why_seen as observable stylistic traits.
"""

import pytest
from senda.providers.base import SearchResultItem, AIProvenance
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

    # Automated SEO content farm snippet with multiple clichés
    score_slop, reasons_slop = compute_slop_score(
        title="Los 10 Mejores Métodos: Guía Definitiva de Productividad",
        snippet="En conclusión, en el vertiginoso mundo actual es fundamental destacar que a continuación te explicamos todo lo que necesitas saber sobre productividad.",
        domain="seo-farm-tips.xyz",
        has_author=False,
        has_date=False,
    )
    assert score_slop >= 0.55
    assert len(reasons_slop) >= 2


def test_anti_slop_preserves_ranking_order_and_scores():
    """Verify that applying anti-slop NEVER demotes scores or alters search ranking order."""
    item1 = SearchResultItem(
        url="https://spamcontentfarm.com/article",
        title="Los 10 Mejores Consejos para Programar en Python",
        snippet="En conclusión, en el vertiginoso panorama digital es crucial destacar que a continuación te presentamos todo lo que necesitas saber.",
        score=95.0,
    )
    item2 = SearchResultItem(
        url="https://kernel.org/doc",
        title="Kernel Documentation",
        snippet="Official Linux kernel documentation and design guidelines.",
        authors=["Linus Torvalds"],
        published_date="2026-01-01",
        score=80.0,
    )

    items = [item1, item2]
    # Apply filter
    filtered = apply_anti_slop_filter(items, threshold=0.55)

    # 1. Scores must remain completely untouched (no demotion penalty)
    assert filtered[0].score == 95.0
    assert filtered[1].score == 80.0

    # 2. Ranking order must remain strictly identical
    assert filtered[0].url == "https://spamcontentfarm.com/article"
    assert filtered[1].url == "https://kernel.org/doc"


def test_anti_slop_never_assigns_ai_provenance_without_declared_signal():
    """
    In strict compliance with Section 4.3 of POLITICA_ETICA.md:
    Senda prohibits heuristic AI detectors. Applying the filter must NEVER manufacture
    an AIProvenance label on items lacking declared provenance signals.
    """
    slop_item = SearchResultItem(
        url="https://spamcontentfarm.com/article",
        title="Los 10 Mejores Consejos para Programar en Python",
        snippet="En conclusión, en el vertiginoso panorama digital es crucial destacar que a continuación te presentamos todo lo que necesitas saber.",
        score=90.0,
    )
    assert slop_item.ai_provenance is None

    filtered = apply_anti_slop_filter([slop_item], threshold=0.55)

    # Must NOT assign synthetic / AI provenance
    assert filtered[0].ai_provenance is None

    # Must describe observable stylistic traits transparently in why_seen
    assert "Rasgo observable: Clichés o patrones frecuentes de redacción" in filtered[0].why_seen


def test_anti_slop_preserves_authentic_declared_provenance():
    """Items that already have an authentic declared provenance signal retain it untouched."""
    authentic_c2pa_item = SearchResultItem(
        url="https://example.org/c2pa-article",
        title="Verified Scientific Article",
        snippet="En conclusión, presentamos el análisis formal.",
        ai_provenance=AIProvenance(
            declared_signal="C2PA Content Credentials: Verificado humano",
            status="humano",
        ),
        score=85.0,
    )

    filtered = apply_anti_slop_filter([authentic_c2pa_item], threshold=0.55)
    assert filtered[0].ai_provenance is not None
    assert filtered[0].ai_provenance.status == "humano"
    assert "C2PA" in filtered[0].ai_provenance.declared_signal
