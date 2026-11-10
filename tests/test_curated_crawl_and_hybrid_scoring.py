# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit and integration tests for curated seeds, meta robots, canonical deduplication and honest coverage."""

from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest

from senda.crawler.runner import CrawlerRunner
from senda.crawler.fetcher import FetchedDocument
from senda.crawler.seeds import (
    CURATED_SEEDS,
    get_curated_seed_urls,
    get_seeds_by_country,
    get_government_seeds,
)
from senda.extractor.parser import DocumentExtractor
from senda.indexer.storage import StorageEngine
from senda.security.threat_guard import threat_guard, ThreatCategory


@pytest.fixture
def temp_storage(tmp_path):
    return StorageEngine(db_path=tmp_path / "test_crawl_hybrid.db")


# 1. Test Meta Robots (noindex and nofollow)
def test_meta_robots_noindex_and_nofollow_respected():
    html_noindex_nofollow = """<!DOCTYPE html>
    <html>
      <head>
        <title>Private Draft Document</title>
        <meta name="robots" content="noindex, nofollow">
        <link rel="canonical" href="https://example.org/draft">
      </head>
      <body>
        <h1>Internal notes</h1>
        <p>This draft must not appear in search results.</p>
        <a href="https://example.org/secret-link">Secret Link</a>
      </body>
    </html>"""

    doc = DocumentExtractor.extract("https://example.org/draft", html_noindex_nofollow)
    assert doc.is_indexable is False
    assert len(doc.outgoing_links) == 0
    assert doc.canonical_url == "https://example.org/draft"


@pytest.mark.asyncio
async def test_crawler_runner_skips_noindex_documents(temp_storage):
    """Verify that CrawlerRunner respects meta robots noindex and skips inserting into database."""
    runner = CrawlerRunner(storage=temp_storage)
    target_url = "https://example.org/unindexable-page"

    html_content = """<!DOCTYPE html><html><head><meta name="robots" content="noindex"><title>No Index</title></head><body>Content</body></html>"""
    mock_doc = FetchedDocument(
        url=target_url,
        status_code=200,
        headers={"content-type": "text/html"},
        content=html_content.encode("utf-8"),
        text=html_content,
        content_type="text/html",
        encoding="utf-8",
    )

    with patch.object(runner.fetcher, "fetch", new_callable=AsyncMock, return_value=mock_doc):
        # Allow in robots.txt so it reaches document fetching
        runner.robots_manager.register_empty_policy("example.org")
        indexed = await runner.crawl_seed(target_url, max_pages=1)

        # Must not be indexed due to meta robots noindex
        assert indexed == 0
        stats = temp_storage.get_stats()
        assert stats["total_documents"] == 0


# 2. Test Canonical URL Extraction & Deduplication
def test_canonical_url_extraction_and_deduplication(temp_storage):
    canonical_target = "https://example.org/official-article"
    html_tracked = f"""<!DOCTYPE html>
    <html>
      <head>
        <title>Official Article</title>
        <link rel="canonical" href="{canonical_target}">
        <meta name="author" content="Dra. Valentina Gómez">
      </head>
      <body>
        <h1>Official Research</h1>
        <p>Document content discussing open science methodologies.</p>
        <a href="https://doi.org/10.1234/test.doi">DOI Citation</a>
        <a href="https://datos.gov.co/dataset/999">Government Open Data</a>
      </body>
    </html>"""

    doc_tracked = DocumentExtractor.extract("https://example.org/official-article?utm_source=twitter&tracker=123", html_tracked)
    assert doc_tracked.canonical_url == canonical_target
    assert doc_tracked.is_indexable is True
    assert doc_tracked.authors == ["Dra. Valentina Gómez"]
    # Check primary citations detection (.gov and doi.org)
    assert len(doc_tracked.primary_links) == 2
    assert any("doi.org" in lnk for lnk in doc_tracked.primary_links)
    assert any("datos.gov.co" in lnk for lnk in doc_tracked.primary_links)

    # First insert with tracking URL
    inserted1 = temp_storage.upsert_document(doc_tracked)
    assert inserted1 is True
    assert temp_storage.get_stats()["total_documents"] == 1

    # Second insert with clean canonical URL and identical content hash
    doc_canonical = DocumentExtractor.extract(canonical_target, html_tracked)
    inserted2 = temp_storage.upsert_document(doc_canonical)

    # Must be deduplicated (False returned, total count unchanged)
    assert inserted2 is False
    assert temp_storage.get_stats()["total_documents"] == 1


# 3. Test Curated Seeds Directory
def test_curated_seeds_integrity():
    assert len(CURATED_SEEDS) >= 10

    urls_all = get_curated_seed_urls()
    assert len(urls_all) == len(CURATED_SEEDS)

    for seed in CURATED_SEEDS:
        assert seed.id.startswith("seed-")
        assert seed.url.startswith("https://")
        assert seed.domain != ""
        assert seed.organization != ""
        assert seed.category != ""
        assert seed.license_hint != ""
        assert seed.why_included != ""

    # Category filtering
    software_libre = get_curated_seed_urls(category="software_libre")
    assert len(software_libre) >= 3
    assert "https://www.fsf.org/" in software_libre
    assert "https://www.gnu.org/" in software_libre

    # Country and government seeds filtering
    co_seeds = get_seeds_by_country("CO")
    assert len(co_seeds) >= 5
    assert any(s.domain == "www.presidencia.gov.co" for s in co_seeds)
    assert any(s.domain == "www.cancilleria.gov.co" for s in co_seeds)

    es_seeds = get_seeds_by_country("es")
    assert len(es_seeds) >= 5
    assert any(s.domain == "www.lamoncloa.gob.es" for s in es_seeds)

    jp_seeds = get_seeds_by_country("JP")
    assert len(jp_seeds) >= 3
    assert any(s.domain == "www.kantei.go.jp" for s in jp_seeds)

    gov_seeds = get_government_seeds()
    assert len(gov_seeds) >= 40
    assert any(s.id == "seed-un-data" for s in gov_seeds)
    assert any(s.id == "seed-whitehouse-gov" for s in gov_seeds)


# 4. Test Crawler Safety Gate with ThreatGuard
@pytest.mark.asyncio
async def test_crawler_blocks_threat_guard_targets(temp_storage):
    runner = CrawlerRunner(storage=temp_storage)
    malware_url = "http://malicious-test-site.example.com/exploit.html"
    threat_guard.register_threat(
        target=malware_url,
        category=ThreatCategory.MALWARE,
        feed_source="URLhaus (abuse.ch)",
        rule_id="TEST-MALWARE-1",
    )

    with patch.object(runner.fetcher, "fetch", new_callable=AsyncMock) as mock_fetch:
        indexed = await runner.crawl_seed(malware_url, max_pages=1)
        assert indexed == 0
        # The fetcher must NEVER have been called
        assert mock_fetch.call_count == 0


# 5. Honest Coverage Metrics Reporting (Strictly zero inflated numbers)
def test_honest_coverage_metrics_reporting(temp_storage):
    stats = temp_storage.get_stats()
    # Honest integer reporting: exact number of documents and domains
    assert isinstance(stats["total_documents"], int)
    assert isinstance(stats["total_domains"], int)
    assert stats["total_documents"] == 0
    assert stats["total_domains"] == 0
