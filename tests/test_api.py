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
    r_search_light = client.get("/search?q=freedom&category=images&theme=light")
    assert r_search_light.status_code == 200
    assert 'data-theme="light"' in r_search_light.text
    # Verify theme toggle button preserves search query and category in Zero-JS
    assert '/search?q=freedom&amp;category=images&amp;theme=dark' in r_search_light.text or '/search?q=freedom&category=images&theme=dark' in r_search_light.text

    # 5. Search results with dark theme
    r_search_dark = client.get("/search?q=freedom&category=images&theme=dark")
    assert r_search_dark.status_code == 200
    assert 'data-theme="dark"' in r_search_dark.text
    assert '/search?q=freedom&amp;category=images&amp;theme=light' in r_search_dark.text or '/search?q=freedom&category=images&theme=light' in r_search_dark.text


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
    """Verify /reader endpoint redirects directly to target URL without proxying."""
    resp_redirect = client.get("/reader?url=https://fsf.org/news", follow_redirects=False)
    assert resp_redirect.status_code == 302
    assert resp_redirect.headers["location"] == "https://fsf.org/news"

    resp_empty = client.get("/reader", follow_redirects=False)
    assert resp_empty.status_code == 302
    assert resp_empty.headers["location"] == "/"


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


def test_purpose_built_dropdown_options_per_category_and_mobile_css(client):
    """Verify each category tab renders strictly relevant tools to avoid saturation and cognitive clutter."""
    # 1. Web tab: Fecha, Región, SafeSearch, Lentes, Densidad (No 'Ordenar')
    resp_web = client.get("/search?q=freedom&category=all&time_filter=1d&goggle=tech_libre")
    assert resp_web.status_code == 200
    html_web = resp_web.text
    assert "Fecha: 24 horas" in html_web
    assert "Región:" in html_web
    assert "SafeSearch:" in html_web
    assert "Lente: Software Libre" in html_web
    assert "densityBtn" in html_web
    assert "Ordenar:" not in html_web

    # 2. News tab: Fecha, Ordenar, Región, Densidad (No 'Lente', No 'SafeSearch')
    resp_news = client.get("/search?q=freedom&category=news&time_filter=1d&sort=date")
    assert resp_news.status_code == 200
    html_news = resp_news.text
    assert "Fecha: 24 horas" in html_news
    assert "Ordenar: Recientes" in html_news
    assert "Región:" in html_news
    assert "densityBtn" in html_news
    assert "Lente:" not in html_news and "Lentes:" not in html_news
    assert "SafeSearch:" not in html_news

    # 3. Images tab: Región, SafeSearch (Clean visual mode: No Fecha, No Ordenar, No Lente, No Densidad)
    resp_img = client.get("/search?q=freedom&category=images")
    assert resp_img.status_code == 200
    html_img = resp_img.text
    assert "Región:" in html_img
    assert "SafeSearch:" in html_img
    assert "Fecha:" not in html_img
    assert "Ordenar:" not in html_img
    assert "Lente:" not in html_img and "Lentes:" not in html_img
    assert "densityBtn" not in html_img

    # 4. Videos tab: Fecha, Región, SafeSearch (No Ordenar, No Lente, No Densidad)
    resp_vid = client.get("/search?q=freedom&category=videos&time_filter=1w")
    assert resp_vid.status_code == 200
    html_vid = resp_vid.text
    assert "Fecha: 1 semana" in html_vid
    assert "Región:" in html_vid
    assert "SafeSearch:" in html_vid
    assert "Ordenar:" not in html_vid
    assert "Lente:" not in html_vid and "Lentes:" not in html_vid
    assert "densityBtn" not in html_vid

    # 5. Library tab: Fecha, Densidad (Peer-reviewed science: No SafeSearch, No Lente, No Región, No Ordenar)
    resp_lib = client.get("/search?q=freedom&category=library&time_filter=1m")
    assert resp_lib.status_code == 200
    html_lib = resp_lib.text
    assert "Fecha: 1 mes" in html_lib
    assert "densityBtn" in html_lib
    assert "Región:" not in html_lib
    assert "SafeSearch:" not in html_lib
    assert "Lente:" not in html_lib and "Lentes:" not in html_lib
    assert "Ordenar:" not in html_lib

    # 6. Community tab: Fecha, Lentes, Densidad (IndieWeb/SmallWeb: No Región, No SafeSearch, No Ordenar)
    resp_comm = client.get("/search?q=freedom&category=community&time_filter=1d&goggle=tech_libre")
    assert resp_comm.status_code == 200
    html_comm = resp_comm.text
    assert "Fecha: 24 horas" in html_comm
    assert "Lente: Software Libre" in html_comm
    assert "densityBtn" in html_comm
    assert "Región:" not in html_comm
    assert "SafeSearch:" not in html_comm
    assert "Ordenar:" not in html_comm

    # Verify CSS static file has mobile overflow fix for tools bar
    resp_css = client.get("/static/css/senda.css")
    assert resp_css.status_code == 200
    css = resp_css.text
    assert ".filter-dropdown[open]" in css
    assert "overflow: visible" in css
    assert ".dropdown-btn-icon" in css


