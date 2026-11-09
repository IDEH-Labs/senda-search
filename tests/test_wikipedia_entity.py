# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit, contract, and integration tests for Wikipedia & Wikidata Entity Provider."""

import json
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from senda.providers.wikipedia import WikipediaEntityProvider, WikipediaEntityCard
from senda.api.app import create_app
from senda.indexer.storage import StorageEngine


@pytest.fixture
def einstein_fixture():
    fixture_path = Path(__file__).parent / "fixtures" / "wikipedia_einstein_summary.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def temp_storage(tmp_path):
    db_file = tmp_path / "test_wiki.db"
    return StorageEngine(db_file)


def test_wikipedia_parse_summary_real_fixture(einstein_fixture):
    """Verify that recorded real Wikipedia summary response parses accurately."""
    provider = WikipediaEntityProvider()
    card = provider.parse_summary(einstein_fixture, lang="es")

    assert card is not None
    assert card.title == "Albert Einstein"
    assert card.wikibase_item == "Q937"
    assert "físico" in card.description.lower()
    assert "relatividad" in card.extract.lower() or "einstein" in card.extract.lower()
    assert card.thumbnail_url is not None
    assert "https://es.wikipedia.org/wiki/Albert_Einstein" in card.wikipedia_url
    assert "action=history" in card.history_url
    assert "CC BY-SA 4.0" in card.license
    assert card.source == "Wikipedia en Español"


def test_wikipedia_parse_disambiguation_ignored():
    """Verify disambiguation pages are ignored to avoid showing ambiguous entities."""
    provider = WikipediaEntityProvider()
    disam_data = {
        "type": "disambiguation",
        "title": "Mercurio (desambiguación)",
        "extract": "Mercurio puede referirse a...",
    }
    card = provider.parse_summary(disam_data)
    assert card is None


@pytest.mark.asyncio
async def test_wikipedia_caching_and_fast_lookup(einstein_fixture):
    """Verify in-memory caching prevents repeated network queries."""
    provider = WikipediaEntityProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = einstein_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        # First call: hits network
        card1 = await provider.get_entity("Albert Einstein", lang="es")
        assert card1 is not None
        assert card1.title == "Albert Einstein"
        assert mock_get.call_count == 1

        # Second call: served from memory cache (0 network calls)
        card2 = await provider.get_entity("Albert Einstein", lang="es")
        assert card2 is not None
        assert card2.title == "Albert Einstein"
        assert mock_get.call_count == 1  # Still 1, served from cache!


@pytest.mark.asyncio
async def test_wikipedia_bang_and_short_query_ignored():
    """Verify queries with bangs or single characters are immediately skipped."""
    provider = WikipediaEntityProvider()
    assert await provider.get_entity("!w einstein") is None
    assert await provider.get_entity("a") is None
    assert await provider.get_entity("   ") is None


@pytest.mark.asyncio
async def test_wikipedia_error_and_404_handling():
    """Verify 404 or connection errors gracefully return None without raising."""
    provider = WikipediaEntityProvider()

    # 404 response
    mock_resp_404 = MagicMock()
    mock_resp_404.status_code = 404

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp_404
        assert await provider.get_entity("NonExistentTermXYZ1234") is None

    # Exception handling
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Network timeout")
        assert await provider.get_entity("Einstein") is None


def test_api_renders_entity_card_in_html(temp_storage, einstein_fixture):
    """Verify entity card appears on search results HTML and JSON API."""
    app = create_app(storage=temp_storage)
    client = TestClient(app)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = einstein_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        # 1. HTML request
        resp = client.get("/search?q=Albert+Einstein")
        assert resp.status_code == 200
        html = resp.text

        assert "entity-card" in html
        assert "Albert Einstein" in html
        assert "Q937" in html
        assert "Historial de cambios" in html
        assert "Wikipedia en Español" in html

        # 2. JSON request
        api_resp = client.get("/search?q=Albert+Einstein&format=json")
        assert api_resp.status_code == 200
        data = api_resp.json()
        assert data["entity_card"] is not None
        assert data["entity_card"]["title"] == "Albert Einstein"
        assert data["entity_card"]["wikibase_item"] == "Q937"
