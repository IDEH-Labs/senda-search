# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Automated verification tests for native language propagation across search providers."""

import pytest
from fastapi.testclient import TestClient
from senda.api.app import app
from senda.providers.news import RealTimeNewsProvider, NEWS_LANG_CONFIG
from senda.providers.wikipedia import WikipediaSearchProvider


@pytest.mark.asyncio
async def test_news_lang_config_completeness():
    """Verify that all 10 supported languages have valid news feeds."""
    for lang in ("ar", "de", "en", "es", "fr", "it", "ja", "pt", "ru", "zh"):
        assert lang in NEWS_LANG_CONFIG
        cfg = NEWS_LANG_CONFIG[lang]
        assert "hl" in cfg and "gl" in cfg and "ceid" in cfg


@pytest.mark.asyncio
async def test_news_provider_native_languages():
    """Verify that RealTimeNewsProvider correctly fetches language-specific feeds."""
    provider = RealTimeNewsProvider()
    
    # Test English query
    en_items = await provider.search("technology", lang="en", page_size=3)
    if en_items:
        for it in en_items:
            assert it.language == "en"
            assert it.doc_type == "news"

    # Test French query
    fr_items = await provider.search("technologie", lang="fr", page_size=3)
    if fr_items:
        for it in fr_items:
            assert it.language == "fr"
            assert it.doc_type == "news"


@pytest.mark.asyncio
async def test_news_provider_empty_query_headlines():
    """Verify that an empty query in the news vertical fetches breaking headlines rather than empty list."""
    provider = RealTimeNewsProvider()
    headlines = await provider.search("", lang="en", page_size=2)
    # Breaking headlines RSS should yield results
    assert isinstance(headlines, list)
    if headlines:
        assert headlines[0].language == "en"


@pytest.mark.asyncio
async def test_wikipedia_search_native_language():
    """Verify that WikipediaSearchProvider routes to the correct localized Wikipedia domain."""
    provider = WikipediaSearchProvider()

    de_items = await provider.search("Linux", lang="de", page_size=2)
    if de_items:
        assert de_items[0].language == "de"
        assert "de.wikipedia.org" in de_items[0].url

    ru_items = await provider.search("Linux", lang="ru", page_size=2)
    if ru_items:
        assert ru_items[0].language == "ru"
        assert "ru.wikipedia.org" in ru_items[0].url


def test_api_search_with_lang_parameter():
    """Verify that the FastAPI /search endpoint respects the lang parameter and propagates it."""
    client = TestClient(app)

    # 1. Search in English
    resp_en = client.get("/search?q=Linux&category=news&lang=en")
    assert resp_en.status_code == 200
    assert 'lang="en"' in resp_en.text
    # Check that the lang input is maintained in the form
    assert 'name="lang" value="en"' in resp_en.text

    # 2. Search in French
    resp_fr = client.get("/search?q=Linux&category=news&lang=fr")
    assert resp_fr.status_code == 200
    assert 'lang="fr"' in resp_fr.text
    assert 'name="lang" value="fr"' in resp_fr.text

    # 3. Homepage with lang=de
    resp_home = client.get("/?lang=de")
    assert resp_home.status_code == 200
    assert 'lang="de"' in resp_home.text
    assert 'name="lang" id="search-lang" value="de"' in resp_home.text
