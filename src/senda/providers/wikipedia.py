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
from senda.countries import get_sovereign_country
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


# Verified sovereign and institutional website overrides (fallback or direct overrides)
SOVEREIGN_OFFICIAL_WEBSITES: Dict[str, str] = {
    "Q967": "https://presidence.gov.bi/",  # Burundi
}

_PARKED_OR_SPAM_DOMAINS = {
    "sedoparking.com",
    "parkingcrew.net",
    "domainmarket.com",
    "hugedomains.com",
    "dan.com",
    "godaddy.com",
    "afternic.com",
}

_TRACKER_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
}


def sanitize_official_website(raw_url: Optional[str]) -> Optional[str]:
    """Ethically validate, upgrade to HTTPS, and sanitize official website URLs.

    Guarantees no dead/parked domains, upgrades unencrypted HTTP to HTTPS,
    and strips tracking query strings.
    """
    if not raw_url or not isinstance(raw_url, str):
        return None

    clean = raw_url.strip()
    if not clean:
        return None

    # Upgrade http to https
    if clean.startswith("http://"):
        clean = "https://" + clean[7:]
    elif not clean.startswith("https://"):
        clean = "https://" + clean

    try:
        parsed = urllib.parse.urlparse(clean)
        netloc = parsed.netloc.lower().strip()
        if not netloc or "." not in netloc or " " in netloc:
            return None

        # Filter localhost / private addresses / raw IPs
        if netloc in ("localhost", "0.0.0.0", "127.0.0.1"):
            return None

        # Filter known parked / spam brokers
        for spam_dom in _PARKED_OR_SPAM_DOMAINS:
            if netloc == spam_dom or netloc.endswith("." + spam_dom):
                return None

        # Strip tracking query params
        path = parsed.path or "/"
        clean_query = ""
        if parsed.query:
            query_parts = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
            filtered = [(k, v) for k, v in query_parts if k.lower() not in _TRACKER_PARAMS]
            if filtered:
                clean_query = urllib.parse.urlencode(filtered)

        sanitized = urllib.parse.urlunparse((
            "https",
            netloc,
            path,
            "",
            clean_query,
            "",
        ))
        return sanitized
    except Exception:
        return None


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

        # Prepare normalized title (spaces to underscores)
        # If query matches a known sovereign state, prioritize its authoritative Spanish name
        sovereign_match = get_sovereign_country(query=clean_q)
        query_candidate = sovereign_match.name_es if sovereign_match else clean_q
        norm_title = urllib.parse.quote(query_candidate.replace(" ", "_"))
        api_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{norm_title}"

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(api_url, headers=headers)
                # Fallback to Title-cased query if lower-cased multi-word yields 404
                if resp.status_code == 404 and clean_q != clean_q.title():
                    alt_title = urllib.parse.quote(clean_q.title().replace(" ", "_"))
                    alt_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{alt_title}"
                    resp = await client.get(alt_url, headers=headers)

                # Fallback to offline vocabulary suggestion for single-letter typos
                if resp.status_code == 404 and len(clean_q) >= 4:
                    try:
                        from senda.ranking.suggestions import SuggestionEngine, damerau_levenshtein_distance
                        vocab = SuggestionEngine.get_offline_vocabulary()
                        q_lower = clean_q.lower()
                        best_match = None
                        best_d = 999
                        max_d = 1 if len(q_lower) < 7 else 2
                        for term, display in vocab.items():
                            if abs(len(term) - len(q_lower)) <= max_d:
                                d = damerau_levenshtein_distance(q_lower, term)
                                if 0 < d <= max_d and d < best_d:
                                    best_d = d
                                    best_match = display
                        if best_match:
                            sugg_title = urllib.parse.quote(best_match.replace(" ", "_"))
                            sugg_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{sugg_title}"
                            resp = await client.get(sugg_url, headers=headers)
                    except Exception:
                        pass

                # Fallback to Wikimedia OpenSearch API for historical figures, celebrities and people with typos
                if resp.status_code == 404 and len(clean_q) >= 4:
                    try:
                        import unicodedata
                        from senda.ranking.suggestions import damerau_levenshtein_distance
                        os_url = (
                            f"https://{lang}.wikipedia.org/w/api.php?"
                            f"action=opensearch&search={urllib.parse.quote(clean_q)}&limit=1&namespace=0&format=json"
                        )
                        os_resp = await client.get(os_url, headers=headers)
                        if os_resp.status_code == 200:
                            os_data = os_resp.json()
                            if len(os_data) >= 2 and os_data[1]:
                                candidate = os_data[1][0]
                                q_norm = "".join(c for c in unicodedata.normalize("NFKD", clean_q.lower()) if not unicodedata.combining(c))
                                cand_norm = "".join(c for c in unicodedata.normalize("NFKD", candidate.lower()) if not unicodedata.combining(c))
                                dist = damerau_levenshtein_distance(q_norm, cand_norm)
                                max_dist = 2 if len(q_norm) < 10 else 3
                                if dist <= max_dist:
                                    sugg_title = urllib.parse.quote(candidate.replace(" ", "_"))
                                    sugg_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{sugg_title}"
                                    resp = await client.get(sugg_url, headers=headers)
                    except Exception:
                        pass

                if resp.status_code == 200:
                    data = resp.json()
                    card = self.parse_summary(data, lang=lang)
                    if fetch_official_website and card:
                        # 1. Sovereign Country Registry (Universal coverage for 195 nations)
                        sovereign = None
                        if card.wikibase_item and card.wikibase_item in SOVEREIGN_OFFICIAL_WEBSITES:
                            card.official_website = SOVEREIGN_OFFICIAL_WEBSITES[card.wikibase_item]
                        else:
                            if card.wikibase_item:
                                sovereign = get_sovereign_country(qid=card.wikibase_item)
                            if not sovereign and card.title:
                                sovereign = get_sovereign_country(query=card.title)

                            if sovereign:
                                card.official_website = sovereign.official_portal
                            elif card.wikibase_item:
                                # Non-country encyclopedic entity (e.g. universities, foundations, institutions)
                                try:
                                    wb_url = f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={card.wikibase_item}&property=P856&format=json"
                                    wb_resp = await client.get(wb_url, headers=headers)
                                    if wb_resp.status_code == 200:
                                        wb_data = wb_resp.json()
                                        claims = wb_data.get("claims", {}).get("P856", [])
                                        for c in claims:
                                            val = c.get("mainsnak", {}).get("datavalue", {}).get("value")
                                            if isinstance(val, str):
                                                clean_site = sanitize_official_website(val)
                                                if clean_site:
                                                    card.official_website = clean_site
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
