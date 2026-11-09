# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Ethical RSS/Atom News Feed Reader for Senda.

Features:
- Identifiable institutional User-Agent with contact and policy links.
- Conditional HTTP caching using ETag (If-None-Match) and Last-Modified (If-Modified-Since).
- Parsing of RSS 2.0 and Atom 1.0 feeds.
- Transparent classification of news vs. opinion pieces.
- Conversion to Senda Verifiable Provenance SearchResultItem.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import email.utils
import logging
import re
import time
from typing import Optional, List, Dict, Tuple
import urllib.parse
import xml.etree.ElementTree as ET
import httpx

from senda.config import settings
from senda.providers.base import SearchResultItem

logger = logging.getLogger(__name__)

# XML Namespaces
ATOM_NS = "http://www.w3.org/2005/Atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"

OPINION_KEYWORDS = {"opinion", "opinión", "editorial", "tribuna", "columna", "columnista", "punto de vista", "commentary"}


@dataclass
class FeedCacheEntry:
    """In-memory conditional cache entry for an external news feed."""
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    items: List[SearchResultItem] = field(default_factory=list)
    last_fetched_monotonic: float = 0.0


@dataclass
class FeedItem:
    """Normalized article extracted from an RSS or Atom feed."""
    title: str
    url: str
    snippet: str
    published_date: Optional[str]
    author: Optional[str]
    categories: List[str]
    content_type: str  # "noticia" | "opinión"


