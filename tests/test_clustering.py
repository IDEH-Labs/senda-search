# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for Senda Domain Clustering & Diversity Engine."""

import pytest
from senda.providers.base import SearchResultItem
from senda.ranking.clustering import extract_base_domain, apply_domain_clustering


def test_extract_base_domain():
    assert extract_base_domain("https://www.example.org/test") == "example.org"
    assert extract_base_domain("http://sub.domain.co.uk:8080/path") == "sub.domain.co.uk"
    assert extract_base_domain("https://codeberg.org/IDEH-Labs/senda") == "codeberg.org"
    assert extract_base_domain("") == ""
    assert extract_base_domain("not-a-valid-url-???") == "not-a-valid-url-???" or extract_base_domain("not-a-valid-url-???") == ""


def test_apply_domain_clustering_caps_occurrences():
    items = [
        SearchResultItem(url="https://site-a.com/1", title="A1", snippet="", score=100.0),
        SearchResultItem(url="https://site-a.com/2", title="A2", snippet="", score=95.0),
        SearchResultItem(url="https://site-a.com/3", title="A3", snippet="", score=90.0),
        SearchResultItem(url="https://site-a.com/4", title="A4", snippet="", score=85.0),
        SearchResultItem(url="https://site-b.org/1", title="B1", snippet="", score=80.0),
        SearchResultItem(url="https://site-c.net/1", title="C1", snippet="", score=75.0),
    ]

    clustered = apply_domain_clustering(items, max_per_domain=2)

    assert len(clustered) == 6
    # The first 4 items in primary cluster must be: site-a.com (2 items), site-b.org (1 item), site-c.net (1 item)
    primary_urls = [it.url for it in clustered[:4]]
    assert "https://site-a.com/1" in primary_urls
    assert "https://site-a.com/2" in primary_urls
    assert "https://site-b.org/1" in primary_urls
    assert "https://site-c.net/1" in primary_urls

    # Overflow items (the 3rd and 4th from site-a.com) must be at the end
    overflow_urls = [it.url for it in clustered[4:]]
    assert overflow_urls == ["https://site-a.com/3", "https://site-a.com/4"]


def test_apply_domain_clustering_empty_or_zero():
    assert apply_domain_clustering([]) == []
    dummy = [SearchResultItem(url="https://test.com", title="T", snippet="")]
    assert apply_domain_clustering(dummy, max_per_domain=0) == dummy
