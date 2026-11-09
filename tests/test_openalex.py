# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Dedicated test suite for OpenAlex scholarly search provider.

Verifies:
1. Controlled deactivation when OPENALEX_API_KEY is missing (no demo quota in production).
2. Sliding-window rate limit (1 credit per list query) and TTL cache.
3. HTTP 409 / 429 / 500 defensive error handling.
4. Strict prohibition of claiming unverified peer-reviewed status.
5. Real recorded response contract test.
6. Isolation from general search unless category='library' or academic opt-in.
"""

import json
from pathlib import Path
from unittest.mock import patch, AsyncMock
import httpx
import pytest

from senda.providers.openalex import OpenAlexProvider
from senda.providers.aggregator import ProviderAggregator
from senda.providers.internal import InternalStorageProvider
from senda.indexer.storage import StorageEngine

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_storage(tmp_path):
    return StorageEngine(db_path=tmp_path / "test_openalex.db")


def test_openalex_disabled_without_api_key(caplog):
    """Verify that without OPENALEX_API_KEY, the provider is completely deactivated with a clear warning."""
    import logging
    with caplog.at_level(logging.WARNING):
        provider = OpenAlexProvider(api_key="", enabled=True)
        assert provider.is_configured is False
        assert provider._api_key == ""
        # Check clear log warning is emitted
        assert any("OPENALEX_API_KEY no configurada" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_openalex_disabled_returns_empty_without_network():
    """Verify an unconfigured OpenAlex provider immediately returns [] without network calls."""
    provider = OpenAlexProvider(api_key="")
    assert provider.is_configured is False
    res = await provider.search("quantum computing")
    assert res == []


def test_openalex_contract_real_response():
    """Contract test verifying exact mapping against real recorded OpenAlex API response."""
    fixture_path = FIXTURES_DIR / "openalex_response.json"
    assert fixture_path.exists(), "Contract fixture openalex_response.json must exist."

    with open(fixture_path, "r", encoding="utf-8") as f:
        real_data = json.load(f)

    oa = OpenAlexProvider(api_key="contract_test_key")
    items = oa.parse_response(real_data, category="library", page_size=10)

    assert len(items) == 3
    for it in items:
        assert it.title != ""
        assert it.url.startswith("http")
        assert it.source == "Ciencia Abierta (OpenAlex)"
        assert it.doc_type == "library"
        assert it.is_sponsored is False
        assert "revisión por pares no verificada" in it.snippet
        # Explicit check: must never claim generic peer review
        assert "revisada por pares" not in it.snippet
        assert "revisada por pares" not in it.why_seen

    # First item verification
    first = items[0]
    assert first.title == "Quantum computing"
    assert first.url == "https://iopscience.iop.org/article/10.1088/0034-4885/61/2/002/pdf"
    assert first.date == "1998"
    assert "Reports on Progress in Physics" in first.snippet
    assert "Artículo" in first.snippet


@pytest.mark.asyncio
async def test_openalex_cache_and_rate_limit():
    """Verify TTL cache prevents burning credits and rate limiter caps requests."""
    oa = OpenAlexProvider(api_key="valid_key", rate_limit_per_minute=2, cache_ttl_seconds=3600)
    fake_json = {
        "results": [
            {
                "id": "https://openalex.org/W1",
                "doi": "https://doi.org/10.1234/test",
                "title": "Quantum Study",
                "publication_year": 2026,
                "type": "article",
                "open_access": {"is_oa": True, "version": "publishedVersion"},
                "primary_location": {"pdf_url": "https://test.org/p.pdf", "source": {"display_name": "Test Journal"}},
                "authorships": [{"author": {"display_name": "Test Author"}}],
            }
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=fake_json)

        # 1. First call -> 1 network call
        items1 = await oa.search("quantum", category="library")
        assert len(items1) == 1
        assert mock_get.call_count == 1

        # 2. Duplicate call -> served from cache, zero network calls
        items2 = await oa.search("quantum", category="library")
        assert len(items2) == 1
        assert mock_get.call_count == 1

        # 3. Different query -> 2nd network call (consumes remaining limit)
        items3 = await oa.search("different_query", category="library")
        assert len(items3) == 1
        assert mock_get.call_count == 2

        # 4. Third different query -> blocked by rate limiter (rate_limit_per_minute=2)
        items4 = await oa.search("third_query", category="library")
        assert items4 == []
        assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_openalex_http_error_handling():
    """Verify robust handling of HTTP 409, 429, and network disconnects."""
    oa = OpenAlexProvider(api_key="valid_key")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # HTTP 429
        mock_get.return_value = httpx.Response(429)
        assert await oa.search("q_429") == []

        # HTTP 409
        mock_get.return_value = httpx.Response(409)
        assert await oa.search("q_409") == []

        # Exception
        mock_get.side_effect = httpx.ConnectTimeout("Timeout")
        assert await oa.search("q_timeout") == []


@pytest.mark.asyncio
async def test_openalex_opt_in_isolation(temp_storage):
    """Verify OpenAlex is never queried in general search unless library category or explicit opt-in."""
    internal = InternalStorageProvider(temp_storage)
    mock_oa = OpenAlexProvider(api_key="mock_key")

    with patch.object(mock_oa, "search", new_callable=AsyncMock, return_value=[]) as mock_search:
        aggregator = ProviderAggregator(
            internal_provider=internal,
            openalex_provider=mock_oa,
        )

        # 1. General search without opt-in: OpenAlex must NOT be invoked (Zero leakage)
        await aggregator.aggregate("general web query", category="all", opt_in_academic=False)
        assert mock_search.call_count == 0

        # 2. General search with category="web": must NOT be invoked
        await aggregator.aggregate("another web query", category="web", opt_in_academic=False)
        assert mock_search.call_count == 0

        # 3. Explicit category="library": must be invoked
        await aggregator.aggregate("academic query", category="library")
        assert mock_search.call_count == 1

        # 4. Explicit opt_in_academic=True: must be invoked even in category="all"
        await aggregator.aggregate("academic with opt-in", category="all", opt_in_academic=True)
        assert mock_search.call_count == 2