def test_multilingual_backend_resolution_and_rendering(client):
    """Verify ethical, full Zero-JS server-side multilingual translation and Accept-Language negotiation."""
    # Ensure client starts with clean cookie jar
    if "senda_lang" in client.cookies:
        del client.cookies["senda_lang"]

    # 1. French language via Accept-Language header (no cookies set)
    resp_fr = client.get(
        "/search?q=liberte&category=all&time_filter=1d",
        headers={"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"}
    )
    assert resp_fr.status_code == 200
    html_fr = resp_fr.text
    assert '<html lang="fr"' in html_fr
    assert "Date: 24 heures" in html_fr
    assert "Dernières 24 heures" in html_fr
    assert "Région: Mondial" in html_fr
    assert "Densité : Confortable" in html_fr

    # 2. English language via explicit ?lang=en (sets senda_lang cookie)
    resp_en = client.get("/search?q=freedom&category=all&time_filter=1d&lang=en")
    assert resp_en.status_code == 200
    html_en = resp_en.text
    assert '<html lang="en"' in html_en
    assert "Date: 24 hours" in html_en
    assert "Any time" in html_en
    assert "Region: Global" in html_en
    assert "SafeSearch: Off" in html_en
    assert "Density: Comfortable" in html_en

    # 3. German language via cookie senda_lang=de
    client.cookies.set("senda_lang", "de")
    resp_de = client.get("/search?q=freiheit&category=all&time_filter=1d")
    assert resp_de.status_code == 200
    html_de = resp_de.text
    assert '<html lang="de"' in html_de
    assert "Datum: 24 Stunden" in html_de
    assert "Beliebige Zeit" in html_de
    assert "Dichte: Komfortabel" in html_de
    # Clean up cookie
    del client.cookies["senda_lang"]

    # 4. News tab in English has Sort: Recent
    resp_news_en = client.get("/search?q=open+source&category=news&sort=date&lang=en")
    assert resp_news_en.status_code == 200
    assert "Sort: Recent" in resp_news_en.text
    assert "Most recent" in resp_news_en.text


def test_news_sort_dropdown_no_duplication(client):
    """Verify the news tab sort dropdown renders exactly once without duplicate tags or orphan menus."""
    resp = client.get("/search?q=tecnologia&category=news&theme=dark")
    assert resp.status_code == 200
    html = resp.text
    # Exactly 2 dropdown menus in news toolbar: Period (date) and Sort (ordenar)
    assert html.count('class="filter-dropdown-menu"') == 2
    # Verify the sort dropdown options appear exactly once
    assert html.count("Ordenar:") == 1
    assert html.count("sort=relevance") == 1


