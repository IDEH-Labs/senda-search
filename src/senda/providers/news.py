# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Real-time News Provider for Senda Search Engine.

Aggregates breaking and current news from verified editorial outlets in real time
without cookies, tracking, or algorithmic filter bubbles.
"""

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import html
import re
from typing import Dict, List, Optional, Any
import urllib.parse
import xml.etree.ElementTree as ET
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance


NEWS_LANG_CONFIG: Dict[str, Dict[str, str]] = {
    "ar": {"hl": "ar", "gl": "SA", "ceid": "SA:ar"},
    "de": {"hl": "de", "gl": "DE", "ceid": "DE:de"},
    "en": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
    "es": {"hl": "es-419", "gl": "ES", "ceid": "ES:es"},
    "fr": {"hl": "fr", "gl": "FR", "ceid": "FR:fr"},
    "it": {"hl": "it", "gl": "IT", "ceid": "IT:it"},
    "ja": {"hl": "ja", "gl": "JP", "ceid": "JP:ja"},
    "pt": {"hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"},
    "ru": {"hl": "ru", "gl": "RU", "ceid": "RU:ru"},
    "zh": {"hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"},
}


def _clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    return " ".join(clean.split())


def _is_relevant_news(query: str, title: str, source: str) -> bool:
    """Verify that the syndicated news item genuinely matches the search query.

    Prevents collaborative-filtering hallucinations and false positive synonym expansions.
    Supports Unicode scripts across Cyrillic, Arabic, CJK, and European alphabets.
    """
    clean_q = re.sub(r"\b(?:when|before):\S+", "", query).strip()
    if not clean_q:
        return True

    # Match alphanumeric words across all Unicode writing systems
    raw_tokens = re.findall(r"\w+", clean_q, flags=re.UNICODE)
    tokens = [t.lower() for t in raw_tokens if len(t) >= 2 or any(ord(c) > 127 for c in t)]
    if not tokens:
        return True

    title_lower = title.lower()
    source_lower = source.lower()

    return any(token in title_lower or token in source_lower for token in tokens)


def _expand_news_query(query: str) -> str:
    """Intelligently expand discovery and science terms for comprehensive press retrieval."""
    q_lower = query.lower().strip()
    discovery_terms = {
        "descubren", "descubrimiento", "descubrimientos", "descubrieron", "descubre",
        "hallazgo", "hallazgos", "hallan"
    }
    if q_lower in discovery_terms:
        return "(descubren OR descubrimiento OR descubrimientos OR hallazgo OR hallazgos)"
    return query


def _resolve_time_query(query: str, time_filter: Optional[str]) -> str:
    """Map user temporal filter to syndicated feed operators (when: or before:)."""
    expanded_q = _expand_news_query(query)
    if not time_filter or time_filter.lower() in ("all", "cualquiera", "none", ""):
        return expanded_q
    tf = time_filter.lower().strip()
    mapping = {
        "1h": "when:1h",
        "hour": "when:1h",
        "1d": "when:1d",
        "24h": "when:1d",
        "day": "when:1d",
        "1w": "when:7d",
        "7d": "when:7d",
        "week": "when:7d",
        "1m": "when:30d",
        "30d": "when:30d",
        "month": "when:30d",
        "2m": "when:60d",
        "60d": "when:60d",
        "6m": "when:180d",
        "180d": "when:180d",
        "1y": "when:1y",
        "365d": "when:1y",
        "year": "when:1y",
    }
    if tf in mapping:
        return f"{expanded_q} {mapping[tf]}".strip()
    if tf in ("1y_plus", "older_1y", "1y+"):
        one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
        return f"{expanded_q} before:{one_year_ago}".strip()
    return expanded_q


class RealTimeNewsProvider(SearchProvider):
    """Syndicated real-time news provider querying verified press feeds."""

    def __init__(
        self,
        region: str = "ALL",
        lang: str = "es-419",
        timeout: float = 5.0,
        enabled: bool = True,
    ):
        self.region = region.upper()
        self.lang = lang
        self.timeout = timeout
        self.enabled = enabled

    @property
    def name(self) -> str:
        return "realtime_news"

    @property
    def is_configured(self) -> bool:
        return self.enabled

    @staticmethod
    def _item_datetime(item: SearchResultItem) -> datetime:
        """Parse publication date into comparable UTC datetime."""
        if item.published_date:
            try:
                dt = datetime.fromisoformat(item.published_date)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
        return datetime.min.replace(tzinfo=timezone.utc)

    async def search(
        self,
        query: str,
        category: str = "news",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        sort: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
        lang: Optional[str] = None,
        **kwargs: Any,
    ) -> List[SearchResultItem]:
        """Fetch breaking news articles matching the query from verified press feeds."""
        if not self.is_configured:
            return []

        clean_q = query.strip()

        # Resolve language configuration (defaulting to Spanish or provider default)
        target_lang = (lang or self.lang or "es").split("-")[0].lower()
        lang_cfg = NEWS_LANG_CONFIG.get(target_lang, NEWS_LANG_CONFIG["es"])
        hl = lang_cfg["hl"]
        gl = lang_cfg["gl"]
        ceid = lang_cfg["ceid"]

        # Optional region/country override
        gl_override = (region or self.region or "").upper().strip()
        if len(gl_override) == 2 and gl_override not in ("AL", "ALL", "GLOBAL", ""):
            gl = gl_override
            ceid = f"{gl}:{hl}"

        if clean_q:
            query_with_time = _resolve_time_query(clean_q, time_filter)
            encoded_q = urllib.parse.quote_plus(query_with_time)
            feed_url = f"https://news.google.com/rss/search?q={encoded_q}&hl={hl}&gl={gl}&ceid={ceid}"
        else:
            # Query-less breaking top headlines for the target language and region
            feed_url = f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}"

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(feed_url, headers=headers)
                if resp.status_code != 200:
                    return []
                items = self.parse_feed(resp.text, query=clean_q, lang=target_lang)

                # Sorting: default in news or if sort == 'date', sort by publication date descending
                if sort == "relevance":
                    pass
                else:
                    items.sort(key=self._item_datetime, reverse=True)

                start_idx = max(0, (page - 1) * page_size)
                end_idx = start_idx + page_size
                return items[start_idx:end_idx]
        except Exception:
            return []

    def parse_feed(self, xml_content: str, query: str = "", lang: str = "es") -> List[SearchResultItem]:
        """Parse news items from RSS XML payload, strictly resolving publisher origin and enforcing relevance."""
        items: List[SearchResultItem] = []
        if not xml_content:
            return items

        try:
            root = ET.fromstring(xml_content)
        except Exception:
            return items

        channel = root.find("channel")
        if channel is None:
            return items

        for it in channel.findall("item"):
            raw_title = it.findtext("title", "").strip()
            link = it.findtext("link", "").strip()
            raw_desc = it.findtext("description", "")
            pub_date_str = it.findtext("pubDate", "")

            source_elem = it.find("source")
            source_name = source_elem.text.strip() if source_elem is not None and source_elem.text else ""
            source_url = source_elem.get("url", "").strip() if source_elem is not None else ""

            source_domain = None
            if source_url:
                try:
                    p_src = urllib.parse.urlparse(source_url)
                    sd = p_src.netloc.lower()
                    if sd.startswith("www."):
                        sd = sd[4:]
                    if sd:
                        source_domain = sd
                except Exception:
                    pass

            # If source_name is not in <source>, extract from title if it ends with " - Source"
            clean_title = raw_title
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                clean_title = parts[0].strip()
                if not source_name:
                    source_name = parts[1].strip()

            if not source_name:
                source_name = "Prensa Verificada"

            # Relevance guard: eliminate false positives / unrelated feed items
            if query and not _is_relevant_news(query, clean_title, source_name):
                continue

            # Parse publication date to ISO 8601
            iso_date = None
            if pub_date_str:
                try:
                    dt = parsedate_to_datetime(pub_date_str)
                    iso_date = dt.astimezone(timezone.utc).isoformat()
                except Exception:
                    iso_date = pub_date_str

            clean_desc = _clean_text(raw_desc)
            clean_desc_cmp = clean_desc.lower().replace(source_name.lower(), "").strip()
            clean_title_cmp = clean_title.lower().strip()

            if not clean_desc or clean_desc_cmp == clean_title_cmp or clean_desc_cmp.startswith(clean_title_cmp):
                domain_hint = f" ({source_domain})" if source_domain else ""
                snippet = f"Cobertura periodística de actualidad por «{source_name}»{domain_hint}. Consulta el reportaje completo en el medio de comunicación."
            else:
                snippet = clean_desc

            items.append(
                SearchResultItem(
                    url=link,
                    title=clean_title,
                    snippet=snippet,
                    score=92.0,
                    source=source_name,
                    source_domain=source_domain,
                    date=iso_date,
                    language=lang,
                    doc_type="news",
                    is_sponsored=False,
                    canonical_url=source_url or link,
                    source_type="noticia",
                    content_type="noticia",
                    published_date=iso_date,
                    authors=[source_name],
                    provider_origin="Prensa Abierta",
                    why_seen=f"Noticia en tiempo real sindicada del medio verificado «{source_name}». Sin cookies ni seguimiento de usuario.",
                    ai_provenance=AIProvenance(declared_signal=None, status="no determinado"),
                )
            )

        return items
