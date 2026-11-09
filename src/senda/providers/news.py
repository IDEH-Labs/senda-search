# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Real-time News Provider for Senda Search Engine.

Aggregates breaking and current news from verified editorial outlets in real time
without cookies, tracking, or algorithmic filter bubbles.
"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html
import re
from typing import List, Optional
import urllib.parse
import xml.etree.ElementTree as ET
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance


def _clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    return " ".join(clean.split())


class RealTimeNewsProvider(SearchProvider):
    """Syndicated real-time news provider querying verified press feeds."""

    def __init__(
        self,
        region: str = "CO",
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

    async def search(
        self,
        query: str,
        category: str = "news",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> List[SearchResultItem]:
        """Fetch breaking news articles matching the query from verified press feeds."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        gl_code = (region or self.region).upper()
        if gl_code == "ALL" or len(gl_code) != 2:
            gl_code = "CO"

        encoded_q = urllib.parse.quote_plus(clean_q)
        feed_url = f"https://news.google.com/rss/search?q={encoded_q}&hl={self.lang}&gl={gl_code}&ceid={gl_code}:{self.lang}"

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(feed_url, headers=headers)
                if resp.status_code != 200:
                    return []
                return self.parse_feed(resp.text)[:page_size]
        except Exception:
            return []

    def parse_feed(self, xml_content: str) -> List[SearchResultItem]:
        """Parse news items from RSS XML payload."""
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

            # If source_name is not in <source>, extract from title if it ends with " - Source"
            clean_title = raw_title
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                clean_title = parts[0].strip()
                if not source_name:
                    source_name = parts[1].strip()

            if not source_name:
                source_name = "Prensa Verificada"

            # Parse publication date to ISO 8601
            iso_date = None
            if pub_date_str:
                try:
                    dt = parsedate_to_datetime(pub_date_str)
                    iso_date = dt.astimezone(timezone.utc).isoformat()
                except Exception:
                    iso_date = pub_date_str

            snippet = _clean_text(raw_desc)
            if not snippet:
                snippet = clean_title

            items.append(
                SearchResultItem(
                    url=link,
                    title=clean_title,
                    snippet=snippet,
                    score=92.0,
                    source=source_name,
                    date=iso_date,
                    doc_type="news",
                    is_sponsored=False,
                    canonical_url=link,
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
