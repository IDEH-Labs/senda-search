# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit and contract tests for Fediverse and Bluesky open social providers."""

import json
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from senda.providers.fediverse import FediverseProvider
from senda.providers.bluesky import BlueskyProvider
from senda.providers.aggregator import ProviderAggregator


@pytest.fixture
def mastodon_fixture():
    fixture_path = Path(__file__).parent / "fixtures" / "mastodon_tag_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def bluesky_fixture():
    fixture_path = Path(__file__).parent / "fixtures" / "bluesky_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_fediverse_parsing_real_contract_fixture(mastodon_fixture):
    """Verify FediverseProvider accurately parses recorded real Mastodon status responses."""
    provider = FediverseProvider(instance="mastodon.social", enabled=True)
    items = provider._parse_statuses(mastodon_fixture)

    assert len(items) == 2
    first = items[0]
    assert "@LibreOfficeDE" in first.authors[0]
    assert first.source_type == "red_abierta"
    assert first.content_type == "publicación"
    assert first.provider_origin == "ActivityPub"
    assert first.ai_provenance is not None
    assert first.ai_provenance.status == "no determinado"
    assert "https://social.tchncs.de/@LibreOfficeDE/" in first.url
    assert "LibreOffice" in first.snippet


@pytest.mark.asyncio
async def test_bluesky_parsing_real_contract_fixture(bluesky_fixture):
    """Verify BlueskyProvider accurately parses recorded real ATProto search responses."""
    provider = BlueskyProvider(endpoint="https://api.bsky.app", enabled=True)
    posts = bluesky_fixture.get("posts", [])
    items = provider._parse_posts(posts)

    assert len(items) == 2
    first = items[0]
    assert "@linux.mastodon.uno.ap.brid.gy" in first.authors[0]
    assert first.source == "ATProto (Bluesky)"
    assert first.source_type == "red_abierta"
    assert first.content_type == "publicación"
    assert first.provider_origin == "ATProto"
    assert first.ai_provenance is not None
    assert first.ai_provenance.status == "no determinado"
    assert "https://bsky.app/profile/linux.mastodon.uno.ap.brid.gy/post/" in first.url
    assert "software libero" in first.snippet.lower() or "foss" in first.snippet.lower()


@pytest.mark.asyncio
async def test_fediverse_disabled_returns_empty():
    """Verify that disabled Fediverse provider emits zero requests and returns empty."""
    provider = FediverseProvider(enabled=False)
    assert not provider.is_configured
    results = await provider.search("freesoftware")
    assert results == []


@pytest.mark.asyncio
async def test_bluesky_disabled_returns_empty():
    """Verify that disabled Bluesky provider emits zero requests and returns empty."""
    provider = BlueskyProvider(enabled=False)
    assert not provider.is_configured
    results = await provider.search("freesoftware")
    assert results == []


@pytest.mark.asyncio
async def test_category_isolation_in_aggregator():
    """Verify that general search (category='all') NEVER queries Fediverse or Bluesky."""
    mock_fediverse = AsyncMock()
    mock_bluesky = AsyncMock()
    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        fediverse_provider=mock_fediverse,
        bluesky_provider=mock_bluesky,
    )

    # General search: must NOT call social providers
    await aggregator.aggregate(query="linux", category="all")
    mock_fediverse.search.assert_not_called()
    mock_bluesky.search.assert_not_called()

    # Explicit 'social' category: must call social providers
    await aggregator.aggregate(query="linux", category="social")
    mock_fediverse.search.assert_called_once()
    mock_bluesky.search.assert_called_once()


def test_bang_shortcuts_for_social():
    """Verify that !masto and !bsky bang shortcuts redirect properly."""
    masto_redir = ProviderAggregator.detect_bang("!masto privacy")
    assert masto_redir is not None
    url, service = masto_redir
    assert "https://mastodon.social/search?q=privacy" in url
    assert "Mastodon" in service

    bsky_redir = ProviderAggregator.detect_bang("!bsky sovereignty")
    assert bsky_redir is not None
    b_url, b_service = bsky_redir
    assert "https://bsky.app/search?q=sovereignty" in b_url
    assert "Bluesky" in b_service


@pytest.mark.asyncio
async def test_fediverse_search_flows(mastodon_fixture):
    """Verify mock HTTP flows for tag retrieval, fallback, and errors."""
    provider = FediverseProvider(instance="mastodon.social", enabled=True)

    # Empty query
    assert await provider.search("   ") == []

    # Tag search success
    mock_resp_tag = MagicMock()
    mock_resp_tag.status_code = 200
    mock_resp_tag.json.return_value = mastodon_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp_tag
        items = await provider.search("freesoftware")
        assert len(items) == 2

    # Tag empty, fallback to search API
    mock_resp_empty = MagicMock()
    mock_resp_empty.status_code = 200
    mock_resp_empty.json.return_value = []

    mock_resp_search = MagicMock()
    mock_resp_search.status_code = 200
    mock_resp_search.json.return_value = {"statuses": mastodon_fixture}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [mock_resp_empty, mock_resp_search]
        items = await provider.search("something")
        assert len(items) == 2

    # Network exception handling returns empty list safely
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        items = await provider.search("fail")
        assert items == []


@pytest.mark.asyncio
async def test_bluesky_search_flows(bluesky_fixture):
    """Verify mock HTTP flows for Bluesky search and error handling."""
    provider = BlueskyProvider(endpoint="https://api.bsky.app", enabled=True)

    # Empty query
    assert await provider.search("") == []

    # Success flow
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = bluesky_fixture

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        items = await provider.search("linux")
        assert len(items) == 2

    # 500 error flow
    mock_err_resp = MagicMock()
    mock_err_resp.status_code = 500
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_err_resp
        items = await provider.search("error")
        assert items == []

    # Exception flow
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        items = await provider.search("timeout")
        assert items == []

