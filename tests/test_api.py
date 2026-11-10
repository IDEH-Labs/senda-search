# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Integration tests for Senda FastAPI web application and sovereign REST API."""

import pytest
from fastapi.testclient import TestClient
from senda.api.app import create_app
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine
from senda.providers.openalex import OpenAlexProvider


@pytest.fixture
def client(tmp_path):
    storage = StorageEngine(db_path=tmp_path / "api_test.db")
    storage.upsert_document(
        ExtractedDocument(
            url="https://fsf.org/news",
            title="Free Software Foundation Updates",
            description="Defending digital freedom.",
            language="en",
            headings="Announcements",
            body_text="Recent news on digital sovereignty, licensing, and ethical code.",
            content_hash="hash99",
        )
    )
    app = create_app(
        storage=storage,
        openalex_provider=OpenAlexProvider(enabled=False),
        enable_federated_providers=False,
    )
    return TestClient(app)


def test_api_security_headers_and_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Senda" in response.text
    # Verify strict sovereign privacy headers
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    # Verify 8 sovereign language options with native endonyms
    for lang_code in ["en", "es", "fr", "de", "pt", "it", "ja", "zh"]:
        assert f'value="{lang_code}"' in response.text
    assert ">日本語</option>" in response.text
    assert ">中文</option>" in response.text
    assert "lang-picker" in response.text


def test_api_static_pages(client):
    r_about = client.get("/about")
    assert r_about.status_code == 200
    assert "About Senda" in r_about.text

    r_privacy = client.get("/privacy")
    assert r_privacy.status_code == 200
    assert "Verifiable Privacy Policy" in r_privacy.text

    r_js = client.get("/javascript")
    assert r_js.status_code == 200
    assert "jslicense-labels1" in r_js.text
    assert "GNU LibreJS" in r_js.text

    r_opensearch = client.get("/opensearch.xml")
    assert r_opensearch.status_code == 200
    assert "application/opensearchdescription+xml" in r_opensearch.headers["content-type"]
    assert "<OpenSearchDescription" in r_opensearch.text
    assert "Senda" in r_opensearch.text


def test_api_html_search(client):
    response = client.get("/search?q=Foundation")
    assert response.status_code == 200
    assert "Free Software Foundation Updates" in response.text


