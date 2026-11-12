# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Tests for Etapa 2 Remediation:
- Strict CSP with dynamic cryptographic nonces on inline scripts
- Complete removal of inline event handlers (onclick, etc.) across static pages, search results, and disk templates
- Strict object-src 'none', base-uri 'self', form-action 'self', frame-ancestors 'none'
- Documented functional preference cookies (senda_theme, senda_lang) with proper flags
  (SameSite=Lax, Secure over HTTPS and behind reverse proxies with X-Forwarded-Proto, Path=/, Max-Age=31536000)
  and zero tracking identifiers.
"""

import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from senda.api.app import create_app
from senda.extractor.parser import ExtractedDocument, ExtractedImage
from senda.indexer.storage import StorageEngine


@pytest.fixture
def client(tmp_path):
    storage = StorageEngine(db_path=tmp_path / "etapa2_test.db")
    # Seed storage with rich results for all categories
    doc = ExtractedDocument(
        url="https://example.org/article",
        title="Software Freedom Article",
        description="Comprehensive article about sovereign software.",
        language="en",
        headings="Principles and Architecture",
        body_text="Ethical technology ensures user autonomy and strict digital sovereignty.",
        content_hash="etapa2hash1",
        images=[
            ExtractedImage(
                image_url="https://example.org/thumb.jpg",
                alt_text="Visual diagram of software freedom",
                page_url="https://example.org/article",
                page_title="Software Freedom Article",
                domain="example.org",
            )
        ],
    )
    storage.upsert_document(doc)
    app = create_app(storage=storage, enable_federated_providers=False)
    return TestClient(app)


def test_csp_complete_security_directives(client):
    """CSP must enforce complete defense-in-depth directives."""
    resp = client.get("/")
    assert resp.status_code == 200
    csp = resp.headers.get("Content-Security-Policy", "")

    # Directives verification
    assert "default-src 'self';" in csp
    assert "object-src 'none';" in csp
    assert "base-uri 'self';" in csp
    assert "form-action 'self';" in csp
    assert "frame-ancestors 'none';" in csp
    assert "img-src 'self' data:;" in csp
    assert "style-src 'self' 'unsafe-inline';" in csp
    assert "script-src 'self' 'nonce-" in csp


def test_csp_dynamic_cryptographic_nonce(client):
    """Each request must generate a unique cryptographically random 16-byte hex nonce."""
    resp1 = client.get("/")
    csp1 = resp1.headers.get("Content-Security-Policy", "")
    match1 = re.search(r"script-src 'self' 'nonce-([a-f0-9]{32})'", csp1)
    assert match1 is not None, f"Nonce regex failed on CSP: {csp1}"
    nonce1 = match1.group(1)

    resp2 = client.get("/")
    csp2 = resp2.headers.get("Content-Security-Policy", "")
    match2 = re.search(r"script-src 'self' 'nonce-([a-f0-9]{32})'", csp2)
    assert match2 is not None, f"Nonce regex failed on CSP: {csp2}"
    nonce2 = match2.group(1)

    # Nonces must be unique per request (never static or recycled)
    assert nonce1 != nonce2


def test_csp_nonce_rendered_in_html_script_tags(client):
    """Inline script tags in rendered HTML must carry the dynamic nonce from CSP."""
    resp = client.get("/")
    assert resp.status_code == 200
    csp = resp.headers.get("Content-Security-Policy", "")
    match = re.search(r"'nonce-([a-f0-9]{32})'", csp)
    assert match is not None
    nonce = match.group(1)

    # HTML must include the nonce attribute matching the header
    assert f'<script nonce="{nonce}">' in resp.text


def test_zero_inline_event_handlers_in_rendered_html_and_results(client):
    """Rendered HTML pages and search results must not contain inline event handlers like onclick, onload, etc."""
    pages_to_check = [
        "/",
        "/about",
        "/privacy",
        "/javascript",
        "/search?q=software",
        "/search?q=software&category=images",
        "/search?q=software&category=videos",
        "/search?q=software&category=news",
        "/search?q=software&category=library",
    ]
    for path in pages_to_check:
        resp = client.get(path)
        assert resp.status_code == 200
        # Check for inline event handlers (e.g. onclick="...", onload="...", etc.)
        inline_handlers = re.findall(r"\s(on[a-z]{3,15})\s*=", resp.text, re.IGNORECASE)
        assert inline_handlers == [], f"Found inline event handler(s) {inline_handlers} in rendered {path}"


def test_zero_inline_event_handlers_in_template_files():
    """All Jinja2 HTML template source files on disk must be free of inline event handlers and javascript: URLs."""
    template_dir = Path(__file__).resolve().parent.parent / "src" / "senda" / "ui" / "templates"
    assert template_dir.exists() and template_dir.is_dir()

    template_files = list(template_dir.glob("*.html"))
    assert len(template_files) > 0

    for tf in template_files:
        content = tf.read_text(encoding="utf-8")
        handlers = re.findall(r"\s(on[a-zA-Z]{3,15})\s*=", content)
        assert handlers == [], f"Found static inline handler(s) {handlers} in template file {tf.name}"
        assert "javascript:" not in content.lower(), f"Found 'javascript:' URI in template file {tf.name}"


def test_functional_cookies_attributes_http(client):
    """Setting theme and lang query parameters produces functional cookies with proper attributes on HTTP."""
    resp = client.get("/?theme=dark&lang=es")
    assert resp.status_code == 200

    set_cookies = resp.headers.get_list("set-cookie")
    assert len(set_cookies) >= 2

    # Verify senda_theme
    theme_cookie = next(c for c in set_cookies if c.startswith("senda_theme="))
    assert "senda_theme=dark" in theme_cookie
    assert "Max-Age=31536000" in theme_cookie
    assert "Path=/" in theme_cookie
    assert "SameSite=lax" in theme_cookie
    # Not secure on plain http testclient
    assert "Secure" not in theme_cookie

    # Verify senda_lang
    lang_cookie = next(c for c in set_cookies if c.startswith("senda_lang="))
    assert "senda_lang=es" in lang_cookie
    assert "Max-Age=31536000" in lang_cookie
    assert "Path=/" in lang_cookie
    assert "SameSite=lax" in lang_cookie
    assert "Secure" not in lang_cookie


def test_functional_cookies_attributes_https(tmp_path):
    """Setting functional cookies over direct HTTPS must include the Secure flag."""
    storage = StorageEngine(db_path=tmp_path / "https_cookie.db")
    app = create_app(storage=storage, enable_federated_providers=False)
    client_https = TestClient(app, base_url="https://senda.example.org")

    resp = client_https.get("/?theme=light&lang=en")
    assert resp.status_code == 200

    set_cookies = resp.headers.get_list("set-cookie")
    theme_cookie = next(c for c in set_cookies if c.startswith("senda_theme="))
    assert "senda_theme=light" in theme_cookie
    assert "Secure" in theme_cookie

    lang_cookie = next(c for c in set_cookies if c.startswith("senda_lang="))
    assert "senda_lang=en" in lang_cookie
    assert "Secure" in lang_cookie


def test_functional_cookies_secure_behind_reverse_proxy(client):
    """When running behind a reverse proxy (Nginx/Caddy/Traefik) terminating TLS, X-Forwarded-Proto enables Secure."""
    # 1. Reverse proxy with X-Forwarded-Proto: https
    resp_xfp = client.get("/?theme=dark&lang=es", headers={"X-Forwarded-Proto": "https"})
    assert resp_xfp.status_code == 200
    cookies_xfp = resp_xfp.headers.get_list("set-cookie")
    theme_cookie_xfp = next(c for c in cookies_xfp if c.startswith("senda_theme="))
    assert "Secure" in theme_cookie_xfp
    lang_cookie_xfp = next(c for c in cookies_xfp if c.startswith("senda_lang="))
    assert "Secure" in lang_cookie_xfp

    # 2. Reverse proxy with standard RFC 7239 Forwarded: proto=https
    resp_fwd = client.get("/?theme=dark&lang=es", headers={"Forwarded": "proto=https;for=203.0.113.1"})
    assert resp_fwd.status_code == 200
    cookies_fwd = resp_fwd.headers.get_list("set-cookie")
    theme_cookie_fwd = next(c for c in cookies_fwd if c.startswith("senda_theme="))
    assert "Secure" in theme_cookie_fwd

    # 3. Reverse proxy without TLS (X-Forwarded-Proto: http)
    resp_http = client.get("/?theme=dark&lang=es", headers={"X-Forwarded-Proto": "http"})
    assert resp_http.status_code == 200
    cookies_http = resp_http.headers.get_list("set-cookie")
    theme_cookie_http = next(c for c in cookies_http if c.startswith("senda_theme="))
    assert "Secure" not in theme_cookie_http


def test_functional_cookies_rejects_spoofed_proxy_header_from_untrusted_client(tmp_path):
    """Hostile external client attempting to spoof X-Forwarded-Proto from untrusted IP must be rejected."""
    storage = StorageEngine(db_path=tmp_path / "spoof_test.db")
    app = create_app(storage=storage, enable_federated_providers=False)
    # Untrusted external client IP
    untrusted_client = TestClient(app, client=("198.51.100.42", 48123))

    resp = untrusted_client.get("/?theme=dark&lang=es", headers={"X-Forwarded-Proto": "https"})
    assert resp.status_code == 200
    cookies = resp.headers.get_list("set-cookie")
    theme_cookie = next(c for c in cookies if c.startswith("senda_theme="))
    # Spoofed header from untrusted client IP must NOT trigger Secure
    assert "Secure" not in theme_cookie


def test_functional_cookies_contain_no_tracking_identifiers(client):
    """Functional cookies must only store sanitized preference values, never arbitrary IDs or session tokens."""
    # Attempting to send invalid/arbitrary values via query params
    resp = client.get("/?theme=malicious_tracking_token_12345&lang=invalid_lang_code_67890")
    assert resp.status_code == 200

    # No cookies should be set for invalid theme or unsupported lang
    set_cookies = resp.headers.get_list("set-cookie")
    assert set_cookies == []
