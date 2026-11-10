# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for Senda Sovereign Goggles & Domain Ranking Engine."""

import pytest
from senda.providers.base import SearchResultItem
from senda.ranking.goggles import (
    get_available_goggles,
    get_preset_goggle,
    parse_goggle_dsl,
    apply_goggle_rules,
    SovereignGoggle,
)


def test_get_available_goggles():
    catalog = get_available_goggles()
    assert len(catalog) >= 5
    ids = [item["id"] for item in catalog]
    assert "" in ids
    assert "tech_libre" in ids
    assert "no_content_farms" in ids
    assert "science_primary" in ids
    assert "small_web" in ids


def test_get_preset_goggle():
    assert get_preset_goggle(None) is None
    assert get_preset_goggle("") is None
    assert get_preset_goggle("unknown_goggle_id") is None

    libre = get_preset_goggle("tech_libre")
    assert libre is not None
    assert "codeberg.org" in libre.boost_domains
    assert "pinterest.com" in libre.discard_domains


def test_parse_goggle_dsl():
    dsl_text = """
    # Custom Community Lens
    $discard,site=pinterest.com
    $boost=3,site=codeberg.org
    $down=2,site=medium.com
    """
    goggle = parse_goggle_dsl(dsl_text, name="Mi Lente")
    assert goggle.name == "Mi Lente"
    assert "pinterest.com" in goggle.discard_domains
    assert "codeberg.org" in goggle.boost_domains
    assert "medium.com" in goggle.bury_domains


def test_apply_goggle_rules_filter_and_rerank():
    goggle = SovereignGoggle(
        id="test_lens",
        name="Lente Test",
        description="Test lens",
        boost_domains={"codeberg.org"},
        bury_domains={"quora.com"},
        discard_domains={"pinterest.com"},
        boost_weight=30.0,
        bury_weight=20.0,
    )

    items = [
        SearchResultItem(url="https://pinterest.com/pin/123", title="Pin", snippet="", score=100.0),
        SearchResultItem(url="https://quora.com/question", title="Quora", snippet="", score=80.0),
        SearchResultItem(url="https://codeberg.org/IDEH-Labs/senda", title="Senda", snippet="", score=70.0),
        SearchResultItem(url="https://example.org/blog", title="Example", snippet="", score=60.0),
    ]

    filtered = apply_goggle_rules(items, goggle)

    # 1. pinterest.com must be discarded
    urls = [it.url for it in filtered]
    assert "https://pinterest.com/pin/123" not in urls

    # 2. codeberg.org was 70 + 30 = 100.0, so it should rank #1
    assert filtered[0].url == "https://codeberg.org/IDEH-Labs/senda"
    assert filtered[0].score == 100.0
    assert "Lente Test" in filtered[0].why_seen

    # 3. quora.com was 80 - 20 = 60.0, example.org is 60.0
    assert "quora.com" in filtered[-1].url or "quora.com" in filtered[-2].url
