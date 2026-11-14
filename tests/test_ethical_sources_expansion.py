# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for Ethical Sources Expansion: Openverse, Open Library, Lemmy and Ethical Bangs."""

import json
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from senda.providers.openverse import OpenverseProvider
from senda.providers.openlibrary import OpenLibraryProvider
from senda.providers.lemmy import LemmyProvider
from senda.providers.aggregator import ProviderAggregator, BANG_SHORTCUTS


@pytest.fixture
def openverse_json_fixture():
    path = Path(__file__).parent / "fixtures" / "openverse_sample.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def openlibrary_json_fixture():
    path = Path(__file__).parent / "fixtures" / "openlibrary_sample.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def lemmy_json_fixture():
    path = Path(__file__).parent / "fixtures" / "lemmy_sample.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- 1. Openverse Provider Tests ---

def test_openverse_parse_results(openverse_json_fixture):
    """Test parsing Openverse image records into normalized SearchResultItems."""
    provider = OpenverseProvider(enabled=True)
    items = provider.parse_results(openverse_json_fixture)

    assert len(items) == 2

    # First item: CC BY 2.0
    item1 = items[0]
    assert item1.title == "Astronomy Starry Night Sky"
    assert item1.doc_type == "images"
    assert item1.source_type == "primaria_oficial"
    assert item1.content_type == "imagen_libre"
    assert "Openverse" in item1.source
    assert "BY 2.0" in item1.snippet
    assert "Galactic Photographer" in item1.authors
    assert item1.media_url == "https://api.openverse.org/v1/images/e4f8d22c-a0e2-411a-8c5e-7a1a45bb3864/thumb/"
    assert item1.canonical_url == "https://flickr.com/photos/user/12345678"

    # Second item: CC0 1.0 (The Met / Van Gogh)
    item2 = items[1]
    assert item2.title == "Classical Art Public Domain Portrait"
    assert "CC0 1.0" in item2.why_seen
    assert "Vincent van Gogh" in item2.authors


@pytest.mark.asyncio
async def test_openverse_search_mock(openverse_json_fixture):
    """Test OpenverseProvider.search with mocked HTTP request."""
    provider = OpenverseProvider(enabled=True)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = openverse_json_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        results = await provider.search("astronomy", page=1, page_size=10)

        assert len(results) == 2
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "license_type=commercial%2Cmodification" in called_url or "license_type=commercial,modification" in called_url
        assert "q=astronomy" in called_url

        # Check in-memory caching
        cached_results = await provider.search("astronomy", page=1, page_size=10)
        assert len(cached_results) == 2
        # Should not make another HTTP call due to cache
        assert mock_get.call_count == 1


# --- 2. Open Library Provider Tests ---

def test_openlibrary_parse_results(openlibrary_json_fixture):
    """Test parsing Open Library records into normalized SearchResultItems."""
    provider = OpenLibraryProvider(enabled=True)
    items = provider.parse_results(openlibrary_json_fixture)

    assert len(items) == 2
    quijote = items[0]
    assert "Don Quijote de la Mancha" in quijote.title
    assert "(1605)" in quijote.title
    assert "Miguel de Cervantes Saavedra" in quijote.authors
    assert quijote.doc_type == "library"
    assert quijote.content_type == "libro"
    assert quijote.source_type == "académica"
    assert quijote.media_url == "https://covers.openlibrary.org/b/id/8234567-M.jpg"
    assert quijote.url == "https://openlibrary.org/works/OL102749W"
    assert "Escaneo completo disponible" in quijote.snippet

    soledad = items[1]
    assert "Cien años de soledad" in soledad.title
    assert "Gabriel García Márquez" in soledad.authors


@pytest.mark.asyncio
async def test_openlibrary_search_mock(openlibrary_json_fixture):
    """Test OpenLibraryProvider.search with mocked HTTP request."""
    provider = OpenLibraryProvider(enabled=True)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = openlibrary_json_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        results = await provider.search("cervantes", page=1, page_size=5)

        assert len(results) == 2
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "q=cervantes" in called_url


# --- 3. Lemmy Provider Tests ---

def test_lemmy_parse_results(lemmy_json_fixture):
    """Test parsing Lemmy posts into normalized SearchResultItems."""
    provider = LemmyProvider(instance="lemmy.world", enabled=True)
    items = provider.parse_results(lemmy_json_fixture)

    assert len(items) == 1
    post = items[0]
    assert "soberanía" in post.title.lower() or "nodo" in post.title.lower()
    assert post.doc_type == "community"
    assert post.source_type == "red_abierta"
    assert post.content_type == "opinión"
    assert "Lemmy (!privacidad)" in post.source
    assert "@ciberactivista@lemmy.world" in post.authors
    assert post.canonical_url == "https://lemmy.world/post/123456"
    assert "45 votos" in post.snippet
    assert "ActivityPub" in post.why_seen


@pytest.mark.asyncio
async def test_lemmy_search_mock(lemmy_json_fixture):
    """Test LemmyProvider.search with mocked HTTP request."""
    provider = LemmyProvider(instance="lemmy.world", enabled=True)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = lemmy_json_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        results = await provider.search("privacidad", page=1, page_size=5)

        assert len(results) == 1
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "q=privacidad" in called_url
        assert "type_=Posts" in called_url


# --- 4. Aggregator Routing Tests ---

@pytest.mark.asyncio
async def test_aggregator_routes_images_to_openverse():
    """Verify that category='images' dispatches to openverse provider."""
    mock_openverse = AsyncMock()
    mock_openverse.is_configured = True
    mock_openverse.search.return_value = []

    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        openverse_provider=mock_openverse,
    )

    await aggregator.aggregate(query="paisaje", category="images")
    mock_openverse.search.assert_called_once()


@pytest.mark.asyncio
async def test_aggregator_routes_library_to_openlibrary():
    """Verify that category='library' dispatches to openlibrary provider."""
    mock_openlibrary = AsyncMock()
    mock_openlibrary.is_configured = True
    mock_openlibrary.search.return_value = []

    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        openlibrary_provider=mock_openlibrary,
    )

    await aggregator.aggregate(query="quijote", category="library")
    mock_openlibrary.search.assert_called_once()


@pytest.mark.asyncio
async def test_aggregator_routes_community_to_lemmy():
    """Verify that category='community' dispatches to lemmy provider."""
    mock_lemmy = AsyncMock()
    mock_lemmy.is_configured = True
    mock_lemmy.search.return_value = []

    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        lemmy_provider=mock_lemmy,
    )

    await aggregator.aggregate(query="linux", category="community")
    mock_lemmy.search.assert_called_once()


@pytest.mark.asyncio
async def test_aggregator_routes_general_web_to_openlibrary_natively():
    """Verify that general web search (category='all') dispatches to openlibrary natively without shortcuts."""
    mock_openlibrary = AsyncMock()
    mock_openlibrary.is_configured = True
    mock_openlibrary.search.return_value = []

    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        openlibrary_provider=mock_openlibrary,
    )

    await aggregator.aggregate(query="cien años de soledad", category="all")
    mock_openlibrary.search.assert_called_once()
    call_args = mock_openlibrary.search.call_args[1]
    assert call_args["category"] == "all"
    assert call_args["page_size"] == 2