def test_api_post_search_privacy(client):
    """POST /search protects user privacy by avoiding query persistence in browser history."""
    # HTML response via form POST
    response = client.post(
        "/search",
        data={"q": "Foundation", "p": "1"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "Free Software Foundation Updates" in response.text

    # JSON content negotiation via POST
    response_json = client.post(
        "/search?format=json",
        data={"q": "sovereignty", "category": "all"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response_json.status_code == 200
    data = response_json.json()
    assert data["total_matches"] == 1
    assert data["items"][0]["url"] == "https://fsf.org/news"


def test_api_category_verticals(client):
    # Category web
    r_web = client.get("/search?q=Foundation&category=web")
    assert r_web.status_code == 200
    assert "Free Software Foundation Updates" in r_web.text

    # Category images (empty in this fixture, but renders image layout)
    r_img = client.get("/search?q=Foundation&category=images")
    assert r_img.status_code == 200

    # REST API category
    r_api = client.get("/api/v1/search?q=Foundation&category=web")
    assert r_api.status_code == 200
    assert r_api.json()["category"] == "web"


def test_api_content_negotiation_json(client):
    # Format parameter
    r1 = client.get("/search?q=Foundation&format=json")
    assert r1.status_code == 200
    data = r1.json()
    assert data["total_matches"] == 1
    assert data["items"][0]["url"] == "https://fsf.org/news"

    # Accept header
    r2 = client.get("/search?q=Foundation", headers={"Accept": "application/json"})
    assert r2.status_code == 200
    assert r2.json()["total_matches"] == 1


def test_api_rest_search_and_health(client):
    r_health = client.get("/api/v1/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    r_stats = client.get("/api/v1/stats")
    assert r_stats.status_code == 200
    assert r_stats.json()["total_documents"] == 1

    r_search = client.get("/api/v1/search?q=sovereignty")
    assert r_search.status_code == 200
    res = r_search.json()
    assert res["total_matches"] == 1
    assert res["items"][0]["title"] == "Free Software Foundation Updates"


def test_api_takedown(client):
    # Verify document exists
    r_stats_before = client.get("/api/v1/stats").json()
    assert r_stats_before["total_documents"] == 1

    # Execute domain takedown
    takedown_res = client.post(
        "/api/v1/takedown",
        json={"domain": "fsf.org", "reason": "Site owner request"}
    )
    assert takedown_res.status_code == 200
    assert takedown_res.json()["purged_records"] == 1

    # Verify document is gone
    r_stats_after = client.get("/api/v1/stats").json()
    assert r_stats_after["total_documents"] == 0


def test_api_brand_assets_and_manifest(client):
    """Verify webmanifest and static brand assets are served properly."""
    r_manifest = client.get("/manifest.webmanifest")
    assert r_manifest.status_code == 200
    data = r_manifest.json()
    assert data["name"] == "Senda"
    assert len(data["icons"]) >= 3

    r_favicon = client.get("/static/img/favicon.svg")
    assert r_favicon.status_code == 200
    assert "svg" in r_favicon.headers.get("content-type", "")

    r_og = client.get("/static/img/senda-og.png")
    assert r_og.status_code == 200
    assert r_og.headers.get("content-type") == "image/png"


def test_theme_toggle_zero_js_and_cookie(client):
    """Verify theme switching works via query parameter and functional cookie (Tor/LibreJS compatible)."""
    # 1. Default should be dark
    r_default = client.get("/")
    assert r_default.status_code == 200
    assert 'data-theme="dark"' in r_default.text
    assert '?theme=light' in r_default.text

    # 2. Switch to light via query param (Zero JS)
    r_light = client.get("/?theme=light")
    assert r_light.status_code == 200
    assert 'data-theme="light"' in r_light.text
    assert '?theme=dark' in r_light.text
    # Check functional cookie is set
    assert "senda_theme=light" in r_light.headers.get("set-cookie", "")

    # 3. Subsequent request with cookie keeps light mode
    r_cookie = client.get("/", cookies={"senda_theme": "light"})
    assert r_cookie.status_code == 200
    assert 'data-theme="light"' in r_cookie.text

    # 4. Search results with light theme
    r_search_light = client.get("/search?q=freedom&theme=light")
    assert r_search_light.status_code == 200
    assert 'data-theme="light"' in r_search_light.text


def test_api_head_requests(client):
    """Verify RFC 9110 HTTP HEAD support for all public routes and zero body."""
    # Test HEAD on homepage
    r_home = client.head("/")
    assert r_home.status_code == 200
    assert r_home.text == ""
    assert "text/html" in r_home.headers.get("content-type", "")
    assert r_home.headers["X-Frame-Options"] == "DENY"

    # Test HEAD on health endpoint
    r_health = client.head("/health")
    assert r_health.status_code == 200
    assert r_health.text == ""

    # Test HEAD on search
    r_search = client.head("/search?q=Foundation")
    assert r_search.status_code == 200
    assert r_search.text == ""


def test_api_health_endpoints(client):
    """Verify both /health and /api/v1/health endpoints work consistently."""
    r_top = client.get("/health")
    assert r_top.status_code == 200
    data_top = r_top.json()
    assert data_top["status"] == "healthy"
    assert data_top["app"] == "Senda"

    r_v1 = client.get("/api/v1/health")
    assert r_v1.status_code == 200
    data_v1 = r_v1.json()
    assert data_v1["status"] == "healthy"
    assert data_v1["app"] == "Senda"


def test_onion_location_header(client, monkeypatch):
    """Verify Onion-Location header is correctly advertised to Tor Browser when configured."""
    monkeypatch.setattr("senda.config.settings.ONION_HOST", "http://sendatest1234567890abcdef.onion")
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("Onion-Location") == "http://sendatest1234567890abcdef.onion/"

    resp_search = client.get("/search?q=freedom")
    assert resp_search.status_code == 200
    assert resp_search.headers.get("Onion-Location") == "http://sendatest1234567890abcdef.onion/search?q=freedom"


def test_provenance_panel_renders_zero_js(client):
    """Verify the Verifiable Provenance Panel renders semantic zero-JS disclosure and no-referrer links."""
    resp = client.get("/search?q=Foundation")
    assert resp.status_code == 200
    html = resp.text

    # Native zero-JS HTML5 details element
    assert '<details class="why-seen-disclosure">' in html
    assert '<summary class="why-seen-summary"' in html
    assert "provenance-panel" in html
    assert "Tipo de Fuente:" in html
    assert "Estado de Retractación:" in html
    assert "Procedencia de IA:" in html
    assert "Cero Rastreo &bull; no-referrer" in html

    # Privacy checks on outgoing links
    assert 'referrerpolicy="no-referrer"' in html
    assert 'rel="noopener noreferrer"' in html


def test_provenance_json_negotiation(client):
    """Verify JSON content negotiation serves verifiable provenance fields."""
    resp = client.get("/search?q=Foundation&format=json")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert "canonical_url" in item
    assert "source_type" in item
    assert "content_type" in item
    assert "retraction" in item
    assert "primary_citations" in item
    assert "verifications" in item
    assert "ai_provenance" in item


def test_conversion_and_world_time_cards(client):
    """Verify that instant conversion and world time cards render properly in HTML and JSON."""
    # 1. Conversion query in HTML and JSON
    resp_conv = client.get("/search?q=10+km+a+metros")
    assert resp_conv.status_code == 200
    assert "conversion-card" in resp_conv.text
    assert "10,000 m" in resp_conv.text or "10000" in resp_conv.text

    resp_conv_json = client.get("/search?q=10+km+a+metros&format=json")
    assert resp_conv_json.status_code == 200
    conv_data = resp_conv_json.json()
    assert conv_data.get("conversion") is not None
    assert conv_data["conversion"]["category"] == "length"

    # 2. World time query in HTML and JSON
    resp_time = client.get("/search?q=hora+en+Tokio")
    assert resp_time.status_code == 200
    assert "worldtime-card" in resp_time.text
    assert "Tokio" in resp_time.text

    resp_time_json = client.get("/search?q=hora+en+Tokio&format=json")
    assert resp_time_json.status_code == 200
    time_data = resp_time_json.json()
    assert time_data.get("world_time") is not None
    assert "Asia/Tokyo" in time_data["world_time"]["timezone_name"]


def test_reader_endpoint(client):
    """Verify /reader endpoint handles missing URL, errors, and rendering."""
    # Missing URL
    resp_empty = client.get("/reader")
    assert resp_empty.status_code == 200
    assert "No se proporcionó ninguna URL" in resp_empty.text

    # SSRF blocked URL
    resp_ssrf = client.get("/reader?url=http://127.0.0.1:8000/secret")
    assert resp_ssrf.status_code == 200
    assert "bloqueado por seguridad" in resp_ssrf.text or "protección anti-SSRF" in resp_ssrf.text


def test_opensearch_integration(client):
    """Verify OpenSearch XML and footer 1-click details element."""
    resp_xml = client.get("/opensearch.xml")
    assert resp_xml.status_code == 200
    assert "OpenSearchDescription" in resp_xml.text
    assert "application/opensearchdescription+xml" in resp_xml.headers["Content-Type"]

    resp_home = client.get("/")
    assert resp_home.status_code == 200
    assert "opensearch-details" in resp_home.text
    assert "Añadir a mi navegador" in resp_home.text


def test_goggles_and_smallweb_integration(client):
    """Verify Sovereign Goggles, Comunidad & Foros tab, and custom DSL in API and HTML."""
    # 1. HTML search with Goggle
    resp_goggle = client.get("/search?q=Foundation&goggle=tech_libre")
    assert resp_goggle.status_code == 200
    assert "Lente: Software Libre" in resp_goggle.text
    assert "Comunidad & Foros" in resp_goggle.text
    assert "100% Orgánico" in resp_goggle.text

    # 2. JSON search with Goggle catalog
    resp_json = client.get("/search?q=Foundation&goggle=tech_libre&format=json")
    assert resp_json.status_code == 200
    data = resp_json.json()
    assert data["goggle"] == "tech_libre"
    assert any(g["id"] == "tech_libre" for g in data["goggles_catalog"])

    # 3. Community vertical category (Comunidad & Foros)
    resp_community = client.get("/search?q=Foundation&category=community")
    assert resp_community.status_code == 200
    assert "Comunidad & Foros" in resp_community.text

    # 4. Custom DSL Goggle test
    resp_custom = client.get("/search?q=Foundation&custom_goggle=%24discard%2Csite%3Dquora.com")
    assert resp_custom.status_code == 200
    assert "Lente: DSL Personalizada" in resp_custom.text