class NewsFeedReader:
    """Ethical, polite news syndication reader with conditional caching."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        email_contact: Optional[str] = None,
        min_fetch_interval_seconds: float = 300.0,  # 5 minutes courtesy interval
    ):
        self.email_contact = email_contact or getattr(settings, "CONTACT_EMAIL", "contact@ideh.top")
        self.user_agent = user_agent or f"SendaNews/1.0 (+https://ideh.top/senda-search; mailto:{self.email_contact})"
        self.min_fetch_interval_seconds = min_fetch_interval_seconds
        self._cache: Dict[str, FeedCacheEntry] = {}

    def parse_feed_xml(self, xml_text: str, feed_source_name: str = "Medio Sindicado") -> List[SearchResultItem]:
        """Parse RSS or Atom XML and return normalized SearchResultItem objects."""
        items: List[SearchResultItem] = []
        try:
            root = ET.fromstring(xml_text)
        except Exception as e:
            logger.warning(f"NewsFeedReader: Error al parsear XML de feed: {e}")
            return []

        tag = root.tag.lower()
        if "feed" in tag:
            # Atom 1.0 feed
            feed_items = self._parse_atom(root)
        else:
            # RSS 2.0 / RSS 1.0 / RDF feed
            feed_items = self._parse_rss(root)

        for fi in feed_items:
            domain = urllib.parse.urlparse(fi.url).netloc
            author_list = [fi.author] if fi.author else []

            why = (
                f"Artículo sindicado mediante feed RSS/Atom oficial de {feed_source_name} ({domain}). "
                f"Clasificación editorial: {fi.content_type.capitalize()}. Consulta directa y sin intermediarios."
            )

            item = SearchResultItem(
                title=fi.title,
                url=fi.url,
                canonical_url=fi.url,
                snippet=fi.snippet,
                source=feed_source_name,
                date=fi.published_date[:4] if fi.published_date else None,
                doc_type="news",
                source_type="noticia",
                content_type=fi.content_type,
                published_date=fi.published_date,
                authors=author_list,
                score=30.0,
                why_seen=why,
                provider_origin="RSS/Atom Sindicado",
            )
            items.append(item)

        return items

    def _parse_rss(self, root: ET.Element) -> List[FeedItem]:
        """Extract articles from RSS 2.0 / 1.0 / RDF tree (namespace-agnostic)."""
        items: List[FeedItem] = []
        # Find all <item> tags regardless of XML namespace
        items_nodes = [elem for elem in root.iter() if elem.tag.lower().endswith("item")]

        for node in items_nodes:
            # Title
            title_node = next((c for c in node if c.tag.lower().endswith("title")), None)
            title = title_node.text.strip() if (title_node is not None and title_node.text) else ""
            if not title:
                continue

            # Link
            link_node = next((c for c in node if c.tag.lower().endswith("link")), None)
            url = ""
            if link_node is not None:
                url = (link_node.text or link_node.attrib.get("href") or "").strip()
            if not url:
                # Check rdf:about attribute
                for attr_k, attr_v in node.attrib.items():
                    if attr_k.lower().endswith("about"):
                        url = attr_v.strip()
                        break
            if not url:
                continue

            # Description / Snippet
            desc_node = next((c for c in node if c.tag.lower().endswith("description") or c.tag.lower().endswith("encoded")), None)
            raw_desc = desc_node.text if (desc_node is not None and desc_node.text) else ""
            clean_snippet = self._strip_html(raw_desc)[:280].strip()

            # Date (pubDate, dc:date, or date)
            date_node = next((c for c in node if c.tag.lower().endswith("pubdate") or c.tag.lower().endswith("date")), None)
            pub_str = date_node.text.strip() if (date_node is not None and date_node.text) else None
            iso_date = self._parse_date_to_iso(pub_str)

            # Author (creator or author)
            author_node = next((c for c in node if c.tag.lower().endswith("creator") or c.tag.lower().endswith("author")), None)
            author = author_node.text.strip() if (author_node is not None and author_node.text) else None

            # Categories or dc:type
            categories = [
                c.text.strip()
                for c in node
                if (c.tag.lower().endswith("category") or c.tag.lower().endswith("type")) and c.text
            ]

            content_type = self._classify_content_type(title, url, categories)

            items.append(
                FeedItem(
                    title=title,
                    url=url,
                    snippet=clean_snippet or f"Noticia publicada en {urllib.parse.urlparse(url).netloc}",
                    published_date=iso_date,
                    author=author,
                    categories=categories,
                    content_type=content_type,
                )
            )

        return items

    def _parse_atom(self, root: ET.Element) -> List[FeedItem]:
        """Extract articles from Atom 1.0 tree (namespace-agnostic)."""
        items: List[FeedItem] = []
        entries = [elem for elem in root.iter() if elem.tag.lower().endswith("entry")]

        for entry in entries:
            # Title
            title_node = next((c for c in entry if c.tag.lower().endswith("title")), None)
            title = title_node.text.strip() if (title_node is not None and title_node.text) else ""
            if not title:
                continue

            # Link: prefer rel="alternate" or first href
            url = ""
            links = [c for c in entry if c.tag.lower().endswith("link")]
            for lnk in links:
                rel = lnk.attrib.get("rel", "alternate").lower()
                href = lnk.attrib.get("href", "").strip()
                if rel == "alternate" and href:
                    url = href
                    break
                elif href and not url:
                    url = href
            if not url:
                continue

            # Summary / Content
            summary_node = next((c for c in entry if c.tag.lower().endswith("summary") or c.tag.lower().endswith("content")), None)
            raw_summary = summary_node.text if (summary_node is not None and summary_node.text) else ""
            clean_snippet = self._strip_html(raw_summary)[:280].strip()

            # Date: published or updated
            date_node = next((c for c in entry if c.tag.lower().endswith("published") or c.tag.lower().endswith("updated")), None)
            date_str = date_node.text.strip() if (date_node is not None and date_node.text) else None
            iso_date = date_str[:10] if date_str and len(date_str) >= 10 else None

            # Author
            author = None
            author_container = next((c for c in entry if c.tag.lower().endswith("author")), None)
            if author_container is not None:
                name_node = next((c for c in author_container if c.tag.lower().endswith("name")), None)
                if name_node is not None and name_node.text:
                    author = name_node.text.strip()

            # Categories
            categories = [
                c.attrib.get("term", "").strip()
                for c in entry
                if c.tag.lower().endswith("category") and c.attrib.get("term")
            ]

            content_type = self._classify_content_type(title, url, categories)

            items.append(
                FeedItem(
                    title=title,
                    url=url,
                    snippet=clean_snippet or f"Artículo publicado en {urllib.parse.urlparse(url).netloc}",
                    published_date=iso_date,
                    author=author,
                    categories=categories,
                    content_type=content_type,
                )
            )

        return items

    @staticmethod
    def _strip_html(html_text: str) -> str:
        """Strip HTML tags cleanly without importing heavy parsers."""
        if not html_text:
            return ""
        clean = re.sub(r"<[^>]+>", " ", html_text)
        return " ".join(clean.split())

    @staticmethod
    def _parse_date_to_iso(date_str: Optional[str]) -> Optional[str]:
        """Convert RFC 822/2822 date into ISO 8601 string (YYYY-MM-DD)."""
        if not date_str:
            return None
        try:
            parsed_tuple = email.utils.parsedate_to_datetime(date_str)
            return parsed_tuple.strftime("%Y-%m-%d")
        except Exception:
            return date_str[:10] if len(date_str) >= 10 else None

    @staticmethod
    def _classify_content_type(title: str, url: str, categories: List[str]) -> str:
        """Distinguish opinion/editorial from reporting."""
        combined = f"{title} {url} {' '.join(categories)}".lower()
        for kw in OPINION_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", combined):
                return "opinión"
        return "noticia"

    async def fetch_feed(self, feed_url: str, source_name: str = "Medio Sindicado") -> List[SearchResultItem]:
        """Fetch feed with conditional caching (ETag / If-Modified-Since)."""
        now = time.monotonic()
        entry = self._cache.get(feed_url, FeedCacheEntry())

        # Respect local courtesy interval
        if entry.items and (now - entry.last_fetched_monotonic < self.min_fetch_interval_seconds):
            return entry.items

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        }
        if entry.etag:
            headers["If-None-Match"] = entry.etag
        if entry.last_modified:
            headers["If-Modified-Since"] = entry.last_modified

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(feed_url, headers=headers)

                # HTTP 304 Not Modified: return cached items without parsing
                if resp.status_code == 304:
                    entry.last_fetched_monotonic = now
                    return entry.items

                if resp.status_code != 200:
                    logger.warning(f"NewsFeedReader: Feed {feed_url} devolvió HTTP {resp.status_code}.")
                    return entry.items

                xml_text = resp.text
                new_etag = resp.headers.get("etag")
                new_last_mod = resp.headers.get("last-modified")

                items = self.parse_feed_xml(xml_text, feed_source_name=source_name)

                entry.etag = new_etag
                entry.last_modified = new_last_mod
                entry.items = items
                entry.last_fetched_monotonic = now
                self._cache[feed_url] = entry
                return items

        except Exception as e:
            logger.warning(f"NewsFeedReader: Error al recuperar feed {feed_url}: {e}")
            return entry.items
