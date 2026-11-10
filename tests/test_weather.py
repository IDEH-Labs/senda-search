# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from fastapi.testclient import TestClient

from senda.api.app import create_app
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine
from senda.providers.openalex import OpenAlexProvider
from senda.providers.weather import WeatherProvider, WeatherCard, DailyForecastItem


@pytest.fixture
def weather_provider():
    return WeatherProvider(ttl_seconds=60)


def test_detect_city_weather(weather_provider):
    # Explicit weather keywords
    assert weather_provider.detect_city("clima bogota") == ("bogota", True)
    assert weather_provider.detect_city("el clima en medellin") == ("medellin", True)
    assert weather_provider.detect_city("tiempo en buenos aires") == ("buenos aires", True)
    assert weather_provider.detect_city("temperatura cali") == ("cali", True)
    assert weather_provider.detect_city("weather in tokyo") == ("tokyo", True)
    assert weather_provider.detect_city("madrid weather") == ("madrid", True)

    # Bare city names
    assert weather_provider.detect_city("Bogotá") == ("Bogotá", False)
    assert weather_provider.detect_city("Madrid") == ("Madrid", False)

    # Non-city / general queries
    assert weather_provider.detect_city("receta de pastel de manzana") is None
    assert weather_provider.detect_city("site:wikipedia.org linux") is None
    assert weather_provider.detect_city("https://fsf.org") is None


@pytest.mark.asyncio
async def test_get_weather_mocked(weather_provider, monkeypatch):
    # Mock httpx client response
    fake_geo = {
        "results": [
            {
                "id": 1,
                "name": "Bogotá",
                "latitude": 4.6,
                "longitude": -74.08,
                "feature_code": "PPLC",
                "country": "Colombia",
                "admin1": "Bogotá D.C.",
                "population": 7000000,
            }
        ]
    }
    fake_weather = {
        "current": {
            "temperature_2m": 19.5,
            "apparent_temperature": 18.0,
            "relative_humidity_2m": 45,
            "wind_speed_10m": 12.0,
            "precipitation": 0.0,
            "weather_code": 0,
            "is_day": 1,
        },
        "daily": {
            "time": ["2026-11-10", "2026-11-11"],
            "weather_code": [0, 2],
            "temperature_2m_max": [21.0, 20.0],
            "temperature_2m_min": [9.0, 10.0],
        },
    }

    mock_client = AsyncMock()

    async def mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "geocoding-api" in url:
            resp.json.return_value = fake_geo
        else:
            resp.json.return_value = fake_weather
        return resp

    mock_client.get = mock_get
    monkeypatch.setattr(weather_provider, "_get_client", AsyncMock(return_value=mock_client))

    card = await weather_provider.get_weather("Bogotá")
    assert card is not None
    assert card.city_name == "Bogotá"
    assert card.country == "Colombia"
    assert card.temperature == 19.5
    assert card.weather_description == "Cielo despejado"
    assert card.weather_icon == "☀️"
    assert len(card.daily_forecast) == 2
    assert card.daily_forecast[0].day_name == "Hoy"


@pytest.fixture
def client_with_weather(tmp_path, monkeypatch):
    storage = StorageEngine(db_path=tmp_path / "weather_test.db")
    storage.upsert_document(
        ExtractedDocument(
            url="https://fsf.org/bogota",
            title="Bogotá Sovereign City",
            description="Capital of Colombia.",
            language="es",
            headings="Información",
            body_text="Ciudad de Bogotá en Colombia con información meteorológica abierta.",
            content_hash="hashbog1",
        )
    )

    fake_card = WeatherCard(
        city_name="Bogotá",
        country="Colombia",
        admin1="Bogotá D.C.",
        temperature=19.5,
        apparent_temperature=18.0,
        humidity=45,
        wind_speed=12.0,
        precipitation=0.0,
        weather_code=0,
        weather_description="Cielo despejado",
        weather_icon="☀️",
        is_day=True,
        daily_forecast=[
            DailyForecastItem(
                date="2026-11-10",
                day_name="Hoy",
                temp_max=21,
                temp_min=9,
                icon="☀️",
                description="Cielo despejado",
            )
        ],
        updated_at="12:00 UTC",
    )

    app = create_app(
        storage=storage,
        openalex_provider=OpenAlexProvider(enabled=False),
        enable_federated_providers=False,
    )

    return TestClient(app)


def test_weather_card_html_rendered(client_with_weather, monkeypatch):
    fake_card = WeatherCard(
        city_name="Bogotá",
        country="Colombia",
        admin1="Bogotá D.C.",
        temperature=19.5,
        apparent_temperature=18.0,
        humidity=45,
        wind_speed=12.0,
        precipitation=0.0,
        weather_code=0,
        weather_description="Cielo despejado",
        weather_icon="☀️",
        is_day=True,
        daily_forecast=[
            DailyForecastItem(
                date="2026-11-10",
                day_name="Hoy",
                temp_max=21,
                temp_min=9,
                icon="☀️",
                description="Cielo despejado",
            )
        ],
        updated_at="12:00 UTC",
    )

    # Monkeypatch get_weather
    async def mock_gw(self, q):
        return fake_card

    monkeypatch.setattr(WeatherProvider, "get_weather", mock_gw)

    resp = client_with_weather.get("/search?q=Bogot%C3%A1")
    assert resp.status_code == 200
    assert "Bogotá" in resp.text
    assert "Colombia" in resp.text
    assert "19.5" in resp.text
    assert "Cielo despejado" in resp.text
    assert "Sensación" in resp.text
    assert "Humedad" in resp.text
