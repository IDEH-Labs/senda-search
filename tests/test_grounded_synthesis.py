# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit and API tests for Grounded AI Synthesis and Ethical Provenance."""

import pytest
from fastapi.testclient import TestClient

from senda.ai.grounded_synthesis import GroundedSynthesizer, GroundedSynthesisResult
from senda.providers.base import SearchResultItem
from senda.api.app import create_app
from senda.indexer.storage import StorageEngine
from senda.extractor.parser import ExtractedDocument


@pytest.fixture
def temp_storage(tmp_path):
    db_file = tmp_path / "test_synth.db"
    return StorageEngine(db_file)


def test_synthesis_disabled_by_default_returns_none():
    """Verify synthesizer returns None when disabled and not forced."""
    synth = GroundedSynthesizer(enabled=False)
    items = [
        SearchResultItem(
            url="https://fsf.org",
            title="Free Software Foundation",
            snippet="Software freedom is a matter of liberty, not price.",
            source="FSF",
        )
    ]
    res = synth.synthesize("software freedom", items, force=False)
    assert res is None


def test_synthesis_refusal_when_no_items():
    """Verify synthesizer strictly refuses to answer when retrieved items are empty."""
    synth = GroundedSynthesizer(enabled=True)
    res = synth.synthesize("quantum computing", [], force=True)
    assert res is not None
    assert res.is_refusal is True
    assert "No se encontraron fuentes primarias suficientes" in res.summary
    assert len(res.citations) == 0


def test_synthesis_refusal_when_snippets_empty():
    """Verify synthesizer strictly refuses when items lack meaningful textual content."""
    synth = GroundedSynthesizer(enabled=True)
    items = [
        SearchResultItem(
            url="https://empty.org",
            title="Empty",
            snippet="",
            source="Empty",
        )
    ]
    res = synth.synthesize("test", items, force=True)
    assert res is not None
    assert res.is_refusal is True
    assert len(res.citations) == 0


def test_synthesis_grounded_with_valid_items():
    """Verify valid items produce bracketed citations and attribution disclaimer."""
    synth = GroundedSynthesizer(enabled=True)
    items = [
        SearchResultItem(
            url="https://fsf.org/about",
            title="What is Free Software",
            snippet="Free software gives users control over their computing. The four essential freedoms define it.",
            source="FSF",
            authors=["Richard Stallman"],
            published_date="2026-01-01",
        ),
        SearchResultItem(
            url="https://eff.org/privacy",
            title="Digital Privacy in 2026",
            snippet="Protecting encryption is crucial to human autonomy and digital privacy rights.",
            source="EFF",
            authors=["EFF Staff"],
            published_date="2026-02-15",
        ),
    ]

    res = synth.synthesize("digital rights", items, force=True)
    assert res is not None
    assert res.is_refusal is False
    assert len(res.citations) == 2
    assert "[1]" in res.summary
    assert "[2]" in res.summary
    assert "Aviso de procedencia" in res.disclaimer
    assert "Senda no certifica verdad" in res.disclaimer

    c1 = res.citations[0]
    assert c1.index == 1
    assert c1.url == "https://fsf.org/about"
    assert "Richard Stallman" in c1.author

    c2 = res.citations[1]
    assert c2.index == 2
    assert c2.url == "https://eff.org/privacy"
    assert "EFF Staff" in c2.author


def test_api_synthesis_opt_in_renders_in_html(temp_storage):
    """Verify synthesis is included in HTML results when requested with synthesis=true."""
    # Seed storage with a test document
    doc = ExtractedDocument(
        url="https://gnu.org/philosophy",
        title="GNU Philosophy and Free Software",
        description="Software freedom respects user rights and community sovereignty.",
        language="es",
        headings="Filosofía del Software Libre",
        body_text="Software freedom respects user rights and community sovereignty.",
        content_hash="abc123hash",
        text_density=0.85,
        doc_type="web",
    )
    temp_storage.upsert_document(doc)

    app = create_app(storage=temp_storage)
    client = TestClient(app)

    # Request with synthesis=true
    resp = client.get("/search?q=freedom&synthesis=true")
    assert resp.status_code == 200
    html = resp.text

    assert "grounded-answer-box" in html
    assert "Síntesis Asistida de Procedencia" in html
    assert "Senda no certifica verdad ni emite veredictos propios" in html
