# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for SearchProvider adapters, normalization, and aggregator."""

import pytest
from unittest.mock import patch, AsyncMock
import httpx
from senda.indexer.storage import StorageEngine
from senda.extractor.parser import ExtractedDocument
from senda.providers.base import SearchResultItem
from senda.providers.internal import InternalStorageProvider
from senda.providers.searxng import SearXNGProvider
from senda.providers.brave import BraveSearchProvider
from senda.providers.mojeek import MojeekProvider
from senda.providers.openalex import OpenAlexProvider
from senda.providers.aggregator import ProviderAggregator, BANG_SHORTCUTS


@pytest.fixture
def temp_storage(tmp_path):
    db_file = tmp_path / "test_providers.db"
    return StorageEngine(db_path=db_file)


@pytest.fixture
def sample_extracted_doc():
    return ExtractedDocument(
        url="https://www.gentoo.org/",
        title="Welcome to Gentoo Linux",
        description="Gentoo is a highly flexible Linux distribution.",
        language="en",
        headings="Get Gentoo Philosophy",
        body_text="Gentoo is a free operating system based on Linux that can be automatically optimized.",
        content_hash="gentoohash123",
        outgoing_links=["https://wiki.gentoo.org"]
    )


def test_search_result_item_normalization():
    item = SearchResultItem(
        title="Debian GNU/Linux",
        url="https://www.debian.org/",
        snippet="The Universal Operating System",
        source="Senda Local",
        why_seen="Índice propio",
        is_sponsored=False,
    )
    assert item.title == "Debian GNU/Linux"
    assert item.url == "https://www.debian.org/"
    assert item.is_sponsored is False
    assert "Índice" in item.why_seen


def test_bang_detection():
    # Detect !w
    res = ProviderAggregator.detect_bang("!w Debian")
    assert res is not None
    url, service = res
    assert "wikipedia" in url
    assert "Debian" in url
    assert service == "Wikipedia"

    # Detect !osm
    res_osm = ProviderAggregator.detect_bang("!osm Bogota")
    assert res_osm is not None
    assert "openstreetmap" in res_osm[0]

    # Non-bang returns None
    assert ProviderAggregator.detect_bang("linux kernel") is None


@pytest.mark.asyncio
async def test_internal_provider(temp_storage, sample_extracted_doc):
    temp_storage.upsert_document(sample_extracted_doc)
    provider = InternalStorageProvider(temp_storage)
    assert provider.name == "Senda Local"
    assert provider.is_configured is True

    items = await provider.search("Gentoo", category="all")
    assert len(items) >= 1
    assert items[0].source == "Senda Local"
    assert "BM25" in items[0].why_seen
    assert items[0].is_sponsored is False


@pytest.mark.asyncio
async def test_aggregator_deduplication_and_lenses(temp_storage, sample_extracted_doc):
    temp_storage.upsert_document(sample_extracted_doc)
    internal = InternalStorageProvider(temp_storage)
    aggregator = ProviderAggregator(internal_provider=internal)


    # Search with domain lens: boost gentoo.org
    items = await aggregator.aggregate(
        query="Gentoo",
        category="all",
        boost_domains=["gentoo.org"],
    )
    assert len(items) >= 1
    assert "gentoo.org" in items[0].url
    assert "promovido" in items[0].why_seen

    # Search with block list: block gentoo.org -> should be empty
    items_blocked = await aggregator.aggregate(
        query="Gentoo",
        category="all",
        block_domains=["gentoo.org"],
    )
    assert len(items_blocked) == 0


def test_provider_configuration_states():
    searx = SearXNGProvider("")
    assert searx.is_configured is False

    searx_configured = SearXNGProvider("http://localhost:8888")
    assert searx_configured.is_configured is True

    brave = BraveSearchProvider("")
    assert brave.is_configured is False

    brave_configured = BraveSearchProvider("secret_token")
    assert brave_configured.is_configured is True

    mojeek = MojeekProvider("")
    assert mojeek.is_configured is False


