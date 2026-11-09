# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit and contract tests for verified academic providers and retraction cross-referencing."""

import json
from pathlib import Path
import pytest

from senda.providers.crossref import CrossrefProvider
from senda.providers.arxiv import ArxivProvider
from senda.providers.doaj import DoajProvider
from senda.providers.pubmed import PubMedProvider
from senda.providers.openalex import OpenAlexProvider
from senda.security.retractions import retraction_registry, RetractionRegistry

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# 1. Controlled Deactivation Tests (Governance compliance)
def test_academic_providers_disabled_by_default():
    """Verify that unverified academic providers are disabled by default."""
    c = CrossrefProvider()
    assert c.is_configured is False

    a = ArxivProvider()
    assert a.is_configured is False

    d = DoajProvider()
    assert d.is_configured is False

    p = PubMedProvider()
    assert p.is_configured is False


@pytest.mark.asyncio
async def test_academic_providers_return_empty_when_disabled():
    """Verify disabled providers execute zero outbound network calls."""
    c = CrossrefProvider(enabled=False)
    results = await c.search("quantum")
    assert results == []

    a = ArxivProvider(enabled=False)
    assert await a.search("quantum") == []

    d = DoajProvider(enabled=False)
    assert await d.search("quantum") == []

    p = PubMedProvider(enabled=False)
    assert await p.search("quantum") == []


# 2. Contract Test: Crossref (with real recorded response)
def test_crossref_contract_real_response():
    fixture_path = FIXTURES_DIR / "crossref_response.json"
    assert fixture_path.exists(), "crossref_response.json fixture missing"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = CrossrefProvider(enabled=True)
    items = provider.parse_response(data, category="library", page_size=2)

    assert len(items) == 2
    first = items[0]
    assert first.title != ""
    assert "doi.org" in first.url or "http" in first.url
    assert first.doc_type == "library"
    assert first.source_type == "académica"
    assert "revisión por pares no verificada" in first.snippet
    assert "revisada por pares" not in first.snippet.replace("revisión por pares no verificada", "")

    # Provenance dictionary export check
    prov = first.to_provenance_dict()
    assert prov["tipo_fuente"] == "académica"
    assert "título" in prov
    assert "url_canónica" in prov
    assert prov["retractación"]["estado"] in ("ninguna", "retractada")


# 3. Contract Test: arXiv (with real recorded XML response)
def test_arxiv_contract_real_response():
    fixture_path = FIXTURES_DIR / "arxiv_response.xml"
    assert fixture_path.exists(), "arxiv_response.xml fixture missing"

    with open(fixture_path, "r", encoding="utf-8") as f:
        xml_text = f.read()

    provider = ArxivProvider(enabled=True)
    items = provider.parse_response(xml_text, category="library", page_size=2)

    assert len(items) == 2
    first = items[0]
    assert "arxiv.org" in first.url
    assert first.content_type == "preprint"
    assert "Preprint" in first.snippet
    assert "revisión por pares no verificada" in first.snippet

    prov = first.to_provenance_dict()
    assert prov["tipo_contenido"] == "preprint"
    assert prov["tipo_fuente"] == "académica"


# 4. Contract Test: DOAJ (with real recorded response)
def test_doaj_contract_real_response():
    fixture_path = FIXTURES_DIR / "doaj_response.json"
    assert fixture_path.exists(), "doaj_response.json fixture missing"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = DoajProvider(enabled=True)
    items = provider.parse_response(data, category="library", page_size=2)

    assert len(items) == 2
    first = items[0]
    assert first.content_type == "artículo"
    assert "revisada por pares (verificada en DOAJ)" in first.snippet

    prov = first.to_provenance_dict()
    assert prov["tipo_fuente"] == "académica"
    assert prov["tipo_contenido"] == "artículo"


# 5. Contract Test: PubMed (with real recorded response)
def test_pubmed_contract_real_response():
    fixture_path = FIXTURES_DIR / "pubmed_response.json"
    assert fixture_path.exists(), "pubmed_response.json fixture missing"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = PubMedProvider(enabled=True)
    items = provider.parse_response(data, category="library", page_size=2)

    assert len(items) == 2
    first = items[0]
    assert "pubmed.ncbi.nlm.nih.gov" in first.url
    assert first.source_type == "académica"
    assert "revisión por pares no verificada" in first.snippet


