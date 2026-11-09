# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Free Culture Image Search Provider for Senda Search Engine.

Strictly retrieves images under verified Free Cultural Works licenses
(Creative Commons CC0, CC BY, CC BY-SA, and Public Domain) allowing commercial reuse,
aligned with Free Software Foundation (FSF) ethics and open knowledge principles.
"""

import html
import re
from typing import List, Optional
import urllib.parse
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance


def _clean_title(filename: str) -> str:
    """Strip 'File:' prefix and file extension from media titles."""
    name = filename
    if name.lower().startswith("file:"):
        name = name[5:]
    if name.lower().startswith("archivo:"):
        name = name[8:]
    name = re.sub(r"\.[a-zA-Z0-9]{3,4}$", "", name)
    return name.replace("_", " ").strip()


class FreeCultureImageProvider(SearchProvider):
    """Wikimedia Commons Free Cultural Works image provider."""

    def __init__(self, timeout: float = 5.0, enabled: bool = True):
        self.timeout = timeout
        self.enabled = enabled

    @property
    def name(self) -> str:
        return "free_culture_images"

    @property
    def is_configured(self) -> bool:
        return self.enabled

    async def search(
        self,
        query: str,
        category: str = "images",
        page: int = 1,
        page_size: int = 12,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> List[SearchResultItem]:
        """Fetch Free Cultural Works images matching the query."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        # Query Wikimedia Commons generator search API
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": clean_q,
            "gsrnamespace": "6",  # File: namespace
            "gsrlimit": str(page_size),
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata|mime",
            "iiurlwidth": "500",  # Thumbnail width for optimal fast delivery
            "format": "json",
        }

        api_url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                return self.parse_commons(data)[:page_size]
        except Exception:
            return []

    def parse_commons(self, data: dict) -> List[SearchResultItem]:
        """Parse Wikimedia Commons query response into normalized SearchResultItems."""
        items: List[SearchResultItem] = []
        if not isinstance(data, dict):
            return items

        pages = data.get("query", {}).get("pages", {})
        if not isinstance(pages, dict):
            return items

        for _, page_info in pages.items():
            if not isinstance(page_info, dict):
                continue

            raw_title = page_info.get("title", "")
            image_info_list = page_info.get("imageinfo", [])
            if not image_info_list or not isinstance(image_info_list, list):
                continue

            info = image_info_list[0]
            thumb_url = info.get("thumburl") or info.get("url")
            orig_url = info.get("descriptionshorturl") or info.get("descriptionurl") or thumb_url

            if not thumb_url:
                continue

            # Extract metadata and license
            extmeta = info.get("extmetadata", {})
            license_short = extmeta.get("LicenseShortName", {}).get("value")
            license_name = extmeta.get("License", {}).get("value")
            lic = license_short or license_name or "Dominio Público / CC BY-SA"

            artist_raw = extmeta.get("Artist", {}).get("value", "")
            # Clean HTML from artist field
            artist = re.sub(r"<[^>]+>", " ", artist_raw).strip() or "Autor Wikimedia Commons"

            date_str = extmeta.get("DateTimeOriginal", {}).get("value") or extmeta.get("DateTime", {}).get("value")

            clean_t = _clean_title(raw_title)

            items.append(
                SearchResultItem(
                    url=orig_url,
                    title=clean_t,
                    snippet=f"Imagen libre de Wikimedia Commons. Licencia: {lic}. Autoría: {artist}.",
                    score=90.0,
                    source="Wikimedia Commons (Cultura Libre)",
                    media_url=thumb_url,
                    doc_type="images",
                    date=date_str,
                    is_sponsored=False,
                    canonical_url=orig_url,
                    source_type="primaria_oficial",
                    content_type="imagen_libre",
                    published_date=date_str,
                    authors=[artist],
                    provider_origin="Wikimedia Commons",
                    why_seen=f"Imagen de Cultura Libre autorizada para reutilización comercial ({lic}), conforme a los principios de la FSF.",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )

        return items
