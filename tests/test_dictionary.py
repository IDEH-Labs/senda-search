# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit and integration tests for Senda Sovereign Dictionary Provider."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from senda.api.app import create_app
from senda.indexer.storage import StorageEngine
from senda.providers.openalex import OpenAlexProvider
from senda.dictionary import (
    extract_dictionary_term,
    parse_wiktionary_extract,
    DictionaryProvider,
    DictionaryCard,
    DictionarySense,
)


@pytest.fixture
def client(tmp_path):
    storage = StorageEngine(db_path=tmp_path / "dict_test.db")
    app = create_app(
        storage=storage,
        openalex_provider=OpenAlexProvider(enabled=False),
        enable_federated_providers=False,
    )
    return TestClient(app)


def test_extract_dictionary_term():
    # Spanish definitions
    assert extract_dictionary_term("definición de resiliencia") == ("resiliencia", "es", "definition")
    assert extract_dictionary_term("definición resiliencia") == ("resiliencia", "es", "definition")
    assert extract_dictionary_term("qué significa entropía?") == ("entropía", "es", "definition")
    assert extract_dictionary_term("significado de altruismo") == ("altruismo", "es", "definition")
    assert extract_dictionary_term("definir soberanía") == ("soberanía", "es", "definition")
    assert extract_dictionary_term("dict: libertad") == ("libertad", "es", "definition")

    # Spanish synonyms & antonyms
    assert extract_dictionary_term("sinónimos de efímero") == ("efímero", "es", "synonym")
    assert extract_dictionary_term("antónimos de efímero") == ("efímero", "es", "antonym")

    # English patterns
    assert extract_dictionary_term("what does resilience mean?") == ("resilience", "en", "definition")
    assert extract_dictionary_term("definition of entropy") == ("entropy", "en", "definition")
    assert extract_dictionary_term("define autonomy") == ("autonomy", "en", "definition")
    assert extract_dictionary_term("synonyms for ephemeral") == ("ephemeral", "en", "synonym")

    # Non-dictionary queries
    assert extract_dictionary_term("receta de arepas con queso") is None
    assert extract_dictionary_term("clima en medellin") is None
    assert extract_dictionary_term("historia de colombia") is None
    assert extract_dictionary_term("2 + 2") is None
    assert extract_dictionary_term("") is None


def test_parse_wiktionary_extract():
    sample_text = """
== Español ==

=== Etimología ===
Del griego antiguo ἐφήμερος (ephḗmeros, 'de un día').

==== Adjetivo ====
efímero ¦ plural: efímeros

1
Que dura un solo día.
Ejemplo: Insecto efímero.
2
Que dura poco tiempo.
Sinónimos: breve, fugaz, pasajero.
Ejemplo: La belleza es cosa efímera.
"""
    card = parse_wiktionary_extract("efímero", sample_text, lang="es", intent="synonym")
    assert card is not None
    assert card.word == "efímero"
    assert "Adjetivo" in card.part_of_speech
    assert "griego antiguo" in card.etymology
    assert len(card.senses) == 2
    assert card.senses[0].number == 1
    assert "dura un solo día" in card.senses[0].definition
    assert card.senses[0].example == "Insecto efímero."
    assert "breve" in card.all_synonyms
    assert "fugaz" in card.all_synonyms
    assert card.query_intent == "synonym"
    assert "es.wiktionary.org" in card.source_url


@pytest.mark.asyncio
async def test_dictionary_provider_mocked():
    provider = DictionaryProvider()
    fake_card = DictionaryCard(
        word="resiliencia",
        part_of_speech="Sustantivo femenino",
        etymology="Del latín resiliens.",
        senses=[
            DictionarySense(number=1, definition="Capacidad para resistir una crisis.", field="Psicología")
        ],
        all_synonyms=["entereza"],
        source_url="https://es.wiktionary.org/wiki/resiliencia",
        source_name="Wikcionario",
        lang="es",
    )

    with patch.object(provider, "get_definition", new=AsyncMock(return_value=fake_card)):
        res = await provider.get_definition("definición de resiliencia")
        assert res is not None
        assert res.word == "resiliencia"
        assert res.senses[0].field == "Psicología"


def test_api_dictionary_card_render(client):
    fake_card = DictionaryCard(
        word="resiliencia",
        part_of_speech="Sustantivo femenino",
        etymology="Del latín resiliens.",
        senses=[
            DictionarySense(number=1, definition="Capacidad para resistir una crisis y salir adelante.", field="Psicología", example="Gran muestra de resiliencia.")
        ],
        all_synonyms=["entereza"],
        source_url="https://es.wiktionary.org/wiki/resiliencia",
        source_name="Wikcionario",
        lang="es",
    )

    with patch("senda.dictionary.DictionaryProvider.get_definition", new=AsyncMock(return_value=fake_card)):
        resp = client.get("/search?q=definici%C3%B3n+de+resiliencia")
        assert resp.status_code == 200
        assert "dictionary-card" in resp.text
        assert "resiliencia" in resp.text
        assert "Sustantivo femenino" in resp.text
        assert "Capacidad para resistir una crisis" in resp.text
        assert "Psicología" in resp.text
        assert "Wikcionario" in resp.text
