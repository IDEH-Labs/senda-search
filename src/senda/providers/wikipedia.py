# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Verifiable Wikipedia & Wikidata Knowledge Entity Provider for Senda.

Retrieves encyclopedic summaries, biographical data, and provenance metadata
directly from official Wikimedia REST APIs. Requires zero local disk storage,
attributes all facts under Creative Commons CC BY-SA 4.0, and provides links to revision histories.
"""

import html
import re
import time
import urllib.parse
from typing import Dict, List, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance


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
    official_website: Optional[str] = Field(default=None, description="Official verified website URL")


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

    async def get_entity(
        self,
        query: str,
        lang: str = "es",
        fetch_official_website: bool = False,
    ) -> Optional[WikipediaEntityCard]:
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
                    if fetch_official_website and card and card.wikibase_item:
                        try:
                            wb_url = f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={card.wikibase_item}&property=P856&format=json"
                            wb_resp = await client.get(wb_url, headers=headers)
                            if wb_resp.status_code == 200:
                                wb_data = wb_resp.json()
                                claims = wb_data.get("claims", {}).get("P856", [])
                                for c in claims:
                                    val = c.get("mainsnak", {}).get("datavalue", {}).get("value")
                                    if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://")):
                                        card.official_website = val
                                        break
                        except Exception:
                            pass
                    self._cache_set(cache_key, card)
                    return card
                elif resp.status_code == 404:
                    # Not an encyclopedic entry; cache absence briefly to prevent repeat requests
                    self._cache_set(cache_key, None)
                    return None
        except Exception:
            return None

        return None


class WikipediaSearchProvider(SearchProvider):
    """Full-text encyclopedic article search provider via Wikipedia REST API."""

    def __init__(self, lang: str = "es", timeout: float = 4.5, enabled: bool = True):
        self.lang = lang
        self.timeout = timeout
        self.enabled = enabled

    @property
    def name(self) -> str:
        return "wikipedia_search"

    @property
    def is_configured(self) -> bool:
        return self.enabled

    async def search(
        self,
        query: str,
        category: str = "all",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[SearchResultItem]:
        """Query official Wikipedia REST search API."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        target_lang = (lang or self.lang or "es").split("-")[0].lower()
        if target_lang not in ("ar", "de", "en", "es", "fr", "it", "ja", "pt", "ru", "zh"):
            target_lang = self.lang or "es"

        encoded_q = urllib.parse.quote(clean_q)
        api_url = f"https://{target_lang}.wikipedia.org/w/rest.php/v1/search/page?q={encoded_q}&limit={page_size}"
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
                return self.parse_pages(data, lang=target_lang)[:page_size]
        except Exception:
            return []

    def parse_pages(self, data: dict, lang: str = "es") -> List[SearchResultItem]:
        """Convert Wikipedia search API results into normalized SearchResultItems."""
        items: List[SearchResultItem] = []
        if not isinstance(data, dict):
            return items

        pages = data.get("pages", [])
        for p in pages:
            if not isinstance(p, dict):
                continue
            key = p.get("key") or ""
            title = p.get("title") or key.replace("_", " ")
            raw_excerpt = p.get("excerpt") or p.get("description") or ""

            # Strip searchmatch html tags
            clean_excerpt = re.sub(r"<[^>]+>", " ", raw_excerpt)
            clean_excerpt = html.unescape(clean_excerpt)
            clean_excerpt = " ".join(clean_excerpt.split())
            if not clean_excerpt:
                clean_excerpt = p.get("description") or title

            article_url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(key)}"
            thumb_info = p.get("thumbnail") or {}
            media_url = thumb_info.get("url") if isinstance(thumb_info, dict) else None
            if media_url and media_url.startswith("//"):
                media_url = f"https:{media_url}"

            items.append(
                SearchResultItem(
                    url=article_url,
                    title=title,
                    snippet=clean_excerpt,
                    score=85.0,
                    source=f"Wikipedia ({lang.upper()})",
                    media_url=media_url,
                    language=lang,
                    doc_type="web",
                    is_sponsored=False,
                    canonical_url=article_url,
                    source_type="académica",
                    content_type="artículo",
                    authors=["Comunidad Wikimedia"],
                    provider_origin="Wikipedia",
                    why_seen="Artículo enciclopédico de referencia abierta (Wikipedia). Sin cookies ni venta de perfiles.",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )
        return items
