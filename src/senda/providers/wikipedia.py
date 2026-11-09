# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Verifiable Wikipedia & Wikidata Knowledge Entity Provider for Senda.

Retrieves encyclopedic summaries, biographical data, and provenance metadata
directly from official Wikimedia REST APIs. Requires zero local disk storage,
attributes all facts under Creative Commons CC BY-SA 4.0, and provides links to revision histories.
"""

import time
import urllib.parse
from typing import Dict, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

from senda.config import settings


class WikipediaEntityCard(BaseModel):
    """Normalized encyclopedic entity card with transparent provenance."""

    title: str = Field(description="Normalized entity title")
    description: Optional[str] = Field(default=None, description="Short factual description")
    extract: str = Field(description="Encyclopedic summary extract")
    thumbnail_url: Optional[str] = Field(default=None, description="Verified thumbnail image URL")
    wikipedia_url: str = Field(description="Permanent link to Wikipedia article")
    history_url: str = Field(description="Direct link to revision history for auditability")
    wikibase_item: Optional[str] = Field(default=None, description="Wikidata entity ID (e.g. Q937)")
    last_updated: Optional[str] = Field(default=None, description="ISO timestamp of last revision")
    license: str = Field(default="Creative Commons Atribución-CompartirIgual 4.0 (CC BY-SA 4.0)")
    source: str = Field(default="Wikipedia en Español")
    lang: str = Field(default="es")


class WikipediaEntityProvider:
    """Fetches and caches encyclopedic entities on demand with zero tracking."""

    def __init__(self, timeout: float = 3.5, cache_ttl_seconds: int = 3600):
        self.timeout = timeout
        self.cache_ttl_seconds = cache_ttl_seconds
        # In-memory volatile cache: key -> (timestamp, WikipediaEntityCard)
        self._cache: Dict[str, Tuple[float, Optional[WikipediaEntityCard]]] = {}

    def _cache_get(self, key: str) -> Optional[WikipediaEntityCard]:
        cached = self._cache.get(key)
        if not cached:
            return None
        ts, item = cached
        if time.time() - ts > self.cache_ttl_seconds:
            self._cache.pop(key, None)
            return None
        return item

    def _cache_set(self, key: str, item: Optional[WikipediaEntityCard]):
        self._cache[key] = (time.time(), item)

    def parse_summary(self, data: dict, lang: str = "es") -> Optional[WikipediaEntityCard]:
        """Convert a Wikipedia REST API summary response into a WikipediaEntityCard."""
        if not isinstance(data, dict):
            return None

        # Exclude disambiguation pages or empty pages
        if data.get("type") in ("disambiguation", "no-extract"):
            return None

        title = data.get("title")
        extract = data.get("extract")
        if not title or not extract:
            return None

        description = data.get("description")
        thumbnail = data.get("thumbnail") or {}
        thumbnail_url = thumbnail.get("source")

        urls = data.get("content_urls") or {}
        desktop_urls = urls.get("desktop") or {}
        wiki_url = desktop_urls.get("page") or f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title)}"

        # Construct history link for transparent auditability
        history_url = f"https://{lang}.wikipedia.org/w/index.php?title={urllib.parse.quote(title)}&action=history"

        wikibase_item = data.get("wikibase_item")
        last_updated = data.get("timestamp")

        source_name = "Wikipedia en Español" if lang == "es" else f"Wikipedia ({lang.upper()})"

        return WikipediaEntityCard(
            title=title,
            description=description,
            extract=extract,
            thumbnail_url=thumbnail_url,
            wikipedia_url=wiki_url,
            history_url=history_url,
            wikibase_item=wikibase_item,
            last_updated=last_updated,
            source=source_name,
            lang=lang,
        )

    async def get_entity(self, query: str, lang: str = "es") -> Optional[WikipediaEntityCard]:
        """Fetch entity summary for a query term if an exact encyclopedic article exists."""
        clean_q = query.strip()
        if not clean_q or len(clean_q) < 2:
            return None

        # Ignore common operators or bangs
        if clean_q.startswith("!"):
            return None

        cache_key = f"{lang}:{clean_q.lower()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        # Prepare normalized title (spaces to underscores, capitalized words)
        norm_title = urllib.parse.quote(clean_q.replace(" ", "_"))
        api_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{norm_title}"

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    card = self.parse_summary(data, lang=lang)
                    self._cache_set(cache_key, card)
                    return card
                elif resp.status_code == 404:
                    # Not an encyclopedic entry; cache absence briefly to prevent repeat requests
                    self._cache_set(cache_key, None)
                    return None
        except Exception:
            return None

        return None
