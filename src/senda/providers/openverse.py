# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Openverse Search Provider for Senda Search Engine.

Accesses +700M Creative Commons and Public Domain images indexed by Openverse (WordPress Foundation),
strictly filtering for Free Cultural Works (commercial reuse and modifications allowed)
in adherence to Free Software Foundation (FSF) ethics and verifiable provenance.
"""

from collections import deque
import logging
import os
import time
from typing import Optional, List, Dict, Tuple, Any
import urllib.parse
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance

logger = logging.getLogger(__name__)


class OpenverseProvider(SearchProvider):
    """Adapter for Openverse REST API v1."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 6.0,
        rate_limit_per_minute: int = 60,
        cache_ttl_seconds: int = 3600,
        enabled: Optional[bool] = None,
    ):
        self.endpoint = (endpoint or getattr(settings, "OPENVERSE_ENDPOINT", "https://api.openverse.org/v1")).rstrip("/")
        # Check explicit parameter, settings model (SENDA_OPENVERSE_API_KEY via pydantic-settings), or direct os.environ
        resolved_key = (
            api_key
            if api_key is not None
            else getattr(settings, "OPENVERSE_API_KEY", "")
            or os.environ.get("SENDA_OPENVERSE_API_KEY", "")
            or os.environ.get("OPENVERSE_API_KEY", "")
        )
        self.api_key = resolved_key.strip()
        self.timeout = timeout
        self.rate_limit_per_minute = rate_limit_per_minute or getattr(settings, "OPENVERSE_RATE_LIMIT_PER_MINUTE", 60)
        self.cache_ttl_seconds = cache_ttl_seconds or getattr(settings, "OPENVERSE_CACHE_TTL_SECONDS", 3600)
        self._enabled = getattr(settings, "OPENVERSE_ENABLED", True) if enabled is None else enabled
        self.last_status: str = "ok"
        self.last_error: Optional[str] = None

        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._request_timestamps: deque = deque()

    @property
    def name(self) -> str:
        return "Openverse (Cultura Libre)"

    @property
    def is_configured(self) -> bool:
        return self._enabled

    def _check_rate_limit(self) -> bool:
        """Sliding-window rate limiter preventing upstream saturation."""
        now = time.monotonic()
        while self._request_timestamps and now - self._request_timestamps[0] > 60.0:
            self._request_timestamps.popleft()

        if len(self._request_timestamps) >= self.rate_limit_per_minute:
            return False

        self._request_timestamps.append(now)
        return True

    def _get_from_cache(self, cache_key: str) -> Optional[List[SearchResultItem]]:
        if cache_key in self._cache:
            ts, items = self._cache[cache_key]
            if time.time() - ts < self.cache_ttl_seconds:
                return items
            del self._cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, items: List[SearchResultItem]) -> None:
        if len(self._cache) > 500:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[cache_key] = (time.time(), items)

    async def search(
        self,
        query: str,
        category: str = "images",
        page: int = 1,
        page_size: int = 12,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        lang: Optional[str] = None,
        **kwargs: Any,
    ) -> List[SearchResultItem]:
        """Fetch Free Cultural Works images matching query via Openverse."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        cache_key = f"openverse:{clean_q}:{page}:{page_size}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self._check_rate_limit():
            logger.warning("OpenverseProvider: Rate limit excedido para %s", clean_q)
            return []

        # Filter strictly for commercial use and modification (Free Cultural Works / FSF compatible)
        params = {
            "q": clean_q,
            "page": str(max(1, page)),
            "page_size": str(min(50, max(1, page_size))),
            "license_type": "commercial,modification",
        }

        api_url = f"{self.endpoint}/images/?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 403:
                    self.last_status = "challenge_blocked"
                    self.last_error = "Desafío anti-bot de Cloudflare detectado (HTTP 403)."
                    logger.warning("OpenverseProvider: Desafío Cloudflare (HTTP 403) detectado. Fuente no disponible sin SENDA_OPENVERSE_API_KEY registrada.")
                    return []
                elif resp.status_code != 200:
                    self.last_status = f"http_{resp.status_code}"
                    self.last_error = f"Error HTTP {resp.status_code} desde api.openverse.org."
                    logger.warning("OpenverseProvider: Respuesta inesperada HTTP %s.", resp.status_code)
                    return []

                self.last_status = "ok"
                self.last_error = None
                data = resp.json()
                items = self.parse_results(data)
                self._save_to_cache(cache_key, items)
                return items
        except Exception as exc:
            self.last_status = "network_error"
            self.last_error = str(exc)
            logger.warning("OpenverseProvider: Error de conexión hacia api.openverse.org: %s", exc)
            return []

    def parse_results(self, data: Dict[str, Any]) -> List[SearchResultItem]:
        """Parse Openverse JSON response into normalized SearchResultItems."""
        items: List[SearchResultItem] = []
        if not isinstance(data, dict):
            return items

        results = data.get("results", [])
        if not isinstance(results, list):
            return items

        for item in results:
            if not isinstance(item, dict):
                continue

            orig_url = item.get("foreign_landing_url") or item.get("url")
            if not orig_url:
                continue

            thumb_url = item.get("thumbnail") or item.get("url")
            title = (item.get("title") or "Obra Libre (Openverse)").strip()
            creator = (item.get("creator") or "").strip()
            lic = (item.get("license") or "CC").upper()
            lic_ver = item.get("license_version") or ""
            full_lic = f"{lic} {lic_ver}".strip()

            author_name = creator if creator else "Autor en Openverse"
            attribution = item.get("attribution") or f"Obra de {author_name} bajo {full_lic}."

            snippet = f"Imagen de Cultura Libre indexada por Openverse. Licencia: {full_lic}. Autoría: {author_name}."

            items.append(
                SearchResultItem(
                    url=orig_url,
                    title=title,
                    snippet=snippet,
                    score=88.0,
                    source="Openverse (Cultura Libre)",
                    media_url=thumb_url,
                    doc_type="images",
                    date=None,
                    is_sponsored=False,
                    canonical_url=orig_url,
                    source_type="primaria_oficial",
                    content_type="imagen_libre",
                    published_date=None,
                    authors=[author_name],
                    provider_origin="Openverse",
                    why_seen=f"Imagen de Cultura Libre autorizada para reutilización comercial ({full_lic}), procedente de Openverse.",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )

        return items
