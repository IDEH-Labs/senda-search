# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit and contract tests for News Syndication (RSS/Atom) and ClaimReview verification attribution."""

import json
from pathlib import Path
from unittest.mock import patch, AsyncMock
import httpx
import pytest

from senda.news.feed_reader import NewsFeedReader
from senda.news.claim_review import ClaimReviewParser, ClaimReviewRegistry, claim_review_registry
from senda.providers.base import SearchResultItem, VerificationItem

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# 1. Contract Test: Real News RSS Feed
def test_rss_feed_parsing_with_real_fixture():
    fixture_path = FIXTURES_DIR / "news_rss_feed.xml"
    assert fixture_path.exists(), "news_rss_feed.xml fixture must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    reader = NewsFeedReader()
    items = reader.parse_feed_xml(xml_content, feed_source_name="FSF News")

    assert len(items) > 0
    first = items[0]
    assert first.title != ""
    assert first.url.startswith("http")
    assert first.source == "FSF News"
    assert first.source_type == "noticia"
    assert first.doc_type == "news"
    assert first.content_type in ("noticia", "opinión")
    if first.published_date:
        assert len(first.published_date) == 10  # YYYY-MM-DD

    # Check provenance dictionary export
    prov = first.to_provenance_dict()
    assert prov["tipo_fuente"] == "noticia"
    assert prov["url_canónica"] == first.url
    assert prov["retractación"]["estado"] == "ninguna"


# 2. Test Opinion vs News Classification
def test_opinion_piece_classification():
    rss_opinion_sample = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Diario Independiente</title>
        <link>https://diario.example.org</link>
        <item>
          <title>Columna: Por qué la privacidad es el derecho fundamental del siglo XXI</title>
          <link>https://diario.example.org/opinion/privacidad-2026</link>
          <description>Reflexión editorial sobre la vigilancia algorítmica.</description>
          <pubDate>Mon, 09 Mar 2026 12:00:00 GMT</pubDate>
          <category>Opinión</category>
        </item>
        <item>
          <title>Aprobada nueva ley de protección de datos en el parlamento</title>
          <link>https://diario.example.org/noticias/ley-datos</link>
          <description>El congreso ratificó hoy la norma con mayoría calificada.</description>
          <pubDate>Mon, 09 Mar 2026 14:00:00 GMT</pubDate>
          <category>Nacional</category>
        </item>
      </channel>
    </rss>"""

    reader = NewsFeedReader()
    items = reader.parse_feed_xml(rss_opinion_sample, feed_source_name="Diario Independiente")

    assert len(items) == 2
    opinion_item = items[0]
    assert opinion_item.content_type == "opinión"
    assert "Opinión" in opinion_item.why_seen

    news_item = items[1]
    assert news_item.content_type == "noticia"
    assert "Noticia" in news_item.why_seen


# 3. Test Conditional Caching (ETag / If-Modified-Since -> HTTP 304)
@pytest.mark.asyncio
async def test_conditional_caching_etag_last_modified():
    feed_url = "https://diario.example.org/rss.xml"
    sample_xml = """<?xml version="1.0"?><rss version="2.0"><channel><title>News</title><item><title>Test</title><link>https://diario.example.org/1</link></item></channel></rss>"""

    reader = NewsFeedReader(min_fetch_interval_seconds=0.0)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # First request: 200 OK with ETag & Last-Modified
        mock_get.return_value = httpx.Response(
            200,
            text=sample_xml,
            headers={"etag": '"etag-abc-123"', "last-modified": "Mon, 09 Mar 2026 10:00:00 GMT"},
        )
        items1 = await reader.fetch_feed(feed_url)
        assert len(items1) == 1
        assert mock_get.call_count == 1

        # Second request: Server returns 304 Not Modified
        mock_get.return_value = httpx.Response(304)
        items2 = await reader.fetch_feed(feed_url)

        # Verifies conditional headers were sent
        sent_headers = mock_get.call_args[1].get("headers", {})
        assert sent_headers.get("If-None-Match") == '"etag-abc-123"'
        assert sent_headers.get("If-Modified-Since") == "Mon, 09 Mar 2026 10:00:00 GMT"

        # Cached items served without re-parsing
        assert len(items2) == 1
        assert items2[0].title == "Test"


