# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for DocumentExtractor."""

from senda.extractor.parser import DocumentExtractor


def test_extractor_parses_metadata_and_body():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Senda Search Engine - Sovereign &amp; Free</title>
        <meta name="description" content="An independent ethical search engine.">
        <style>body { background: #fff; }</style>
        <script>console.log("tracking code should be removed");</script>
    </head>
    <body>
        <nav><a href="/home">Home</a> <a href="/about">About</a></nav>
        <header><h1>Welcome to Senda</h1></header>
        <main>
            <h2>Ethical Principles</h2>
            <p>Senda prioritizes user privacy and software freedom.</p>
            <p>Visit the <a href="https://fsf.org">Free Software Foundation</a> for more details.</p>
            <a href="https://example.com/spam" rel="nofollow">Spam Link</a>
        </main>
        <footer><p>&copy; 2026 IDEH Labs</p></footer>
    </body>
    </html>
    """

    doc = DocumentExtractor.extract("https://ideh.top/senda", html)

    assert doc.url == "https://ideh.top/senda"
    assert doc.title == "Senda Search Engine - Sovereign & Free"
    assert doc.description == "An independent ethical search engine."
    assert doc.language == "en"
    assert "Ethical Principles" in doc.headings
    assert "Senda prioritizes user privacy and software freedom." in doc.body_text

    # Verify script, style, nav, and footer were stripped from body_text
    assert "tracking code" not in doc.body_text
    assert "background: #fff" not in doc.body_text
    assert "Home About" not in doc.body_text
    assert "IDEH Labs" not in doc.body_text

    # Verify outgoing links (nofollow ignored, canonicalized)
    assert "https://fsf.org/" in doc.outgoing_links
    assert not any("spam" in link for link in doc.outgoing_links)
    assert doc.content_hash != ""


def test_extractor_fallback_title():
    html = """
    <html>
    <body>
        <h1>Headline Title</h1>
        <p>Some content</p>
    </body>
    </html>
    """
    doc = DocumentExtractor.extract("https://example.com", html)
    assert doc.title == "Headline Title"
    assert "Some content" in doc.body_text


def test_extractor_deduplication_hash():
    html1 = "<html><head><title>Test</title></head><body><p>Hello World</p></body></html>"
    html2 = "<html><head><title>Test</title></head><body><p>Hello   World</p><script>alert(1)</script></body></html>"

    doc1 = DocumentExtractor.extract("https://example.com/1", html1)
    doc2 = DocumentExtractor.extract("https://example.com/2", html2)

    # Cleaned body and title match, so content_hash must match
    assert doc1.content_hash == doc2.content_hash


def test_extractor_anti_seo_text_density():
    # 1. High density text page (minimal HTML, lots of prose)
    high_density_html = "<html><body><p>" + ("Deep philosophical analysis of sovereign software. " * 50) + "</p></body></html>"
    doc_high = DocumentExtractor.extract("https://example.com/essay", high_density_html)

    # 2. Low density / commercial bloated page (huge JS, CSS, divs, tiny text)
    low_density_html = "<html><head><style>" + ("div { color: red; }" * 100) + "</style></head><body>" + ("<div><span>" * 20) + "Buy now" + ("</span></div>" * 20) + "</body></html>"
    doc_low = DocumentExtractor.extract("https://example.com/shop", low_density_html)

    assert doc_high.text_density > 0.8
    assert doc_low.text_density < 0.1
    assert doc_high.text_density > doc_low.text_density


def test_extractor_verticals_and_images():
    html_library = """
    <html>
        <head>
            <title>Linux Kernel - Wikipedia</title>
            <meta name="date" content="2026-05-15">
        </head>
        <body>
            <h1>Linux Overview</h1>
            <p>The Linux kernel is free and open-source software.</p>
            <img src="/upload/tux.png" alt="Tux the penguin mascot" width="300" height="300">
        </body>
    </html>
    """
    doc_lib = DocumentExtractor.extract("https://en.wikipedia.org/wiki/Linux", html_library)

    assert doc_lib.doc_type == "library"
    assert doc_lib.published_at == "2026-05-15"
    assert len(doc_lib.images) == 1
    assert doc_lib.images[0].image_url == "https://en.wikipedia.org/upload/tux.png"
    assert doc_lib.images[0].alt_text == "Tux the penguin mascot"
    assert "Wikimedia" in doc_lib.images[0].license or "Free Culture" in doc_lib.images[0].license

    # News classification
    html_news = """
    <html>
        <head>
            <title>FSF Defends User Freedom</title>
            <meta property="article:published_time" content="2026-11-01T12:00:00Z">
        </head>
        <body><p>News dispatch on rights.</p></body>
    </html>
    """
    doc_news = DocumentExtractor.extract("https://fsf.org/news/sovereignty", html_news)
    assert doc_news.doc_type == "news"
    assert doc_news.published_at == "2026-11-01"
