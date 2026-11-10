# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Reader Mode
Zero-telemetry, distraction-free, ad-free article extraction engine.
Enforces strict anti-SSRF protections, HTML sanitization, and DNS pinning.
Works 100% server-side with zero JavaScript required.
Compatible with Tor Browser (Safest mode) and GNU LibreJS.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Optional
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel

from senda.crawler.fetcher import SafeFetcher, FetchError


class ReaderArticle(BaseModel):
    """Normalized sanitized article representation."""
    url: str
    domain: str
    title: str
    byline: Optional[str] = None
    published_date: Optional[str] = None
    reading_time_min: int = 1
    word_count: int = 0
    content_html: str
    excerpt: str = ""


class SovereignReader:
    """Extracts, cleans, and sanitizes web articles for distraction-free reading."""

    SAFE_TAGS = {
        "p", "h1", "h2", "h3", "h4", "h5", "h6",
        "blockquote", "ul", "ol", "li", "pre", "code",
        "b", "strong", "i", "em", "u", "mark", "small",
        "a", "img", "figure", "figcaption", "table", "thead",
        "tbody", "tr", "th", "td", "hr", "br"
    }

    DISCARD_SELECTORS = [
        "script", "style", "iframe", "object", "embed", "applet",
        "audio", "video", "source", "form", "input", "button", "select",
        "textarea", "svg", "canvas", "noscript",
        "header", "footer", "nav", "aside", "menu",
        '[role="navigation"]', '[role="banner"]', '[role="complementary"]',
        '[class*="cookie"]', '[id*="cookie"]',
        '[class*="popup"]', '[id*="popup"]',
        '[class*="modal"]', '[id*="modal"]',
        '[class*="banner"]', '[id*="banner"]',
        '[class*="advert"]', '[id*="advert"]',
        '[class*="social"]', '[id*="social"]',
        '[class*="share"]', '[id*="share"]',
        '[class*="newsletter"]', '[id*="newsletter"]',
        '[class*="sidebar"]', '[id*="sidebar"]',
        '[class*="comment"]', '[id*="comment"]',
        '[class*="related"]', '[id*="related"]',
    ]

    def __init__(self, fetcher: Optional[SafeFetcher] = None):
        self.fetcher = fetcher or SafeFetcher(user_agent="Senda-Sovereign-Reader/0.1 (+https://senda.ideh.top/about)")

    async def extract_url(self, target_url: str) -> ReaderArticle:
        """Fetch, sanitize, and extract article from target URL."""
        parsed = urllib.parse.urlparse(target_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("URL inválida: Debe comenzar con http:// o https://")

        # Fetch using SafeFetcher (guarantees anti-SSRF, DNS validation, socket pinning)
        doc = await self.fetcher.fetch(target_url)
        html_text = doc.content.decode("utf-8", errors="replace")
        return self.extract_html(html_text, base_url=target_url)

    def extract_html(self, html_text: str, base_url: str = "") -> ReaderArticle:
        """Parse, clean, and extract article content from raw HTML string."""
        soup = BeautifulSoup(html_text, "html.parser")
        domain = urllib.parse.urlparse(base_url).netloc if base_url else ""

        # 1. Extract metadata (Title, Byline, Date)
        title = self._extract_title(soup)
        byline = self._extract_byline(soup)
        pub_date = self._extract_date(soup)

        # 2. Strip junk elements
        for selector in self.DISCARD_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

        # 3. Locate primary article container
        article_el = self._find_primary_container(soup)
        if not article_el:
            article_el = soup.body or soup

        # 4. Sanitize tags and attributes
        cleaned_html, word_count = self._sanitize_content(article_el, base_url)
        reading_time = max(1, round(word_count / 200))

        # Plain text excerpt
        plain_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cleaned_html)).strip()
        excerpt = plain_text[:280] + ("..." if len(plain_text) > 280 else "")

        return ReaderArticle(
            url=base_url,
            domain=domain,
            title=title or "Artículo sin título",
            byline=byline,
            published_date=pub_date,
            reading_time_min=reading_time,
            word_count=word_count,
            content_html=cleaned_html,
            excerpt=excerpt,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return ""

    def _extract_byline(self, soup: BeautifulSoup) -> Optional[str]:
        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()
        author_tag = soup.find(attrs={"rel": "author"}) or soup.find(class_=re.compile(r"author|byline", re.I))
        if author_tag:
            text = author_tag.get_text(strip=True)
            if len(text) < 80:
                return text
        return None

    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        date_meta = (
            soup.find("meta", property="article:published_time")
            or soup.find("meta", attrs={"name": "date"})
            or soup.find("meta", attrs={"name": "pubdate"})
        )
        if date_meta and date_meta.get("content"):
            return date_meta["content"].strip()[:10]
        time_tag = soup.find("time")
        if time_tag:
            dt = time_tag.get("datetime") or time_tag.get_text(strip=True)
            if dt:
                return dt[:10]
        return None

    def _find_primary_container(self, soup: BeautifulSoup) -> Optional[Tag]:
        # Try semantic tags first
        candidates = soup.find_all(["article", "main"])
        if candidates:
            return max(candidates, key=lambda el: len(el.get_text()))

        role_main = soup.find(attrs={"role": "main"})
        if role_main:
            return role_main

        # Find div with highest density of paragraphs
        divs = soup.find_all("div")
        best_div = None
        best_p_count = 0
        for d in divs:
            p_len = sum(len(p.get_text()) for p in d.find_all("p", recursive=False))
            if p_len > best_p_count:
                best_p_count = p_len
                best_div = d

        return best_div

    def _sanitize_content(self, container: Tag, base_url: str) -> tuple[str, int]:
        sanitized_parts = []
        word_count = 0

        # Traverse all descendant tags
        for el in container.find_all(True):
            if not isinstance(el, Tag):
                continue
            name = el.name.lower()
            if name not in self.SAFE_TAGS:
                el.unwrap()
                continue

            # Strip all event handlers and styling
            attrs_to_remove = [k for k in el.attrs if k.startswith("on") or k in ("style", "id", "class")]
            for a in attrs_to_remove:
                del el[a]

            # Enforce safe href and links
            if name == "a":
                href = el.get("href", "")
                if href.startswith("javascript:") or href.startswith("data:"):
                    el.unwrap()
                    continue
                if base_url and not href.startswith(("http://", "https://", "mailto:")):
                    el["href"] = urllib.parse.urljoin(base_url, href)
                el["rel"] = "noopener noreferrer nofollow"
                el["target"] = "_blank"

            # Enforce safe image sources
            elif name == "img":
                src = el.get("src", "")
                if not src or src.startswith("javascript:"):
                    el.decompose()
                    continue
                if base_url and not src.startswith(("http://", "https://")):
                    el["src"] = urllib.parse.urljoin(base_url, src)
                el["loading"] = "lazy"
                el["referrerpolicy"] = "no-referrer"

        # Collect paragraphs, headings, blockquotes, lists
        meaningful_tags = container.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "ul", "ol", "pre", "figure"])
        if meaningful_tags:
            for tag in meaningful_tags:
                txt = tag.get_text(strip=True)
                if not txt and not tag.find("img"):
                    continue
                word_count += len(txt.split())
                sanitized_parts.append(str(tag))
        else:
            txt = container.get_text(strip=True)
            word_count += len(txt.split())
            sanitized_parts.append(f"<p>{txt}</p>")

        return "\n".join(sanitized_parts), word_count
