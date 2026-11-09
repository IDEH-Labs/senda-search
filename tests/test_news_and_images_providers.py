# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Tests for Real-time News, Free Culture Images, and Federated Verified Search."""

import json
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from senda.providers.news import RealTimeNewsProvider
from senda.providers.images import FreeCultureImageProvider
from senda.providers.wikipedia import WikipediaSearchProvider
from senda.providers.aggregator import ProviderAggregator


@pytest.fixture
def news_xml_fixture():
    path = Path(__file__).parent / "fixtures" / "realtime_news_sample.xml"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def commons_images_fixture():
    path = Path(__file__).parent / "fixtures" / "commons_images_sample.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def wiki_search_fixture():
    path = Path(__file__).parent / "fixtures" / "wikipedia_page_search.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_realtime_news_parse_feed(news_xml_fixture):
    """Verify that RealTimeNewsProvider parses real syndicated RSS news."""
    provider = RealTimeNewsProvider()
    items = provider.parse_feed(news_xml_fixture)

    assert len(items) == 5
    first = items[0]
    assert "Shakira" in first.title
    assert first.source_type == "noticia"
    assert first.content_type == "noticia"
    assert first.doc_type == "news"
    assert first.source in ("El Tiempo", "Infobae", "Prensa Verificada")
    assert first.published_date is not None
    assert "Prensa Abierta" in first.provider_origin
    assert "noticia en tiempo real" in first.why_seen.lower()


def test_free_culture_images_parse_commons(commons_images_fixture):
    """Verify FreeCultureImageProvider extracts verified Free Cultural Works images."""
    provider = FreeCultureImageProvider()
    items = provider.parse_commons(commons_images_fixture)

    assert len(items) > 0
    first = items[0]
    assert first.media_url is not None
    assert first.doc_type == "images"
    assert first.source_type == "primaria_oficial"
    assert first.content_type == "imagen_libre"
    assert "FSF" in first.why_seen or "Cultura Libre" in first.source


def test_wikipedia_page_search_parse(wiki_search_fixture):
    """Verify WikipediaSearchProvider parses real search API responses."""
    provider = WikipediaSearchProvider(lang="es")
    items = provider.parse_pages(wiki_search_fixture)

    assert len(items) > 0
    first = items[0]
    assert first.url.startswith("https://es.wikipedia.org/wiki/")
    assert first.source_type == "académica"
    assert first.content_type == "artículo"


@pytest.mark.asyncio
async def test_aggregator_routes_news_vertical():
    """Verify category='news' queries the real-time news provider."""
    mock_news = AsyncMock()
    mock_news.search.return_value = []
    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        news_provider=mock_news,
    )

    await aggregator.aggregate(query="atentado", category="news")
    mock_news.search.assert_called_once()


@pytest.mark.asyncio
async def test_aggregator_routes_images_vertical():
    """Verify category='images' queries the Free Culture images provider."""
    mock_images = AsyncMock()
    mock_images.search.return_value = []
    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        image_provider=mock_images,
    )

    await aggregator.aggregate(query="albert einstein", category="images")
    mock_images.search.assert_called_once()


@pytest.mark.asyncio
async def test_aggregator_federates_all_verified_sources_in_general_search():
    """Verify general search (category='all') queries the full constellation of verified sources."""
    mock_wiki = AsyncMock()
    mock_wiki.search.return_value = []
    mock_news = AsyncMock()
    mock_news.search.return_value = []
    mock_crossref = AsyncMock()
    mock_crossref.search.return_value = []
    mock_doaj = AsyncMock()
    mock_doaj.search.return_value = []
    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        wikipedia_search_provider=mock_wiki,
        news_provider=mock_news,
        crossref_provider=mock_crossref,
        doaj_provider=mock_doaj,
    )

    await aggregator.aggregate(query="descubren", category="all")
    mock_wiki.search.assert_called_once()
    mock_news.search.assert_called_once()
    mock_crossref.search.assert_called_once()
    mock_doaj.search.assert_called_once()