# 4. Contract Test: Real ClaimReview JSON-LD Extraction
def test_claim_review_parsing_with_real_fixture():
    fixture_path = FIXTURES_DIR / "claim_review_sample.json"
    assert fixture_path.exists(), "claim_review_sample.json fixture must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    verifications = ClaimReviewParser.parse_json_ld(data)
    assert len(verifications) == 1

    v = verifications[0]
    assert v.verifier == "ColombiaCheck"
    assert v.attributed_verdict == "Falso"
    assert "colombiacheck.com" in v.url
    assert v.date == "2026-03-15"


# 5. Non-Negotiable Ethics Rule: Verdict MUST be attributed, NEVER Senda's own judgment
def test_claim_review_verdict_strictly_attributed_never_own_verdict():
    v = VerificationItem(
        verifier="Maldita.es",
        attributed_verdict="Bulo",
        url="https://maldita.es/malditobulo/ejemplo",
        date="2026-02-20",
    )

    formatted = ClaimReviewParser.format_attribution(v)

    # Must explicitly state who made the conclusion
    assert "Maldita.es concluyó" in formatted
    assert '"Bulo"' in formatted
    assert "2026-02-20" in formatted

    # Prohibited: Senda cannot proclaim truth/falsehood itself
    assert "Senda concluye" not in formatted
    assert "Senda verifica" not in formatted
    assert "Senda certifica" not in formatted


# 6. Test ClaimReviewRegistry and Decoration of SearchResultItem
def test_claim_review_registry_decorates_search_item():
    registry = ClaimReviewRegistry()
    target_url = "https://fake-news-portal.example.org/conspiracy-claim"

    verif = VerificationItem(
        verifier="Newtral",
        attributed_verdict="Falso",
        url="https://newtral.es/fact-check/123",
        date="2026-01-15",
    )
    registry.register(target_url, verif)

    item = SearchResultItem(
        title="Viral sensational headline",
        url=target_url,
        snippet="Sensational text claim.",
        source="Web Pública",
    )

    # Decorate item
    decorated = registry.decorate_search_item(item)
    assert len(decorated.verifications) == 1
    assert decorated.verifications[0].verifier == "Newtral"
    assert decorated.verifications[0].attributed_verdict == "Falso"

    # Export canonical provenance dict
    prov = decorated.to_provenance_dict()
    assert len(prov["verificaciones"]) == 1
    assert prov["verificaciones"][0]["verificador"] == "Newtral"
    assert prov["verificaciones"][0]["veredicto_atribuido"] == "Falso"


def test_atom_feed_parsing():
    sample_atom = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Atom News Example</title>
      <entry>
        <title>New Open Access Policy Announced</title>
        <link rel="alternate" href="https://news.example.org/entry-1" />
        <summary>Summary of the open access directive.</summary>
        <published>2026-04-01T10:00:00Z</published>
        <author><name>Editorial Team</name></author>
        <category term="Open Access" />
      </entry>
    </feed>"""

    reader = NewsFeedReader()
    items = reader.parse_feed_xml(sample_atom, feed_source_name="Atom Channel")

    assert len(items) == 1
    it = items[0]
    assert it.title == "New Open Access Policy Announced"
    assert it.url == "https://news.example.org/entry-1"
    assert it.authors == ["Editorial Team"]
    assert it.published_date == "2026-04-01"
    assert it.source == "Atom Channel"


def test_claim_review_graph_and_string_formats():
    # String JSON with @graph container
    graph_json = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ClaimReview",
                "datePublished": "2026-05-10",
                "url": "https://factcheck.org/claim-123",
                "author": {"name": "FactCheck.org"},
                "reviewRating": {"alternateName": "Misleading"}
            },
            {
                "@type": "WebPage",
                "url": "https://factcheck.org"
            }
        ]
    })

    items = ClaimReviewParser.parse_json_ld(graph_json)
    assert len(items) == 1
    assert items[0].verifier == "FactCheck.org"
    assert items[0].attributed_verdict == "Misleading"

    # Invalid input should return empty list gracefully
    assert ClaimReviewParser.parse_json_ld("{invalid json") == []
    assert ClaimReviewParser.parse_json_ld(123) == []


@pytest.mark.asyncio
async def test_news_feed_reader_interval_and_errors():
    reader = NewsFeedReader(min_fetch_interval_seconds=600.0)
    feed_url = "https://error-feed.example.org/rss.xml"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Non-200 status code
        mock_get.return_value = httpx.Response(500)
        items = await reader.fetch_feed(feed_url)
        assert items == []

        # Request error
        mock_get.side_effect = httpx.RequestError("DNS down")
        items_err = await reader.fetch_feed(feed_url)
        assert items_err == []