def test_typo_correction_and_did_you_mean(tmp_path):
    """Verify sovereign typo tolerance, suggestions, and auto-fallback when zero results are found."""
    storage = StorageEngine(db_path=tmp_path / "typo_test.db")
    storage.upsert_document(
        ExtractedDocument(
            url="https://es.wikipedia.org/wiki/Catedral_de_Notre_Dame",
            title="Catedral de Notre Dame",
            description="La catedral de Notre Dame es una iglesia de culto católico en París.",
            language="es",
            headings="Historia y Arquitectura",
            body_text="Notre Dame es uno de los monumentos más populares de la capital francesa.",
            content_hash="notredame123",
        )
    )
    app = create_app(
        storage=storage,
        openalex_provider=OpenAlexProvider(enabled=False),
        enable_federated_providers=False,
    )
    test_client = TestClient(app)

    # 1. Zero initial results for 'notredam' -> automatic fallback to 'Notre Dame'
    resp = test_client.get("/search?q=notredam&format=json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "notredam"
    assert data["auto_corrected"] is True
    assert data["corrected_query"] == "Notre Dame"
    assert data["original_query"] == "notredam"
    assert len(data["items"]) >= 1

    # HTML rendering of auto-corrected banner
    resp_html = test_client.get("/search?q=notredam")
    assert resp_html.status_code == 200
    assert "search-correction-banner auto-corrected" in resp_html.text
    assert "Mostrando resultados para" in resp_html.text
    assert "Buscar en su lugar" in resp_html.text
    assert "Notre Dame" in resp_html.text

    # 2. Literal search bypasses auto-correction
    resp_literal = test_client.get("/search?q=notredam&literal=1&format=json")
    assert resp_literal.status_code == 200
    data_lit = resp_literal.json()
    assert data_lit["auto_corrected"] is False
    assert data_lit["did_you_mean"] is None
    assert len(data_lit["items"]) == 0

    # 3. Did-you-mean suggestion when query has partial matches
    # 'notre dam' matches 'notre' but triggers did_you_mean to 'Notre Dame'
    resp_dam = test_client.get("/search?q=notre+dam&format=json")
    assert resp_dam.status_code == 200
    data_dam = resp_dam.json()
    assert data_dam["did_you_mean"] == "Notre Dame"


def test_navigational_direct_site_resolution(client):
    """Verify sovereign navigational intent resolution for domain queries and brand queries."""
    # 1. Direct domain query 'google.com'
    resp_google = client.get("/search?q=google.com&format=json")
    assert resp_google.status_code == 200
    data_g = resp_google.json()
    assert len(data_g["items"]) >= 1
    top_g = data_g["items"][0]
    assert top_g["url"] == "https://www.google.com/"
    assert "Google" in top_g["title"]
    assert top_g["source"] == "Navegación Directa"

    # HTML check for 'google.com'
    resp_g_html = client.get("/search?q=google.com")
    assert resp_g_html.status_code == 200
    assert "https://www.google.com/" in resp_g_html.text
    assert "badge-navigational" in resp_g_html.text
    assert "Sitio Oficial" in resp_g_html.text

    # 2. Brand query without TLD 'xvideos'
    resp_xv = client.get("/search?q=xvideos&format=json")
    assert resp_xv.status_code == 200
    data_xv = resp_xv.json()
    assert len(data_xv["items"]) >= 1
    top_xv = data_xv["items"][0]
    assert top_xv["url"] == "https://www.xvideos.com/"
    assert "XVideos" in top_xv["title"]
    assert top_xv["source"] == "Navegación Directa"

    # 3. Arbitrary domain query 'archlinux.org'
    resp_arch = client.get("/search?q=archlinux.org&format=json")
    assert resp_arch.status_code == 200
    data_arch = resp_arch.json()
    assert len(data_arch["items"]) >= 1
    top_arch = data_arch["items"][0]
    assert "archlinux.org" in top_arch["url"]
    assert top_arch["source"] == "Navegación Directa"


def test_zero_js_language_and_footer_theme_persistence(client):
    """Verify robust Tor Browser Safest / Zero-JS navigation state continuity."""
    # 1. Search page with light theme and French language
    resp = client.get("/search?q=linux&lang=fr&theme=light")
    assert resp.status_code == 200
    html = resp.text

    # Zero-JS Language form and noscript button
    assert 'class="lang-form"' in html
    assert 'class="lang-submit-noscript"' in html
    assert '<noscript>' in html
    assert 'name="q" value="linux"' in html
    assert 'name="theme" value="light"' in html

    # Footer links preserve both theme and lang
    assert '/about?theme=light&amp;lang=fr' in html or '/about?theme=light&lang=fr' in html
    assert '/privacy?theme=light&amp;lang=fr' in html or '/privacy?theme=light&lang=fr' in html
    assert '/javascript?theme=light&amp;lang=fr' in html or '/javascript?theme=light&lang=fr' in html

    # Mobile theme-color in light mode
    assert 'content="#ffffff"' in html

    # Clear button hidden without JS
    assert 'id="clearSearchBtn" class="command-bar-clear" aria-label="Limpiar" style="display: none;"' in html

    # 2. Homepage preserves lang in search form
    resp_home = client.get("/?lang=en&theme=light")
    assert resp_home.status_code == 200
    html_home = resp_home.text
    assert '<input type="hidden" name="lang" value="en">' in html_home
    assert '<input type="hidden" name="theme" id="search-theme" value="light">' in html_home




