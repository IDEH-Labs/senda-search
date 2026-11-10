# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import pytest
from fastapi.testclient import TestClient

from senda.api.app import create_app
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine
from senda.providers.openalex import OpenAlexProvider
from senda.calculator import evaluate_math_query, format_number


@pytest.fixture
def client(tmp_path):
    storage = StorageEngine(db_path=tmp_path / "calc_test.db")
    storage.upsert_document(
        ExtractedDocument(
            url="https://fsf.org/calc",
            title="Sovereign Mathematics",
            description="Pure deterministic arithmetic.",
            language="es",
            headings="Calculadora",
            body_text="Guía de cálculo soberano sin JavaScript ni telemetría.",
            content_hash="hashcalc1",
        )
    )
    app = create_app(
        storage=storage,
        openalex_provider=OpenAlexProvider(enabled=False),
        enable_federated_providers=False,
    )
    return TestClient(app)


def test_basic_arithmetic():
    assert evaluate_math_query("2 + 2").formatted_result == "4"
    assert evaluate_math_query("100 - 35").formatted_result == "65"
    assert evaluate_math_query("15 * 8").formatted_result == "120"
    assert evaluate_math_query("15 x 8").formatted_result == "120"
    assert evaluate_math_query("15 × 8").formatted_result == "120"
    assert evaluate_math_query("15 · 8").formatted_result == "120"
    assert evaluate_math_query("100 / 4").formatted_result == "25"
    assert evaluate_math_query("100 ÷ 4").formatted_result == "25"
    assert evaluate_math_query("10 // 3").formatted_result == "3"
    assert evaluate_math_query("10 % 3").formatted_result == "1"
    assert evaluate_math_query("2^10").formatted_result == "1,024"
    assert evaluate_math_query("2**10").formatted_result == "1,024"


def test_percentages():
    # X% de Y / X% of Y
    assert evaluate_math_query("15% de 200").formatted_result == "30"
    assert evaluate_math_query("25 % de 80").formatted_result == "20"
    assert evaluate_math_query("50% of 100").formatted_result == "50"
    # Base + X% / Base - X%
    assert evaluate_math_query("200 + 10%").formatted_result == "220"
    assert evaluate_math_query("100 - 15%").formatted_result == "85"


def test_natural_language_prefixes():
    assert evaluate_math_query("cuanto es 25 + 75?").formatted_result == "100"
    assert evaluate_math_query("cuánto es 50 * 2").formatted_result == "100"
    assert evaluate_math_query("calcular 12 * 12 =").formatted_result == "144"
    assert evaluate_math_query("calcula 100 / 5").formatted_result == "20"
    assert evaluate_math_query("what is 7 * 8?").formatted_result == "56"
    assert evaluate_math_query("resolver 2 + 3 * 4").formatted_result == "14"


def test_functions_and_constants():
    assert evaluate_math_query("sqrt(144)").formatted_result == "12"
    assert evaluate_math_query("raiz(81)").formatted_result == "9"
    assert evaluate_math_query("raíz(49)").formatted_result == "7"
    assert evaluate_math_query("abs(-42)").formatted_result == "42"
    assert evaluate_math_query("round(3.7)").formatted_result == "4"
    assert evaluate_math_query("pi * 2").raw_result > 6.28


def test_division_by_zero():
    res = evaluate_math_query("100 / 0")
    assert res is not None
    assert res.is_error is True
    assert "división por cero" in res.formatted_result.lower()


def test_non_math_queries_return_none():
    assert evaluate_math_query("historia de colombia") is None
    assert evaluate_math_query("python 3.12 release notes") is None
    assert evaluate_math_query("quien descubrio america") is None
    assert evaluate_math_query("1984") is None  # Bare number without operator should not trigger calculator
    assert evaluate_math_query("") is None
    assert evaluate_math_query("import os; os.system('ls')") is None


def test_api_integration_calculator(client):
    response = client.get("/search?q=15+x+8")
    assert response.status_code == 200
    assert "Calculadora" in response.text
    assert "120" in response.text

    # JSON content negotiation
    json_resp = client.get("/search?q=15+x+8", headers={"accept": "application/json"})
    assert json_resp.status_code == 200
    data = json_resp.json()
    assert data["calculator"] is not None
    assert data["calculator"]["formatted_result"] == "120"
