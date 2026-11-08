# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for QuerySanitizer and SearchRetriever ranking."""

import pytest
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine
from senda.ranking.retriever import QuerySanitizer, SearchRetriever


def test_query_sanitizer():
    assert QuerySanitizer.sanitize("") == ""
    assert QuerySanitizer.sanitize("   ") == ""

    # Dangerous characters stripped
    sanitized = QuerySanitizer.sanitize("python + (tutorial) : *")
    assert "tutorial" in sanitized
    assert "+" not in sanitized
    assert ":" not in sanitized
    assert "(" not in sanitized

    # Quoted phrase preserved
    sanitized_phrase = QuerySanitizer.sanitize('"free software" movement')
    assert '"free software"' in sanitized_phrase
    assert '"movement"' in sanitized_phrase


@pytest.fixture
def populated_search_engine(tmp_path):
    storage = StorageEngine(db_path=tmp_path / "ranking_test.db")

    # Doc 1: Match in Title
    storage.upsert_document(
        ExtractedDocument(
            url="https://fsf.org/philosophy",
            title="Software Freedom and Ethics",
            description="Philosophy of free software.",
            language="en",
            headings="The Four Freedoms",
            body_text="Every computer user deserves autonomy and rights.",
            content_hash="h1",
        )
    )

    # Doc 2: Match only deep in body
    storage.upsert_document(
        ExtractedDocument(
            url="https://example.com/blog",
            title="A Random Developer Journal",
            description="Casual musings about code.",
            language="en",
            headings="Daily Entry",
            body_text="Today I was thinking about ethics and computer freedom in modern society.",
            content_hash="h2",
        )
    )

    # Doc 3: Completely unrelated
    storage.upsert_document(
        ExtractedDocument(
            url="https://culinary.org/recipe",
            title="Baking Sourdough Bread",
            description="How to feed your sourdough starter.",
            language="en",
            headings="Ingredients Instructions",
            body_text="Flour, water, salt, and active wild yeast starter.",
            content_hash="h3",
        )
    )

    return SearchRetriever(storage)


def test_ranking_retrieval_and_title_weighting(populated_search_engine):
    results = populated_search_engine.search("Freedom", page=1, page_size=10)

    assert results.total_matches == 2
    assert len(results.items) == 2

    # Doc 1 (match in Title and Headings) must rank HIGHER than Doc 2 (match only in body)
    assert results.items[0].url == "https://fsf.org/philosophy"
    assert results.items[1].url == "https://example.com/blog"
    assert results.items[0].relevance_score > results.items[1].relevance_score

    # Check snippet highlighting
    assert "<mark>" in results.items[0].snippet or "Freedom" in results.items[0].title


def test_ranking_pagination(populated_search_engine):
    # Query matching 2 docs, with page_size=1
    page1 = populated_search_engine.search("ethics", page=1, page_size=1)
    assert page1.total_matches == 2
    assert page1.total_pages == 2
    assert len(page1.items) == 1
    first_url = page1.items[0].url

    page2 = populated_search_engine.search("ethics", page=2, page_size=1)
    assert len(page2.items) == 1
    assert page2.items[0].url != first_url


def test_ranking_empty_results(populated_search_engine):
    results = populated_search_engine.search("nonexistenttermxyz123")
    assert results.total_matches == 0
    assert len(results.items) == 0
