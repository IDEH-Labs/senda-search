# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Open Access CC0 Museum & Heritage Image Provider for Senda Search Engine.

Strictly queries verified public domain and CC0 1.0 open-access collections from world-renowned
cultural institutions (Cleveland Museum of Art, Art Institute of Chicago),
allowing 100% free personal and commercial reuse, download and adaptation.
"""

from collections import deque
import html
import logging
import time
from typing import Optional, List, Dict, Tuple, Any
import urllib.parse
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance

logger = logging.getLogger(__name__)


class OpenAccessMuseumProvider(SearchProvider):
    """Federated provider for verified CC0 Open Access museum collections."""

    def __init__(
        self,
        timeout: float = 5.0,
        rate_limit_per_minute: int = 60,
        cache_ttl_seconds: int = 3600,
        enabled: bool = True,
    ):
        self.timeout = timeout
        self.rate_limit_per_minute = rate_limit_per_minute
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enabled = enabled
        self._cache: Dict[str, Tuple[float, List[SearchResultItem]]] = {}
        self._request_timestamps: deque = deque()

    @property
    def name(self) -> str:
        return "Museos de Acceso Abierto (CC0)"

    @property
    def is_configured(self) -> bool:
        return self.enabled

    def _check_rate_limit(self) -> bool:
        now = time.monotonic()
        while self._request_timestamps and now - self._request_timestamps[0] > 60.0:
            self._request_timestamps.popleft()
        if len(self._request_timestamps) >= self.rate_limit_per_minute:
            return False
        self._request_timestamps.append(now)
        return True

    def _get_from_cache(self, key: str) -> Optional[List[SearchResultItem]]:
        if key in self._cache:
            ts, items = self._cache[key]
            if time.time() - ts < self.cache_ttl_seconds:
                return items
            del self._cache[key]
        return None

    def _save_to_cache(self, key: str, items: List[SearchResultItem]) -> None:
        if len(self._cache) > 500:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._cache[key] = (time.time(), items)

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
        """Fetch CC0 public domain museum artwork & photographs matching the query."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        cache_key = f"museums:{clean_q}:{page}:{page_size}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if not self._check_rate_limit():
            return []

        items: List[SearchResultItem] = []
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        # Divide page_size between Cleveland and Chicago
        half_limit = max(4, page_size // 2)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            # 1. Cleveland Museum of Art (CMA Open Access CC0)
            try:
                cma_params = {
                    "q": clean_q,
                    "cc0": "1",
                    "has_image": "1",
                    "limit": str(half_limit),
                    "skip": str((max(1, page) - 1) * half_limit),
                }
                cma_url = f"https://openaccess-api.clevelandart.org/api/artworks/?{urllib.parse.urlencode(cma_params)}"
                resp = await client.get(cma_url, headers=headers)
                if resp.status_code == 200:
                    items.extend(self.parse_cma(resp.json()))
            except Exception as exc:
                logger.debug("CMA query error: %s", exc)

            # 2. Art Institute of Chicago (AIC Open Access CC0)
            try:
                aic_params = {
                    "q": clean_q,
                    "query[term][is_public_domain]": "true",
                    "fields": "id,title,artist_title,image_id,thumbnail,date_display,dimensions",
                    "limit": str(half_limit),
                    "page": str(max(1, page)),
                }
                aic_url = f"https://api.artic.edu/api/v1/artworks/search?{urllib.parse.urlencode(aic_params)}"
                resp = await client.get(aic_url, headers=headers)
                if resp.status_code == 200:
                    items.extend(self.parse_aic(resp.json()))
            except Exception as exc:
                logger.debug("AIC query error: %s", exc)

        self._save_to_cache(cache_key, items)
        return items[:page_size]

    def parse_cma(self, data: Dict[str, Any]) -> List[SearchResultItem]:
        """Parse Cleveland Museum of Art Open Access response."""
        items: List[SearchResultItem] = []
        if not isinstance(data, dict):
            return items

        artworks = data.get("data", [])
        if not isinstance(artworks, list):
            return items

        for art in artworks:
            if not isinstance(art, dict):
                continue

            images = art.get("images") or {}
            web_img = (images.get("web") or {}).get("url")
            print_img = (images.get("print") or {}).get("url") or web_img
            if not web_img:
                continue

            title = (art.get("title") or "Obra en Dominio Público").strip()
            creators = art.get("creators") or []
            artist_name = "Artista desconocido"
            if creators and isinstance(creators, list) and isinstance(creators[0], dict):
                artist_name = creators[0].get("description") or "Colección CMA"

            landing_url = art.get("url") or f"https://www.clevelandart.org/art/{art.get('id', '')}"
            dimensions = art.get("dimensions") or None

            items.append(
                SearchResultItem(
                    url=landing_url,
                    title=title,
                    snippet=f"Obra en Dominio Público (CC0) del Cleveland Museum of Art. Creada por {artist_name}.",
                    score=91.0,
                    source="Cleveland Museum of Art (CC0)",
                    media_url=web_img,
                    download_url=print_img,
                    dimensions=dimensions,
                    license="CC0 1.0 (Dominio Público)",
                    license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                    doc_type="images",
                    date=art.get("creation_date"),
                    is_sponsored=False,
                    canonical_url=landing_url,
                    source_type="primaria_oficial",
                    content_type="imagen_libre",
                    published_date=art.get("creation_date"),
                    authors=[artist_name],
                    provider_origin="Cleveland Museum of Art",
                    why_seen="Obra de arte y patrimonio en Dominio Público (CC0 1.0) sin restricciones de uso personal ni comercial.",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )

        return items

    def parse_aic(self, data: Dict[str, Any]) -> List[SearchResultItem]:
        """Parse Art Institute of Chicago Open Access response."""
        items: List[SearchResultItem] = []
        if not isinstance(data, dict):
            return items

        artworks = data.get("data", [])
        if not isinstance(artworks, list):
            return items

        for art in artworks:
            if not isinstance(art, dict):
                continue

            image_id = art.get("image_id")
            if not image_id:
                continue

            # IIIF standard image delivery URLs for Art Institute of Chicago
            thumb_url = f"https://www.artic.edu/iiif/2/{image_id}/full/600,/0/default.jpg"
            download_url = f"https://www.artic.edu/iiif/2/{image_id}/full/1686,/0/default.jpg"

            art_id = art.get("id")
            landing_url = f"https://www.artic.edu/artworks/{art_id}" if art_id else "https://www.artic.edu"
            title = (art.get("title") or "Obra en Dominio Público").strip()
            artist = (art.get("artist_title") or "Colección Art Institute of Chicago").strip()
            date_display = art.get("date_display")
            dimensions = art.get("dimensions") or None

            items.append(
                SearchResultItem(
                    url=landing_url,
                    title=title,
                    snippet=f"Patrimonio en Dominio Público (CC0) del Art Institute of Chicago. Autoría: {artist}.",
                    score=91.0,
                    source="Art Institute of Chicago (CC0)",
                    media_url=thumb_url,
                    download_url=download_url,
                    dimensions=dimensions,
                    license="CC0 1.0 (Dominio Público)",
                    license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                    doc_type="images",
                    date=date_display,
                    is_sponsored=False,
                    canonical_url=landing_url,
                    source_type="primaria_oficial",
                    content_type="imagen_libre",
                    published_date=date_display,
                    authors=[artist],
                    provider_origin="Art Institute of Chicago",
                    why_seen="Patrimonio visual y cultural en Dominio Público (CC0 1.0), libre de derechos de autor y de libre reutilización.",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )

        return items
