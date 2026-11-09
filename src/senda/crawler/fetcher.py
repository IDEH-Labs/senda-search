# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Safe, asynchronous HTTP document fetcher with anti-SSRF and DoS protections.

Adheres strictly to security limits: size quotas, timeout guards, redirect
inspection, and MIME-type gating.
"""

from dataclasses import dataclass
from typing import Optional, Iterable
from urllib.parse import urljoin
import httpcore
import httpx

from senda.config import settings
from senda.crawler.network_guard import NetworkGuard, SSRFSecurityViolation


class FetchError(Exception):
    """Base exception for crawler fetching errors."""
    pass


class DocumentTooLargeError(FetchError):
    """Raised when a remote payload exceeds MAX_DOCUMENT_SIZE_BYTES."""
    pass


class UnsupportedContentTypeError(FetchError):
    """Raised when the remote resource is not indexable HTML/text."""
    pass


class PinningNetworkBackend(httpcore.AnyIOBackend):
    """Custom network backend enforcing DNS pre-resolution and IP socket pinning.

    Closes the Time-Of-Check to Time-Of-Use (TOCTOU) DNS rebinding vulnerability by
    ensuring the TCP socket connects exclusively to the pre-validated public IP,
    while allowing TLS certificate checks to inspect the original hostname.
    """

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options: Optional[Iterable] = None,
    ) -> httpcore.AsyncNetworkStream:
        validated_ips = NetworkGuard.resolve_and_validate(host, port)
        pinned_ip = validated_ips[0]
        return await super().connect_tcp(
            host=pinned_ip,
            port=port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class AntiSSRFTransport(httpx.AsyncHTTPTransport):
    """Hardened HTTP transport leveraging PinningNetworkBackend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pool._network_backend = PinningNetworkBackend()


@dataclass(frozen=True)
class FetchedDocument:
    """Immutable representation of a safely retrieved web document."""
    url: str
    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str
    content_type: str
    encoding: str


class SafeFetcher:
    """Hardened HTTP client designed for sovereign, ethical web crawling."""

    INDEXABLE_CONTENT_TYPES = (
        "text/html",
        "application/xhtml+xml",
        "text/plain",
    )

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_size_bytes: Optional[int] = None,
        max_redirects: Optional[int] = None,
        proxy: Optional[str] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.user_agent = user_agent or settings.USER_AGENT
        self.timeout_seconds = timeout_seconds or settings.REQUEST_TIMEOUT_SECONDS
        self.max_size_bytes = max_size_bytes or settings.MAX_DOCUMENT_SIZE_BYTES
        self.max_redirects = max_redirects or settings.MAX_REDIRECTS
        self.proxy = proxy or settings.CRAWLER_PROXY or None

        if transport:
            self.transport = transport
        elif self.proxy:
            self.transport = httpx.AsyncHTTPTransport(proxy=self.proxy, verify=True)
        else:
            self.transport = AntiSSRFTransport(verify=True)

    async def fetch(self, url: str) -> FetchedDocument:
        """Safely fetch a URL with full anti-SSRF verification and streaming size guards.

        Follows redirects manually up to max_redirects, validating every hop's DNS
        against SSRF rules before making the request.
        """
        current_url = url
        redirect_count = 0

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.1",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8,*;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }

        async with httpx.AsyncClient(
            transport=self.transport,
            timeout=httpx.Timeout(self.timeout_seconds),
            follow_redirects=False,  # We manage redirects manually to validate every destination
        ) as client:
            while True:
                # 1. Anti-SSRF check on the current target URL
                NetworkGuard.validate_url(current_url)

                try:
                    # Stream request so we can inspect headers before buffering body
                    async with client.stream("GET", current_url, headers=headers) as response:
                        # 2. Check for redirect responses (301, 302, 303, 307, 308)
                        if response.status_code in (301, 302, 303, 307, 308):
                            location = response.headers.get("Location")
                            if not location:
                                raise FetchError(f"HTTP {response.status_code} received without Location header.")

                            redirect_count += 1
                            if redirect_count > self.max_redirects:
                                raise FetchError(f"Exceeded maximum redirect limit of {self.max_redirects}.")

                            current_url = urljoin(current_url, location)
                            continue

                        # 3. Content-Type inspection
                        content_type_header = response.headers.get("Content-Type", "").lower()
                        media_type = content_type_header.split(";")[0].strip()

                        if media_type and not any(media_type.startswith(t) for t in self.INDEXABLE_CONTENT_TYPES):
                            raise UnsupportedContentTypeError(
                                f"Non-indexable content type '{media_type}' at {current_url}"
                            )

                        # 4. Content-Length pre-check (if declared)
                        content_length = response.headers.get("Content-Length")
                        if content_length and content_length.isdigit():
                            if int(content_length) > self.max_size_bytes:
                                raise DocumentTooLargeError(
                                    f"Document length {content_length} bytes exceeds limit of {self.max_size_bytes}"
                                )

                        # 5. Stream and enforce size limit
                        body_chunks = []
                        total_bytes = 0

                        async for chunk in response.aiter_bytes():
                            total_bytes += len(chunk)
                            if total_bytes > self.max_size_bytes:
                                raise DocumentTooLargeError(
                                    f"Document exceeded max size limit of {self.max_size_bytes} bytes during streaming."
                                )
                            body_chunks.append(chunk)

                        content_bytes = b"".join(body_chunks)
                        encoding = response.encoding or "utf-8"

                        try:
                            text_body = content_bytes.decode(encoding, errors="replace")
                        except Exception:
                            text_body = content_bytes.decode("utf-8", errors="replace")

                        return FetchedDocument(
                            url=str(response.url),
                            status_code=response.status_code,
                            headers=dict(response.headers),
                            content=content_bytes,
                            text=text_body,
                            content_type=media_type or "text/html",
                            encoding=encoding,
                        )

                except httpx.TimeoutException as e:
                    raise FetchError(f"Request timed out for '{current_url}': {e}") from e
                except httpx.RequestError as e:
                    raise FetchError(f"Network error requesting '{current_url}': {e}") from e
