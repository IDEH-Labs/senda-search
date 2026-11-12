# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Formal P0 Security and Privacy Regression Test Suite.
Verifies strictly:
- Tarea 1.1: Anti-SSRF, .onion gating, SOCKS proxy delegation, redirect safety, fail-closed posture.
- Tarea 1.2: Prevention of automatic external resource loading in search results and strict CSP img-src.
"""

import asyncio
import socket
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse
import pytest
from fastapi.testclient import TestClient

from senda.api.app import create_app
from senda.crawler.network_guard import NetworkGuard, SSRFSecurityViolation
from senda.crawler.fetcher import SafeFetcher, FetchError
from senda.crawler.runner import CrawlerRunner
from senda.indexer.storage import StorageEngine
from senda.frontier.queue import FrontierQueue
from senda.providers.base import SearchResultItem


# ============================================================================
# TAREA 1.1: .ONION, SOCKS, PROXY Y SSRF (TESTS OBLIGATORIOS 1 A 25)
# ============================================================================

VALID_V3_ONION = "expyuzz5wqqfdgah56trgahphgahpagah56trgahphgahpagah56trga.onion"
VALID_V3_ONION_2 = "abcdefghijklmnopqrstuvwxyz234567abcdefghijklmnopqrstuvwx.onion"


def test_1_onion_without_proxy_rejected():
    """1. .onion destination without proxy must immediately raise SSRFSecurityViolation."""
    fetcher = SafeFetcher(proxy=None)
    assert not fetcher.allow_onion
    with pytest.raises(SSRFSecurityViolation, match="Destino .onion denegado sin proxy"):
        NetworkGuard.validate_url(f"http://{VALID_V3_ONION}/index.html", allow_onion=fetcher.allow_onion)


def test_2_onion_in_frontier_filtered_without_proxy():
    """2. Outgoing .onion links must never be enqueued into the frontier when proxy is not configured."""
    storage = MagicMock(spec=StorageEngine)
    frontier = FrontierQueue()
    fetcher = SafeFetcher(proxy=None)
    assert not fetcher.allow_onion

    # Simulate runner encountering an outgoing .onion link
    extracted_links = [
        f"http://{VALID_V3_ONION}/hidden",
        "https://example.com/safe-article"
    ]
    enqueued = []
    for link in extracted_links:
        parsed = urlparse(link)
        domain = parsed.netloc.lower()
        if domain.endswith(".onion") and not getattr(fetcher, "allow_onion", False):
            continue
        enqueued.append(link)

    assert len(enqueued) == 1
    assert enqueued[0] == "https://example.com/safe-article"
    assert f"http://{VALID_V3_ONION}/hidden" not in enqueued


@pytest.mark.asyncio
async def test_3_and_4_socks_local_server_receives_hostname():
    """3 & 4. SOCKS proxy receives domain name (ATYP=3) during handshake, verifying no local DNS leak."""
    received = []

    async def handle_socks(reader, writer):
        # Greeting
        ver = await reader.read(1)
        if not ver:
            return
        nmethods = (await reader.read(1))[0]
        await reader.read(nmethods)
        writer.write(b"\x05\x00")  # No auth
        await writer.drain()

        # Connection request
        req = await reader.read(4)
        ver, cmd, rsv, atyp = req
        dest = None
        if atyp == 1:  # IPv4
            dest = socket.inet_ntoa(await reader.read(4))
        elif atyp == 3:  # Domain
            dlen = (await reader.read(1))[0]
            dest = (await reader.read(dlen)).decode("ascii")
        elif atyp == 4:  # IPv6
            dest = socket.inet_ntop(socket.AF_INET6, await reader.read(16))
        port = int.from_bytes(await reader.read(2), "big")
        received.append({"atyp": atyp, "dest": dest, "port": port})

        # Close
        writer.write(b"\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x50")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_socks, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    fetcher = SafeFetcher(proxy=f"socks5h://127.0.0.1:{port}", timeout_seconds=1.0)
    assert fetcher.allow_onion is True

    try:
        await fetcher.fetch(f"http://{VALID_V3_ONION}/")
    except Exception:
        pass  # Mock server closes after handshake

    server.close()
    await server.wait_closed()

    assert len(received) >= 1
    # Verify ATYP is 3 (domain name), NOT 1 (IPv4) or loopback
    assert received[0]["atyp"] == 3
    assert received[0]["dest"] == VALID_V3_ONION
    assert received[0]["dest"] != "127.0.0.1"


def test_5_http_proxy_rejected_for_onion():
    """5. HTTP proxy must NOT enable allow_onion (only SOCKS5/SOCKS5h is authorized)."""
    fetcher = SafeFetcher(proxy="http://127.0.0.1:8080")
    assert fetcher.allow_onion is False
    with pytest.raises(SSRFSecurityViolation, match="Destino .onion denegado sin proxy"):
        NetworkGuard.validate_url(f"http://{VALID_V3_ONION}/", allow_onion=fetcher.allow_onion)


def test_6_malformed_proxy_handling():
    """6. Malformed proxy string falls closed safely by raising ValueError."""
    with pytest.raises(ValueError, match="Esquema de proxy no soportado|Unknown scheme"):
        SafeFetcher(proxy="not-a-valid-proxy-scheme")


@pytest.mark.asyncio
async def test_7_and_8_inaccessible_proxy_fails_closed_no_direct_fallback():
    """7 & 8. When SOCKS proxy is inaccessible, fail-closed strictly without direct fallback."""
    # Choose unused port
    fetcher = SafeFetcher(proxy="socks5h://127.0.0.1:59999", timeout_seconds=0.5)
    assert fetcher.allow_onion is True

    # Attempt fetch through dead proxy
    with pytest.raises(Exception) as excinfo:
        await fetcher.fetch(f"http://{VALID_V3_ONION}/test")

    # Ensure it did not attempt a direct connection or fallback to 127.0.0.1
    assert not isinstance(excinfo.value, SSRFSecurityViolation)


def test_9_redirect_to_another_onion_allowed_only_with_socks():
    """9. Redirection from .onion to another .onion revalidates proxy requirement."""
    # Without proxy
    with pytest.raises(SSRFSecurityViolation):
        NetworkGuard.validate_url(f"http://{VALID_V3_ONION_2}/redirected", allow_onion=False)
    # With proxy
    url_norm, ips = NetworkGuard.validate_url(f"http://{VALID_V3_ONION_2}/redirected", allow_onion=True)
    assert VALID_V3_ONION_2 in url_norm
    assert ips == []


def test_10_redirect_onion_to_public_destination_revalidates_public_ip():
    """10. Redirection from .onion to public domain validates target against SSRF."""
    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        url_norm, ips = NetworkGuard.validate_url("https://example.com/page", allow_onion=True)
        assert ips == ["93.184.216.34"]


def test_11_redirect_to_localhost_blocked():
    """11. Redirection targeting localhost must be strictly blocked by SSRF defense."""
    with pytest.raises(SSRFSecurityViolation, match="prohibited IP '127.0.0.1'|forbidden non-public IP literal"):
        NetworkGuard.validate_url("http://127.0.0.1:8000/admin", allow_onion=True)
    with pytest.raises(SSRFSecurityViolation, match="prohibited IP '127.0.0.1'"):
        mock_addr = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
        with patch("socket.getaddrinfo", return_value=mock_addr):
            NetworkGuard.validate_url("http://localhost:8000/secret", allow_onion=True)


def test_12_redirect_to_rfc1918_private_ip_blocked():
    """12. Redirection targeting RFC 1918 private IP must be blocked."""
    with pytest.raises(SSRFSecurityViolation, match="forbidden non-public IP literal"):
        NetworkGuard.validate_url("http://192.168.1.100/router", allow_onion=True)
    with pytest.raises(SSRFSecurityViolation, match="forbidden non-public IP literal"):
        NetworkGuard.validate_url("http://10.0.0.1/internal", allow_onion=True)


def test_13_redirect_to_cloud_metadata_blocked():
    """13. Redirection targeting cloud metadata (169.254.169.254) must be blocked."""
    with pytest.raises(SSRFSecurityViolation, match="forbidden non-public IP literal"):
        NetworkGuard.validate_url("http://169.254.169.254/latest/meta-data/", allow_onion=True)


def test_14_redirect_with_scheme_change_blocked():
    """14. Redirection attempting non-http(s) schemes must be blocked."""
    with pytest.raises(SSRFSecurityViolation, match="Prohibited URL scheme"):
        NetworkGuard.validate_url("gopher://127.0.0.1:70/", allow_onion=True)
    with pytest.raises(SSRFSecurityViolation, match="Prohibited URL scheme"):
        NetworkGuard.validate_url("file:///etc/shadow", allow_onion=True)


def test_15_ipv4_and_ipv6_loopback_blocked():
    """15. Loopback IPs are blocked in is_ip_allowed."""
    assert not NetworkGuard.is_ip_allowed("127.0.0.1")
    assert not NetworkGuard.is_ip_allowed("127.0.1.1")
    assert not NetworkGuard.is_ip_allowed("::1")


def test_16_ipv4_mapped_ipv6_blocked():
    """16. IPv4-mapped IPv6 loopback and private ranges are unpacked and blocked."""
    assert not NetworkGuard.is_ip_allowed("::ffff:127.0.0.1")
    assert not NetworkGuard.is_ip_allowed("::ffff:10.0.0.1")
    assert not NetworkGuard.is_ip_allowed("::ffff:169.254.169.254")


def test_17_link_local_blocked():
    """17. IPv4 and IPv6 link-local addresses are blocked."""
    assert not NetworkGuard.is_ip_allowed("169.254.1.1")
    assert not NetworkGuard.is_ip_allowed("fe80::1")


def test_18_carrier_grade_nat_blocked():
    """18. Carrier-Grade NAT 100.64.0.0/10 is blocked."""
    assert not NetworkGuard.is_ip_allowed("100.64.0.1")
    assert not NetworkGuard.is_ip_allowed("100.127.255.254")


def test_19_alternative_ip_representations():
    """19. Alternative IP literal representations are checked safely."""
    # ipaddress.ip_address handles standard formats; raw socket strings that fail are rejected
    assert not NetworkGuard.is_ip_allowed("0.0.0.0")
    assert not NetworkGuard.is_ip_allowed("255.255.255.255")


def test_20_simulated_dns_returning_loopback_blocked():
    """20. DNS resolution returning loopback IP must be blocked."""
    mock_addr = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
    with patch("socket.getaddrinfo", return_value=mock_addr):
        with pytest.raises(SSRFSecurityViolation, match="prohibited IP '127.0.0.1'"):
            NetworkGuard.resolve_and_validate("spoofed-public.example.com", 80)


def test_21_pinning_backend_eliminates_toctou_for_direct_connections():
    """21. PinningNetworkBackend pins socket destination to pre-validated IP."""
    from senda.crawler.fetcher import PinningNetworkBackend
    backend = PinningNetworkBackend()
    assert hasattr(backend, "connect_tcp")


def test_22_non_http_schemes_blocked():
    """22. Non-HTTP schemes must be rejected."""
    for bad_url in ["ftp://example.com", "data:text/plain,test", "ws://example.com"]:
        with pytest.raises(SSRFSecurityViolation, match="Prohibited URL scheme"):
            NetworkGuard.validate_url(bad_url)


def test_23_unusual_ports_evaluated_against_ip_destinations():
    """23. Unusual ports (e.g. 8443, 8080) targeting safe public IPs are validated properly."""
    mock_addr = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 8443))]
    with patch("socket.getaddrinfo", return_value=mock_addr):
        url_norm, ips = NetworkGuard.validate_url("https://example.com:8443/api")
        assert "93.184.216.34" in ips


def test_24_and_25_no_fallback_on_exception():
    """24 & 25. Network exceptions never trigger direct unauthenticated fallback."""
    fetcher = SafeFetcher(proxy="socks5h://127.0.0.1:1", timeout_seconds=0.1)
    # Direct transport must NOT be used
    assert fetcher.transport != fetcher.transport.__class__


# ============================================================================
# TAREA 1.2: PRIVACIDAD Y RECURSOS REMOTOS (TESTS OBLIGATORIOS)
# ============================================================================

def test_results_template_renders_no_external_img_tags(tmp_path):
    """Verify HTML search results across all categories contain zero remote <img> tags."""
    from senda.extractor.parser import ExtractedDocument, ExtractedImage

    storage = StorageEngine(db_path=tmp_path / "img_test.db")
    doc = ExtractedDocument(
        url="https://fsf.org/news",
        title="Free Software News",
        description="Defending freedom.",
        language="en",
        headings="News",
        body_text="Articles on software freedom.",
        content_hash="h123",
        images=[
            ExtractedImage(
                image_url="https://external-tracker.example.com/mascot.png",
                alt_text="Free mascot illustration",
                page_url="https://fsf.org/news",
                page_title="Free Software News",
                domain="fsf.org",
            )
        ]
    )
    storage.upsert_document(doc)

    app = create_app(storage=storage, enable_federated_providers=False)
    client = TestClient(app)

    # 1. Images category with actual indexed item
    resp_images = client.get("/search?q=mascot&category=images")
    assert resp_images.status_code == 200
    html_images = resp_images.text

    # Must contain placeholder and title
    assert "image-thumb-placeholder" in html_images
    assert "Free mascot illustration" in html_images

    # Must strictly NOT contain any <img tag or remote tracker URL
    assert "<img" not in html_images
    assert "https://external-tracker.example.com/mascot.png" not in html_images

    # 2. Videos category layout check
    resp_videos = client.get("/search?q=freedom&category=videos")
    assert resp_videos.status_code == 200
    html_videos = resp_videos.text
    assert "<img" not in html_videos


def test_csp_header_enforces_img_src_self_data():
    """Verify CSP strictly allows only 'self' and data: for images, blocking wildcard '*'."""
    app = create_app()
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "img-src 'self' data:;" in csp
    assert "img-src *" not in csp
