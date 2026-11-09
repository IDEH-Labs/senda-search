# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Safe, robust HTML document extractor.

Parses web documents, extracts metadata, isolates indexable text by stripping
boilerplate/scripts/styles, computes cryptographic content hashes for deduplication,
and gathers normalized outgoing links.
"""

from dataclasses import dataclass, field
import hashlib
import re
from typing import Optional, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from senda.frontier.canonical import canonicalize_url, is_spider_trap


@dataclass(frozen=True)
class ExtractedImage:
    """Representation of an extracted image with Free Culture attribution."""
    image_url: str
    alt_text: str
    page_url: str
    page_title: str
    domain: str
    license: str = "Free Culture"


@dataclass(frozen=True)
class ExtractedDocument:
    """Cleaned representation of a parsed web document ready for indexing."""
    url: str
    title: str
    description: str
    language: str
    headings: str
    body_text: str
    content_hash: str
    text_density: float = 0.0
    doc_type: str = "web"  # "web", "news", "library"
    published_at: Optional[str] = None
    images: list[ExtractedImage] = field(default_factory=list)
    outgoing_links: list[str] = field(default_factory=list)


class DocumentExtractor:
    """Extracts search signals and outgoing links from HTML documents."""

    # Tags to decompose entirely to eliminate noise, scripts, and navigation clutter
    NON_CONTENT_TAGS = {
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "svg",
        "iframe",
        "object",
        "embed",
        "applet",
    }

    WHITESPACE_RE = re.compile(r"\s+")

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Collapse multiple spaces and clean text."""
        return cls.WHITESPACE_RE.sub(" ", text).strip()

    @classmethod
    def extract(cls, url: str, html_content: str) -> ExtractedDocument:
        """Parse HTML string and extract structured indexable fields."""
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract Language
        lang = ""
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = cls.clean_text(str(html_tag["lang"])).lower()
        if not lang:
            meta_lang = soup.find("meta", attrs={"http-equiv": re.compile(r"^content-language$", re.I)})
            if meta_lang and meta_lang.get("content"):
                lang = cls.clean_text(str(meta_lang["content"])).lower()

        # 2. Extract Title
        title = ""
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = cls.clean_text(title_tag.string)
        if not title:
            # Fall back to first h1
            h1_tag = soup.find("h1")
            if h1_tag:
                title = cls.clean_text(h1_tag.get_text())

        # 3. Extract Description
        description = ""
        meta_desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if meta_desc and meta_desc.get("content"):
            description = cls.clean_text(str(meta_desc["content"]))
        if not description:
            og_desc = soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
            if og_desc and og_desc.get("content"):
                description = cls.clean_text(str(og_desc["content"]))

        # 4. Extract Outgoing Links before decomposing elements
        outgoing_links_set: Set[str] = set()
        for a_tag in soup.find_all("a", href=True):
            # Check rel attribute for nofollow
            rel = a_tag.get("rel", [])
            if isinstance(rel, list):
                rel_set = {r.lower() for r in rel}
            else:
                rel_set = {r.lower() for r in rel.split()}

            if "nofollow" in rel_set:
                continue

            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
                continue

            # Resolve relative to base URL
            absolute_url = urljoin(url, raw_href)
            canonical = canonicalize_url(absolute_url)
            if canonical and canonical != url and not is_spider_trap(canonical):
                outgoing_links_set.add(canonical)

        # 5. Extract Headings (h1..h6) for relevance weighting
        headings_list: list[str] = []
        for h_tag in soup.find_all(re.compile(r"^h[1-6]$", re.I)):
            h_text = cls.clean_text(h_tag.get_text())
            if h_text:
                headings_list.append(h_text)
        headings_combined = " ".join(headings_list)

        # 6. Extract Images with Free Culture licensing hints before tag decomposition
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()

        extracted_images: list[ExtractedImage] = []
        seen_img_urls: Set[str] = set()

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
            resolved_img = urljoin(url, src.strip())
            if not (resolved_img.startswith("http://") or resolved_img.startswith("https://")):
                continue

            lower_img = resolved_img.lower()
            if lower_img.endswith(".ico") or "pixel" in lower_img or "tracking" in lower_img:
                continue
            if resolved_img in seen_img_urls:
                continue

            alt = cls.clean_text(img.get("alt") or img.get("title") or "")
            if len(alt) < 2 and not ("commons.wikimedia" in lower_img or "upload.wikimedia" in lower_img):
                continue

            # Free Culture license detection
            img_license = "Free Culture"
            if "wikimedia.org" in lower_img or "wikimedia.org" in domain or "wikipedia.org" in domain:
                img_license = "CC-BY-SA / Wikimedia Commons"
            elif "creativecommons.org" in html_content:
                img_license = "Creative Commons"

            seen_img_urls.add(resolved_img)
            extracted_images.append(
                ExtractedImage(
                    image_url=resolved_img,
                    alt_text=alt or title,
                    page_url=url,
                    page_title=title,
                    domain=domain,
                    license=img_license
                )
            )
            if len(extracted_images) >= 15:
                break

        # 7. Categorize Document (Web vs News vs Library/Encyclopedia)
        library_domains = (
            "wikipedia.org",
            "wikimedia.org",
            "archive.org",
            "gutenberg.org",
            "wikiversity.org",
            "wikibooks.org",
            "wikisource.org",
            "man7.org",
            "tldp.org",
        )
        is_gnu_manual = "gnu.org" in domain and ("/manual" in path or "/software" in path)
        if any(domain == ld or domain.endswith("." + ld) for ld in library_domains) or is_gnu_manual:
            doc_type = "library"
        elif (
            "/news" in path
            or "/blog" in path
            or "/noticias" in path
            or "/press" in path
            or "planet." in domain
            or "lwn.net" in domain
            or soup.find("meta", property="og:type", content="article")
        ):
            doc_type = "news"
        else:
            doc_type = "web"

        # 8. Extract publication date for news and articles
        published_at: Optional[str] = None
        date_meta = (
            soup.find("meta", property="article:published_time")
            or soup.find("meta", attrs={"name": "pubdate"})
            or soup.find("meta", attrs={"name": "date"})
            or soup.find("time", attrs={"datetime": True})
        )
        if date_meta:
            content_val = date_meta.get("content") or date_meta.get("datetime")
            if content_val and len(str(content_val)) >= 10:
                published_at = str(content_val)[:10]

        # 9. Decompose non-content tags for clean body text
        for tag_name in cls.NON_CONTENT_TAGS:
            for element in soup.find_all(tag_name):
                element.decompose()

        # Extract body text
        body = soup.find("body") or soup
        body_text = cls.clean_text(body.get_text(separator=" "))

        # 10. Content Hash (SHA-256) of title + body_text
        hash_input = f"{title}\n{body_text}".encode("utf-8")
        content_hash = hashlib.sha256(hash_input).hexdigest()

        # 11. Anti-SEO text density metric: text_length / max(raw_html_length, 1)
        raw_len = len(html_content)
        text_len = len(body_text)
        text_density = round(min(1.0, text_len / max(raw_len, 1)), 4)

        return ExtractedDocument(
            url=url,
            title=title,
            description=description,
            language=lang,
            headings=headings_combined,
            body_text=body_text,
            content_hash=content_hash,
            text_density=text_density,
            doc_type=doc_type,
            published_at=published_at,
            images=extracted_images,
            outgoing_links=sorted(outgoing_links_set),
        )
