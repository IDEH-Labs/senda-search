# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Tests for Open Access CC0 Museums & Enhanced Free Culture Image Search."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from senda.providers.museums import OpenAccessMuseumProvider
from senda.providers.images import FreeCultureImageProvider
from senda.providers.openverse import OpenverseProvider
from senda.providers.aggregator import ProviderAggregator


@pytest.fixture
def cma_sample_fixture():
    return {
        "data": [
            {
                "id": 12345,
                "title": "Water Lilies (Nymphéas)",
                "creators": [
                    {"description": "Claude Monet (French, 1840-1926)"}
                ],
                "images": {
                    "web": {"url": "https://openaccess-cdn.clevelandart.org/1960.81/1960.81_web.jpg"},
                    "print": {"url": "https://openaccess-cdn.clevelandart.org/1960.81/1960.81_print.jpg"}
                },
                "url": "https://www.clevelandart.org/art/1960.81",
                "creation_date": "1914-1926",
                "dimensions": "200.7 x 426.7 cm",
                "tombstone": "Oil on canvas, 1914-1926"
            }
        ]
    }


@pytest.fixture
def aic_sample_fixture():
    return {
        "data": [
            {
                "id": 6565,
                "title": "The Bedroom",
                "artist_title": "Vincent van Gogh",
                "image_id": "25c31d8d-21a4-9ea1-1d73-6a4cedcedced",
                "date_display": "1889",
                "dimensions": "73.6 × 92.3 cm (29 × 36 5/8 in.)"
            }
        ]
    }


def test_parse_cma(cma_sample_fixture):
    """Verify Cleveland Museum of Art CC0 parser returns normalized SearchResultItem with download_url & dimensions."""
    provider = OpenAccessMuseumProvider()
    items = provider.parse_cma(cma_sample_fixture)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Water Lilies (Nymphéas)"
    assert item.doc_type == "images"
    assert "Cleveland Museum of Art" in item.source
    assert item.media_url == "https://openaccess-cdn.clevelandart.org/1960.81/1960.81_web.jpg"
    assert item.download_url == "https://openaccess-cdn.clevelandart.org/1960.81/1960.81_print.jpg"
    assert item.dimensions == "200.7 x 426.7 cm"
    assert "CC0" in item.license
    assert "Claude Monet" in item.authors[0]
    assert item.is_sponsored is False


def test_parse_aic(aic_sample_fixture):
    """Verify Art Institute of Chicago CC0 parser returns IIIF image URLs and direct download URLs."""
    provider = OpenAccessMuseumProvider()
    items = provider.parse_aic(aic_sample_fixture)

    assert len(items) == 1
    item = items[0]
    assert item.title == "The Bedroom"
    assert item.doc_type == "images"
    assert "Art Institute of Chicago" in item.source
    assert "25c31d8d-21a4-9ea1-1d73-6a4cedcedced" in item.media_url
    assert "1686" in item.download_url
    assert item.dimensions == "73.6 × 92.3 cm (29 × 36 5/8 in.)"
    assert "CC0" in item.license
    assert item.authors[0] == "Vincent van Gogh"


@pytest.mark.asyncio
async def test_museums_search_mock(cma_sample_fixture, aic_sample_fixture):
    """Verify OpenAccessMuseumProvider aggregates both CMA and AIC results."""
    provider = OpenAccessMuseumProvider()

    mock_resp_cma = MagicMock()
    mock_resp_cma.status_code = 200
    mock_resp_cma.json.return_value = cma_sample_fixture

    mock_resp_aic = MagicMock()
    mock_resp_aic.status_code = 200
    mock_resp_aic.json.return_value = aic_sample_fixture

    async def mock_get(url, **kwargs):
        if "clevelandart.org" in url:
            return mock_resp_cma
        return mock_resp_aic

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        items = await provider.search("art", category="images", page=1, page_size=10)

    assert len(items) == 2
    sources = [it.source for it in items]
    assert any("Cleveland" in s for s in sources)
    assert any("Chicago" in s for s in sources)


@pytest.mark.asyncio
async def test_aggregator_routes_images_to_museums():
    """Verify that ProviderAggregator dispatches category='images' to museum provider."""
    mock_museums = AsyncMock()
    mock_museums.is_configured = True
    mock_museums.search.return_value = []

    mock_images = AsyncMock()
    mock_images.is_configured = True
    mock_images.search.return_value = []

    mock_openverse = AsyncMock()
    mock_openverse.is_configured = True
    mock_openverse.search.return_value = []

    mock_internal = AsyncMock()
    mock_internal.search.return_value = []

    aggregator = ProviderAggregator(
        internal_provider=mock_internal,
        image_provider=mock_images,
        openverse_provider=mock_openverse,
        museum_provider=mock_museums,
    )

    await aggregator.aggregate(query="van gogh", category="images")

    mock_museums.search.assert_called_once()
    mock_images.search.assert_called_once()
    mock_openverse.search.assert_called_once()
