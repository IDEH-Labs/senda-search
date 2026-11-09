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


def test_ranking_operators_and_filtering(populated_search_engine):
    # 1. Test site: operator (should match only fsf.org, not example.com)
    site_results = populated_search_engine.search("site:fsf.org freedom")
    assert site_results.total_matches == 1
    assert site_results.items[0].url == "https://fsf.org/philosophy"

    # 2. Test negative operator -term (exclude example.com by excluding 'society')
    neg_results = populated_search_engine.search("freedom -society")
    assert neg_results.total_matches == 1
    assert neg_results.items[0].url == "https://fsf.org/philosophy"


def test_morphological_stemmer():
    from senda.ranking.stemmer import MorphologicalStemmer

    assert MorphologicalStemmer.get_root_prefix("desarrolladores") == "desarroll"
    assert MorphologicalStemmer.get_root_prefix("libertades") == "liberta"
    assert MorphologicalStemmer.get_root_prefix("freedoms") == "freedom"
    assert MorphologicalStemmer.get_root_prefix("computing") == "comput"
    # Short words preserved
    assert MorphologicalStemmer.get_root_prefix("sol") == "sol"


def test_anti_seo_text_density_ranking_boost(tmp_path):
    storage = StorageEngine(db_path=tmp_path / "density_rank_test.db")

    # Document 1: Commercial / bloated page (low text density 0.05)
    storage.upsert_document(
        ExtractedDocument(
            url="https://commercial-spam.com/post",
            title="Sovereign protocol notes",
            description="Notes on protocol.",
            language="en",
            headings="Protocol specification",
            body_text="Here is the protocol discussion for distributed sovereign networks.",
            content_hash="h_spam",
            text_density=0.05,
        )
    )

    # Document 2: High density handcrafted essay (high text density 0.90)
    storage.upsert_document(
        ExtractedDocument(
            url="https://sovereign-lab.org/protocol-essay",
            title="Sovereign protocol notes",
            description="Notes on protocol.",
            language="en",
            headings="Protocol specification",
            body_text="Here is the protocol discussion for distributed sovereign networks.",
            content_hash="h_lab",
            text_density=0.90,
        )
    )

    retriever = SearchRetriever(storage)
    results = retriever.search("protocol")

    assert results.total_matches == 2
    # The high text density document must be ranked first!
    assert results.items[0].url == "https://sovereign-lab.org/protocol-essay"
    assert results.items[1].url == "https://commercial-spam.com/post"
    assert results.items[0].relevance_score > results.items[1].relevance_score


def test_search_verticals_and_images(tmp_path):
    from senda.extractor.parser import ExtractedImage

    storage = StorageEngine(db_path=tmp_path / "verticals_test.db")

    # 1. News document
    storage.upsert_document(
        ExtractedDocument(
            url="https://fsf.org/news/copyleft-summit",
            title="Copyleft Summit 2026 Announced",
            description="Global gathering of software freedom advocates.",
            language="en",
            headings="Keynotes and Workshops",
            body_text="Discussion on GPL enforcement, sovereign hosting, and digital autonomy.",
            content_hash="h_news",
            doc_type="news",
            published_at="2026-11-05",
        )
    )

    # 2. Library / Encyclopedia document with free media image
    storage.upsert_document(
        ExtractedDocument(
            url="https://en.wikipedia.org/wiki/GNU_General_Public_License",
            title="GNU General Public License - Wikipedia",
            description="Comprehensive historical encyclopedia entry on the GPL.",
            language="en",
            headings="Origins and History",
            body_text="The GNU General Public License is a series of widely used free software licenses.",
            content_hash="h_lib",
            doc_type="library",
            images=[
                ExtractedImage(
                    image_url="https://upload.wikimedia.org/wikipedia/commons/gplv3.png",
                    alt_text="GNU GPLv3 official logo",
                    page_url="https://en.wikipedia.org/wiki/GNU_General_Public_License",
                    page_title="GNU General Public License",
                    domain="en.wikipedia.org",
                    license="CC-BY-SA 4.0 / Wikimedia Commons"
                )
            ]
        )
    )

    retriever = SearchRetriever(storage)

    # Web / All search
    all_res = retriever.search("GNU", category="all")
    assert all_res.total_matches >= 1

    # News vertical search
    news_res = retriever.search("sovereign", category="news")
    assert news_res.total_matches == 1
    assert news_res.items[0].doc_type == "news"
    assert news_res.items[0].url == "https://fsf.org/news/copyleft-summit"

    # Library vertical search
    lib_res = retriever.search("License", category="library")
    assert lib_res.total_matches == 1
    assert lib_res.items[0].doc_type == "library"
    assert "wikipedia.org" in lib_res.items[0].url

    # Free Culture Images vertical search
    img_res = retriever.search("GPLv3", category="images")
    assert img_res.total_matches == 1
    assert img_res.items[0].doc_type == "image"
    assert img_res.items[0].media_url == "https://upload.wikimedia.org/wikipedia/commons/gplv3.png"
    assert "Wikimedia" in img_res.items[0].license

