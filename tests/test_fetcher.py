# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for SafeFetcher network security and download constraints."""

import pytest
from unittest.mock import patch
import httpx

from senda.crawler.fetcher import (
    SafeFetcher,
    FetchError,
    DocumentTooLargeError,
    UnsupportedContentTypeError,
)
from senda.crawler.network_guard import SSRFSecurityViolation


@pytest.mark.asyncio
async def test_fetcher_blocks_private_ip():
    fetcher = SafeFetcher()
    with pytest.raises(SSRFSecurityViolation):
        await fetcher.fetch("http://127.0.0.1:8080/secret")


@pytest.mark.asyncio
async def test_fetcher_blocks_redirect_to_private_ip():
    fetcher = SafeFetcher()

    # Mock NetworkGuard.validate_url to allow initial URL, but block the redirect URL
    original_validate = fetcher_guard = SafeFetcher

    with patch("senda.crawler.fetcher.NetworkGuard.validate_url") as mock_val:
        def side_effect(url):
            if "127.0.0.1" in url or "localhost" in url:
                raise SSRFSecurityViolation("SSRF blocked")
            return ("https://example.com", ["93.184.216.34"])

        mock_val.side_effect = side_effect

        # Mock httpx response that redirects to 127.0.0.1
        class MockRedirectTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(
                    302,
                    headers={"Location": "http://127.0.0.1/admin"},
                    request=request,
                )

        with patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=MockRedirectTransport())):
            with pytest.raises(SSRFSecurityViolation):
                await fetcher.fetch("https://example.com/login")


@pytest.mark.asyncio
async def test_fetcher_rejects_unsupported_content_type():
    fetcher = SafeFetcher()

    with patch("senda.crawler.fetcher.NetworkGuard.validate_url"):
        class MockPdfTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(
                    200,
                    headers={"Content-Type": "application/pdf"},
                    content=b"%PDF-1.4 ...",
                    request=request,
                )

        with patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=MockPdfTransport())):
            with pytest.raises(UnsupportedContentTypeError):
                await fetcher.fetch("https://example.com/file.pdf")


@pytest.mark.asyncio
async def test_fetcher_enforces_size_limit_on_content_length():
    fetcher = SafeFetcher(max_size_bytes=100)

    with patch("senda.crawler.fetcher.NetworkGuard.validate_url"):
        class MockLargeHeaderTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(
                    200,
                    headers={"Content-Type": "text/html", "Content-Length": "5000"},
                    content=b"hello",
                    request=request,
                )

        with patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=MockLargeHeaderTransport())):
            with pytest.raises(DocumentTooLargeError):
                await fetcher.fetch("https://example.com/large")


@pytest.mark.asyncio
async def test_fetcher_enforces_size_limit_during_streaming():
    fetcher = SafeFetcher(max_size_bytes=50)

    with patch("senda.crawler.fetcher.NetworkGuard.validate_url"):
        class MockStreamingLargeTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(
                    200,
                    headers={"Content-Type": "text/html"},
                    content=b"A" * 200,
                    request=request,
                )

        with patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=MockStreamingLargeTransport())):
            with pytest.raises(DocumentTooLargeError):
                await fetcher.fetch("https://example.com/stream-bomb")


@pytest.mark.asyncio
async def test_fetcher_successful_html_retrieval():
    fetcher = SafeFetcher()

    html_payload = "<html><head><title>Senda Test</title></head><body>Ethical Web</body></html>"

    with patch("senda.crawler.fetcher.NetworkGuard.validate_url"):
        class MockSuccessTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(
                    200,
                    headers={"Content-Type": "text/html; charset=utf-8"},
                    content=html_payload.encode("utf-8"),
                    request=request,
                )

        with patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=MockSuccessTransport())):
            doc = await fetcher.fetch("https://example.com/page")
            assert doc.status_code == 200
            assert doc.text == html_payload
            assert doc.content_type == "text/html"
            assert doc.encoding.lower() in ("utf-8", "utf8")


@pytest.mark.asyncio
async def test_pinning_network_backend_connects_to_validated_ip():
    from senda.crawler.fetcher import PinningNetworkBackend
    backend = PinningNetworkBackend()

    with patch("senda.crawler.network_guard.NetworkGuard.resolve_and_validate", return_value=["93.184.216.34"]):
        with patch("httpcore.AnyIOBackend.connect_tcp", new_callable=pytest.importorskip("unittest.mock").AsyncMock) as mock_connect:
            await backend.connect_tcp("example.com", 443)
            # Verify socket connected directly to the pinned public IP (anti-DNS rebinding)
            mock_connect.assert_called_once()
            assert mock_connect.call_args.kwargs["host"] == "93.184.216.34"

