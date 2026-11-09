# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for SearchProvider adapters, normalization, and aggregator."""

import pytest
from senda.indexer.storage import StorageEngine
from senda.extractor.parser import ExtractedDocument
from senda.providers.base import SearchResultItem
from senda.providers.internal import InternalStorageProvider
from senda.providers.searxng import SearXNGProvider
from senda.providers.brave import BraveSearchProvider
from senda.providers.mojeek import MojeekProvider
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
