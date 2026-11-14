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


@pytest.mark.asyncio
async def test_burundi_official_website_override():
    """Verify that sovereign entity Burundi (Q967) uses the verified official portal presidence.gov.bi."""
    from senda.ranking.navigational import NavigationalEngine
    provider = WikipediaEntityProvider()

    summary_fixture = {
        "title": "Burundi",
        "extract": "Burundi es un Estado soberano en África Oriental.",
        "description": "país de África Oriental",
        "content_urls": {
            "desktop": {"page": "https://es.wikipedia.org/wiki/Burundi"},
            "mobile": {"page": "https://es.m.wikipedia.org/wiki/Burundi"}
        },
        "wikibase_item": "Q967"
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = summary_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        card = await provider.get_entity("Burundi", lang="es", fetch_official_website=True)

    assert card is not None
    assert card.official_website == "https://presidence.gov.bi/"

    # Also test NavigationalEngine instant direct query
    nav = NavigationalEngine.resolve("burundi")
    assert nav is not None
    assert nav.url == "https://presidence.gov.bi/"
    assert "Burundi" in nav.title


def test_sanitize_official_website():
    """Verify ethical sanitization, HTTPS upgrading, tracker stripping, and spam rejection."""
    from senda.providers.wikipedia import sanitize_official_website

    # Upgrades http to https
    assert sanitize_official_website("http://example.org") == "https://example.org/"
    assert sanitize_official_website("https://example.org/about") == "https://example.org/about"

    # Strips tracker query parameters
    dirty = "https://institution.org/portal?utm_source=wiki&utm_medium=referral&keep=1"
    clean = sanitize_official_website(dirty)
    assert clean == "https://institution.org/portal?keep=1"
    assert "utm_source" not in clean

    # Rejects spam brokers and parked domains
    assert sanitize_official_website("http://sedoparking.com/land") is None
    assert sanitize_official_website("https://sub.hugedomains.com/") is None
    assert sanitize_official_website("http://parkingcrew.net") is None

    # Rejects invalid formats and localhost
    assert sanitize_official_website("not-a-url") is None
    assert sanitize_official_website("http://localhost:8000") is None
    assert sanitize_official_website("http://127.0.0.1/") is None
    assert sanitize_official_website(None) is None


@pytest.mark.asyncio
async def test_sovereign_country_universal_coverage_across_continents():
    """Verify that multiple sovereign states across all continents resolve their verified portals."""
    from senda.ranking.navigational import NavigationalEngine
    provider = WikipediaEntityProvider()

    test_cases = [
        ("Tanzania", "Q924", "https://www.ikulu.go.tz/"),
        ("Vietnam", "Q881", "https://chinhphu.vn/"),
        ("El Salvador", "Q792", "https://www.transparencia.gob.sv/"),
        ("Sudáfrica", "Q258", "https://www.gov.za/"),
        ("Trinidad y Tobago", "Q754", "https://www.ttconnect.gov.tt/"),
        ("República Democrática del Congo", "Q974", "https://www.primature.gouv.cd/"),
        ("Turquía", "Q43", "https://www.turkiye.gov.tr/"),
    ]

    for title, qid, expected_url in test_cases:
        summary_fixture = {
            "title": title,
            "extract": f"Estado soberano {title}.",
            "description": f"País {title}",
            "content_urls": {
                "desktop": {"page": f"https://es.wikipedia.org/wiki/{title}"},
                "mobile": {"page": f"https://es.m.wikipedia.org/wiki/{title}"}
            },
            "wikibase_item": qid
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = summary_fixture

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            card = await provider.get_entity(title, lang="es", fetch_official_website=True)

        assert card is not None, f"Failed entity card for {title}"
        assert card.official_website == expected_url, f"Expected {expected_url} for {title}, got {card.official_website}"

        # Navigational resolution test
        nav = NavigationalEngine.resolve(title)
        assert nav is not None, f"NavigationalEngine failed to resolve {title}"
        assert nav.url == expected_url, f"NavigationalEngine returned {nav.url} instead of {expected_url} for {title}"


@pytest.mark.asyncio
async def test_celebrity_figure_typo_fallback():
    """Verify that person names with typos resolve via OpenSearch fallback."""
    provider = WikipediaEntityProvider()

    # When querying with typo 'gabriel garcia markez':
    # 1st call to summary returns 404
    # 2nd call to OpenSearch returns ['Gabriel garcia marquez']
    # 3rd call to summary of 'Gabriel garcia marquez' returns 200
    mock_404 = MagicMock(status_code=404)
    mock_opensearch = MagicMock(
        status_code=200,
        json=MagicMock(return_value=["gabriel garcia markez", ["Gabriel García Márquez"]])
    )
    mock_summary = MagicMock(
        status_code=200,
        json=MagicMock(return_value={
            "title": "Gabriel García Márquez",
            "extract": "Gabriel José de la Concordia García Márquez fue un escritor y periodista colombiano.",
            "description": "Escritor colombiano, premio Nobel de Literatura",
            "wikibase_item": "Q5878",
            "content_urls": {
                "desktop": {"page": "https://es.wikipedia.org/wiki/Gabriel_Garc%C3%ADa_M%C3%A1rquez"}
            }
        })
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [mock_404, mock_404, mock_opensearch, mock_summary]
        card = await provider.get_entity("gabriel garcia markez", lang="es")

    assert card is not None
    assert card.title == "Gabriel García Márquez"
    assert "escritor" in card.extract.lower()


