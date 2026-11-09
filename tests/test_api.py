# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Integration tests for Senda FastAPI web application and sovereign REST API."""

import pytest
from fastapi.testclient import TestClient
from senda.api.app import create_app
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine


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
    app = create_app(storage=storage)
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


def test_api_static_pages(client):
    r_about = client.get("/about")
    assert r_about.status_code == 200
    assert "About Senda" in r_about.text

    r_privacy = client.get("/privacy")
    assert r_privacy.status_code == 200
    assert "Verifiable Privacy Policy" in r_privacy.text

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
