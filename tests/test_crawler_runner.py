# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for CrawlerRunner orchestration."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from senda.crawler.fetcher import FetchedDocument
from senda.crawler.runner import CrawlerRunner
from senda.indexer.storage import StorageEngine


@pytest.mark.asyncio
async def test_crawler_runner_indexes_seed_and_outgoing(tmp_path):
    storage = StorageEngine(db_path=tmp_path / "runner_test.db")

    fetcher_mock = MagicMock()

    # Document 1: Seed page
    html_page1 = """
    <html>
        <head><title>Senda Home</title></head>
        <body>
            <p>Welcome to Senda search engine.</p>
            <a href="https://example.com/about">About Us</a>
        </body>
    </html>
    """

    # Document 2: Outgoing link
    html_page2 = """
    <html>
        <head><title>About Senda</title></head>
        <body>
            <p>Our ethical mission and privacy commitments.</p>
        </body>
    </html>
    """

    robots_txt = "User-agent: *\nAllow: /\n"

    async def mock_fetch(url):
        if "robots.txt" in url:
            return FetchedDocument(
                url=url,
                status_code=200,
                headers={"Content-Type": "text/plain"},
                content=robots_txt.encode("utf-8"),
                text=robots_txt,
                content_type="text/plain",
                encoding="utf-8"
            )
        elif url == "https://example.com/":
            return FetchedDocument(
                url=url,
                status_code=200,
                headers={"Content-Type": "text/html"},
                content=html_page1.encode("utf-8"),
                text=html_page1,
                content_type="text/html",
                encoding="utf-8"
            )
        elif url == "https://example.com/about":
            return FetchedDocument(
                url=url,
                status_code=200,
                headers={"Content-Type": "text/html"},
                content=html_page2.encode("utf-8"),
                text=html_page2,
                content_type="text/html",
                encoding="utf-8"
            )
        raise ValueError(f"Unexpected url: {url}")

    fetcher_mock.fetch = AsyncMock(side_effect=mock_fetch)
    fetcher_mock.user_agent = "SendaBot/0.1"

    runner = CrawlerRunner(storage=storage, fetcher=fetcher_mock)

    # Politeness queue delay set to 0 for instant test execution
    runner.frontier.default_crawl_delay = 0.0

    indexed_count = await runner.crawl_seed("https://example.com/", max_pages=2, max_depth=1)

    assert indexed_count == 2
    assert storage.get_stats()["total_documents"] == 2

    # Verify both pages are in FTS index
    doc1 = storage.get_document_by_url("https://example.com/")
    assert doc1["title"] == "Senda Home"

    doc2 = storage.get_document_by_url("https://example.com/about")
    assert doc2["title"] == "About Senda"