@pytest.mark.asyncio
async def test_searxng_provider_mocked():
    searx = SearXNGProvider("http://localhost:8888")
    fake_json = {
        "results": [
            {
                "title": "Debian Project",
                "url": "https://www.debian.org/",
                "content": "Debian is a complete Free Operating System.",
                "engine": "duckduckgo",
                "score": 0.95,
                "publishedDate": "2026-01-01",
                "thumbnail_src": "https://www.debian.org/logo.png",
            },
            {
                "title": "No URL item",
                "content": "Should be ignored",
            }
        ]
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=fake_json)
        results = await searx.search("Debian", category="images", page=1, safe_search="strict", time_filter="month", region="es")
        assert len(results) == 1
        item = results[0]
        assert item.title == "Debian Project"
        assert item.url == "https://www.debian.org/"
        assert item.snippet == "Debian is a complete Free Operating System."
        assert "duckduckgo" in item.source
        assert item.media_url == "https://www.debian.org/logo.png"
        assert "anonimizada" in item.why_seen

        # Error response returns empty
        mock_get.return_value = httpx.Response(500)
        assert await searx.search("Debian") == []

        # Exception returns empty
        mock_get.side_effect = httpx.ConnectError("Network unreachable")
        assert await searx.search("Debian") == []


@pytest.mark.asyncio
async def test_brave_provider_mocked():
    brave = BraveSearchProvider("brave_test_token_123")
    fake_json = {
        "web": {
            "results": [
                {
                    "title": "Arch Linux",
                    "url": "https://archlinux.org/",
                    "description": "A lightweight and flexible Linux distribution.",
                    "page_age": "2026-02-01",
                    "language": "en",
                    "is_sponsored": False,
                },
                {
                    "title": "No URL result",
                    "description": "Ignored",
                }
            ]
        }
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=fake_json)
        results = await brave.search("Arch", category="all", page=2, page_size=5, safe_search="moderate", region="co", time_filter="w")
        assert len(results) == 1
        item = results[0]
        assert item.title == "Arch Linux"
        assert item.url == "https://archlinux.org/"
        assert item.snippet == "A lightweight and flexible Linux distribution."
        assert item.source == "Brave Search"
        assert "Brave Search API" in item.why_seen

        # Error handling
        mock_get.return_value = httpx.Response(403)
        assert await brave.search("Arch") == []

        mock_get.side_effect = httpx.ReadTimeout("Timeout")
        assert await brave.search("Arch") == []


@pytest.mark.asyncio
async def test_mojeek_provider_mocked():
    mojeek = MojeekProvider("mojeek_test_token_456")
    fake_json = {
        "response": {
            "results": [
                {
                    "title": "Trisquel GNU/Linux",
                    "url": "https://trisquel.info/",
                    "desc": "A 100% Free Software operating system.",
                    "date": "2026-03-15",
                },
                {
                    "title": "Item without URL",
                    "desc": "Skip me",
                }
            ]
        }
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=fake_json)
        results = await mojeek.search("Trisquel", safe_search="strict", page=2, page_size=10)
        assert len(results) == 1
        item = results[0]
        assert item.title == "Trisquel GNU/Linux"
        assert item.url == "https://trisquel.info/"
        assert item.snippet == "A 100% Free Software operating system."
        assert item.source == "Mojeek"
        assert "Mojeek Ltd" in item.why_seen

        # Error response
        mock_get.return_value = httpx.Response(502)
        assert await mojeek.search("Trisquel") == []

        mock_get.side_effect = Exception("General error")
        assert await mojeek.search("Trisquel") == []


