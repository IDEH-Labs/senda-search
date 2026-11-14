# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit and integration tests for ethical health, space, and geographic knowledge cards."""

import pytest
from fastapi.testclient import TestClient

from senda.health import evaluate_health_query
from senda.space import evaluate_space_query
from senda.geo import evaluate_geo_query
from senda.api.app import create_app
from senda.indexer.storage import StorageEngine
from senda.providers.openalex import OpenAlexProvider


def test_evaluate_health_query():
    """Verify health query evaluation, verified sources, and typo tolerance."""
    # 1. Exact query
    h_dengue = evaluate_health_query("dengue")
    assert h_dengue is not None
    assert h_dengue.title == "Dengue"
    assert "OMS" in h_dengue.source
    assert len(h_dengue.symptoms) >= 3
    assert len(h_dengue.prevention) >= 3
    assert "Aviso ético" in h_dengue.disclaimer

    # 2. Typo tolerance: 'diabtes' -> 'Diabetes Mellitus'
    h_diab = evaluate_health_query("diabtes")
    assert h_diab is not None
    assert "Diabetes" in h_diab.title

    # 3. Non-health query returns None
    assert evaluate_health_query("computadora cuántica") is None


def test_evaluate_space_query():
    """Verify space and astronomical query evaluation and NASA facts."""
    # 1. Planet Mars
    s_marte = evaluate_space_query("marte")
    assert s_marte is not None
    assert s_marte.title == "Marte"
    assert "NASA" in s_marte.source
    assert "Gravedad superficial" in s_marte.key_facts
    assert s_marte.image_url is not None

    # 2. James Webb Space Telescope alias
    s_webb = evaluate_space_query("telescopio james webb")
    assert s_webb is not None
    assert "James Webb" in s_webb.title

    # 3. Non-space query returns None
    assert evaluate_space_query("receta de cocina") is None


def test_evaluate_geo_query():
    """Verify sovereign geographic OpenStreetMap evaluation."""
    # 1. Bogotá
    g_bog = evaluate_geo_query("bogota")
    assert g_bog is not None
    assert "Bogotá" in g_bog.city_name
    assert g_bog.country == "Colombia"
    assert "openstreetmap.org" in g_bog.osm_map_url
    assert "export/embed.html" in g_bog.osm_embed_url

    # 2. Madrid
    g_mad = evaluate_geo_query("madrid")
    assert g_mad is not None
    assert g_mad.city_name == "Madrid"
    assert g_mad.country == "España"

    # 3. Non-geo query returns None
    assert evaluate_geo_query("fotosíntesis") is None


def test_api_ethical_cards_rendering(tmp_path):
    """Verify that API delivers health, space, and geo cards in JSON and HTML."""
    storage = StorageEngine(db_path=tmp_path / "cards_test.db")
    app = create_app(
        storage=storage,
        openalex_provider=OpenAlexProvider(enabled=False),
        enable_federated_providers=False,
    )
    client = TestClient(app)

    # 1. Health Card in JSON & HTML
    resp_h = client.get("/search?q=dengue&format=json")
    assert resp_h.status_code == 200
    data_h = resp_h.json()
    assert data_h["health"] is not None
    assert data_h["health"]["title"] == "Dengue"

    resp_h_html = client.get("/search?q=dengue")
    assert resp_h_html.status_code == 200
    assert "health-card" in resp_h_html.text
    assert "Salud Pública Verificada" in resp_h_html.text
    assert "Síntomas comunes" in resp_h_html.text

    # 2. Space Card in JSON & HTML
    resp_s = client.get("/search?q=marte&format=json")
    assert resp_s.status_code == 200
    data_s = resp_s.json()
    assert data_s["space"] is not None
    assert data_s["space"]["title"] == "Marte"

    resp_s_html = client.get("/search?q=marte")
    assert resp_s_html.status_code == 200
    assert "space-card" in resp_s_html.text
    assert "Exploración Espacial" in resp_s_html.text

    # 3. Geo Card in JSON & HTML
    resp_g = client.get("/search?q=bogota&format=json")
    assert resp_g.status_code == 200
    data_g = resp_g.json()
    assert data_g["geo"] is not None
    assert "Bogotá" in data_g["geo"]["city_name"]

    resp_g_html = client.get("/search?q=bogota")
    assert resp_g_html.status_code == 200
    assert "geo-card" in resp_g_html.text
    assert "OpenStreetMap" in resp_g_html.text