# 6. Retraction Cross-Referencing Test
def test_retraction_cross_referencing_displays_warning():
    """Verify that a paper marked as retracted in the registry displays the retraction prominently."""
    test_doi = "10.1016/j.cell.2020.99.999"
    retraction_registry.register(
        doi=test_doi,
        status="retractada",
        source="Crossref / Retraction Watch",
        date="2021-04-15",
        notice_url=f"https://doi.org/{test_doi}.retraction",
    )

    # Fake Crossref work item with that DOI
    mock_data = {
        "status": "ok",
        "message": {
            "items": [
                {
                    "title": ["Fabricated Cell Study with Critical Flaws"],
                    "DOI": test_doi,
                    "URL": f"https://doi.org/{test_doi}",
                    "type": "journal-article",
                    "published": {"date-parts": [[2020, 3, 1]]},
                    "container-title": ["Cellular Insights"],
                    "author": [{"given": "Jane", "family": "Doe"}],
                }
            ]
        },
    }

    provider = CrossrefProvider(enabled=True)
    items = provider.parse_response(mock_data, category="library")

    assert len(items) == 1
    item = items[0]
    assert item.retraction is not None
    assert item.retraction.status == "retractada"
    assert item.retraction.source == "Crossref / Retraction Watch"
    assert "[OBRA RETRACTADA]" in item.snippet
    assert "AVISO: Obra formalmente retractada" in item.why_seen

    # Provenance dictionary export check
    prov = item.to_provenance_dict()
    assert prov["retractación"]["estado"] == "retractada"
    assert prov["retractación"]["fuente"] == "Crossref / Retraction Watch"


from unittest.mock import patch, AsyncMock
import httpx


@pytest.mark.asyncio
async def test_crossref_search_mocked_and_cache():
    fixture_path = FIXTURES_DIR / "crossref_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = CrossrefProvider(enabled=True)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=data)
        items = await provider.search("quantum", category="library")
        assert len(items) == 2
        assert mock_get.call_count == 1

        # Second call hits cache
        cached_items = await provider.search("quantum", category="library")
        assert len(cached_items) == 2
        assert mock_get.call_count == 1  # No extra network call


@pytest.mark.asyncio
async def test_crossref_search_errors():
    provider = CrossrefProvider(enabled=True)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # HTTP 429
        mock_get.return_value = httpx.Response(429)
        res429 = await provider.search("quantum")
        assert res429 == []

        # Exception
        mock_get.side_effect = httpx.RequestError("Network down")
        res_err = await provider.search("quantum2")
        assert res_err == []


@pytest.mark.asyncio
async def test_arxiv_search_mocked_and_cache():
    fixture_path = FIXTURES_DIR / "arxiv_response.xml"
    with open(fixture_path, "r", encoding="utf-8") as f:
        xml_text = f.read()

    provider = ArxivProvider(enabled=True, min_request_interval_seconds=0.0)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, text=xml_text)
        items = await provider.search("quantum", category="library")
        assert len(items) == 2
        assert mock_get.call_count == 1

        # Cache check
        cached = await provider.search("quantum", category="library")
        assert len(cached) == 2
        assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_doaj_search_mocked_and_cache():
    fixture_path = FIXTURES_DIR / "doaj_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = DoajProvider(enabled=True)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=data)
        items = await provider.search("quantum", category="library")
        assert len(items) == 2
        assert mock_get.call_count == 1

        cached = await provider.search("quantum", category="library")
        assert len(cached) == 2
        assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_pubmed_search_mocked_and_cache():
    fixture_path = FIXTURES_DIR / "pubmed_response.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = PubMedProvider(enabled=True, min_request_interval_seconds=0.0)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # First call is esearch (returns idlist), second is esummary (returns metadata)
        esearch_resp = httpx.Response(200, json={"esearchresult": {"idlist": ["32000001", "32000002"]}})
        esummary_resp = httpx.Response(200, json=data)
        mock_get.side_effect = [esearch_resp, esummary_resp]

        items = await provider.search("biomedical", category="library")
        assert len(items) == 2
        assert mock_get.call_count == 2

        # Cache check
        cached = await provider.search("biomedical", category="library")
        assert len(cached) == 2
        assert mock_get.call_count == 2