@pytest.mark.asyncio
async def test_aggregator_multi_provider_fusion(temp_storage):
    searx = SearXNGProvider("http://localhost:8888")
    brave = BraveSearchProvider("brave_token")
    mojeek = MojeekProvider("mojeek_token")
    internal = InternalStorageProvider(temp_storage)
    openalex = OpenAlexProvider(enabled=False)

    searx_res = [
        SearchResultItem(title="Senda Meta", url="https://senda.ideh.top", snippet="Senda search", source="SearXNG (google)", why_seen="Meta")
    ]
    brave_res = [
        SearchResultItem(title="Senda Brave Duplicate", url="https://senda.ideh.top", snippet="Duplicate url", source="Brave Search", why_seen="Brave"),
        SearchResultItem(title="GNU Org", url="https://gnu.org", snippet="GNU system", source="Brave Search", why_seen="Brave"),
    ]
    mojeek_res = [
        SearchResultItem(title="FSF Org", url="https://fsf.org", snippet="Free Software", source="Mojeek", why_seen="Mojeek"),
    ]

    with patch.object(searx, "search", new_callable=AsyncMock, return_value=searx_res), \
         patch.object(brave, "search", new_callable=AsyncMock, return_value=brave_res), \
         patch.object(mojeek, "search", new_callable=AsyncMock, return_value=mojeek_res):

        aggregator = ProviderAggregator(
            internal_provider=internal,
            searxng_provider=searx,
            brave_provider=brave,
            mojeek_provider=mojeek,
            openalex_provider=openalex,
        )

        fused = await aggregator.aggregate("free software", category="all", page=1, page_size=10)

        # Ensure deduplication: senda.ideh.top only appears once
        urls = [r.url for r in fused]
        assert urls.count("https://senda.ideh.top") == 1
        assert "https://gnu.org" in urls
        assert "https://fsf.org" in urls


@pytest.mark.asyncio
async def test_openalex_provider_mocked():
    oa_provider = OpenAlexProvider(enabled=True)
    assert oa_provider.name == "OpenAlex (Ciencia Abierta)"
    assert oa_provider.is_configured is True

    fake_json = {
        "meta": {"count": 100},
        "results": [
            {
                "id": "https://openalex.org/W123456",
                "doi": "https://doi.org/10.1234/example.2026",
                "title": "Quantum Computing and Ethical Open Architectures",
                "publication_year": 2026,
                "open_access": {
                    "is_oa": True,
                    "oa_url": "https://arxiv.org/pdf/2026.12345.pdf",
                    "oa_status": "gold",
                },
                "primary_location": {
                    "pdf_url": "https://arxiv.org/pdf/2026.12345.pdf",
                    "landing_page_url": "https://arxiv.org/abs/2026.12345",
                    "source": {
                        "display_name": "arXiv.org",
                    }
                },
                "authorships": [
                    {"author": {"display_name": "Ada Lovelace"}},
                    {"author": {"display_name": "Alan Turing"}},
                    {"author": {"display_name": "Claude Shannon"}},
                    {"author": {"display_name": "Richard Stallman"}},
                ]
            },
            {
                "id": "https://openalex.org/W999",
                # Missing title should be safely skipped
            }
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=fake_json)
        results = await oa_provider.search("quantum", category="library")
        assert len(results) == 1
        item = results[0]
        assert item.title == "Quantum Computing and Ethical Open Architectures"
        assert item.url == "https://arxiv.org/pdf/2026.12345.pdf"
        assert "[PDF Abierto]" in item.snippet
        assert "arXiv.org" in item.snippet
        assert "Ada Lovelace" in item.snippet
        assert "et al." in item.snippet
        assert item.source == "Ciencia Abierta (OpenAlex)"
        assert item.doc_type == "library"
        assert item.score == 45.0  # library vertical boost
        assert "Acceso Abierto (OA)" in item.why_seen

        # Error response returns empty
        mock_get.return_value = httpx.Response(500)
        assert await oa_provider.search("quantum") == []

        # Exception returns empty
        mock_get.side_effect = httpx.ConnectError("Timeout")
        assert await oa_provider.search("quantum") == []

    # Disabled provider
    disabled_provider = OpenAlexProvider(enabled=False)
    assert disabled_provider.is_configured is False
    assert await disabled_provider.search("quantum") == []


def test_open_access_bang_shortcuts():
    res_oa = ProviderAggregator.detect_bang("!oa artificial intelligence")
    assert res_oa is not None
    assert "openalex.org" in res_oa[0]

    res_arxiv = ProviderAggregator.detect_bang("!arxiv neural networks")
    assert res_arxiv is not None
    assert "arxiv.org" in res_arxiv[0]
