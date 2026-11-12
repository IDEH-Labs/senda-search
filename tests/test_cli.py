# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for Senda administrative CLI commands."""

import io
import sys
from unittest.mock import patch
import pytest

from senda.cli.main import main
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine


@pytest.fixture
def test_db_env(tmp_path, monkeypatch):
    db_file = tmp_path / "cli_test.db"
    monkeypatch.setattr("senda.config.settings.DATA_DIR", tmp_path)
    monkeypatch.setattr("senda.config.settings.DATABASE_NAME", "cli_test.db")

    storage = StorageEngine(db_path=db_file)
    storage.upsert_document(
        ExtractedDocument(
            url="https://gentoo.org/about",
            title="Gentoo Linux - Philosophy and Control",
            description="A highly flexible, source-based Linux distribution.",
            language="en",
            headings="Choice Freedom",
            body_text="Gentoo is built around freedom of choice and maximum system control.",
            content_hash="gentoohash1",
        )
    )
    return storage


def test_cli_stats(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "stats"])
    main()

    captured = capsys.readouterr()
    assert "Senda Index Statistics" in captured.out
    assert "Total Documents:  1" in captured.out
    assert "Total Domains:    1" in captured.out


def test_cli_search(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "search", "Gentoo"])
    main()

    captured = capsys.readouterr()
    assert "Senda Search: 'Gentoo'" in captured.out
    assert "Gentoo Linux - Philosophy and Control" in captured.out
    assert "https://gentoo.org/about" in captured.out


def test_cli_purge_url(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "purge-url", "https://gentoo.org/about"])
    main()

    captured = capsys.readouterr()
    assert "Purged 1 document matching URL" in captured.out

    # Verify document is gone
    monkeypatch.setattr(sys, "argv", ["senda", "stats"])
    main()
    captured_after = capsys.readouterr()
    assert "Total Documents:  0" in captured_after.out


def test_cli_purge_domain(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "purge-domain", "gentoo.org"])
    main()

    captured = capsys.readouterr()
    assert "Purged 0 document(s) belonging to domain 'gentoo.org'" in captured.out or "Purged 1 document(s)" in captured.out


def test_cli_crawl_missing_args(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "crawl"])
    main()
    captured = capsys.readouterr()
    assert "Error: Must provide either a seed URL or --seeds-file." in captured.out


def test_cli_crawl_daemon_once(test_db_env, tmp_path, monkeypatch, capsys):
    from unittest.mock import AsyncMock
    seeds_file = tmp_path / "test_seeds.txt"
    seeds_file.write_text("https://example.org\nhttps://fsf.org\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["senda", "crawl-daemon", "--seeds-file", str(seeds_file), "--once", "--max-pages", "5"])

    with patch("senda.cli.main.CrawlerRunner.crawl_seeds", new_callable=AsyncMock) as mock_crawl:
        mock_crawl.return_value = 2
        main()

    captured = capsys.readouterr()
    assert "Senda Ethical Indexer Daemon" in captured.out
    assert "Cycle #1 completed. Indexed/Updated: 2 docs." in captured.out
    assert "Senda Indexer Daemon stopped cleanly." in captured.out


def test_cli_serve(monkeypatch, capsys):
    """Verify senda serve executes cleanly with uvicorn and handles forwarded_allow_ips."""
    monkeypatch.setattr(sys, "argv", ["senda", "serve", "--host", "127.0.0.1", "--port", "8000"])
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.called
        kwargs = mock_run.call_args.kwargs
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8000
        assert kwargs["proxy_headers"] is True
        assert "forwarded_allow_ips" in kwargs

    captured = capsys.readouterr()
    assert "Starting Senda Sovereign Search Web UI" in captured.out


def test_cli_serve_custom_cli_forwarded_ips(monkeypatch, capsys):
    """Verify senda serve CLI flag --forwarded-allow-ips propagates directly to uvicorn."""
    custom_ips = "10.0.0.1,192.168.1.1,172.16.0.0/12"
    monkeypatch.setattr(sys, "argv", ["senda", "serve", "--host", "0.0.0.0", "--port", "9000", "--forwarded-allow-ips", custom_ips])
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.called
        kwargs = mock_run.call_args.kwargs
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 9000
        assert kwargs["forwarded_allow_ips"] == custom_ips


def test_cli_serve_env_and_defaults(monkeypatch, capsys):
    """Verify senda serve uses settings defaults and reads FORWARDED_ALLOW_IPS from environment."""
    monkeypatch.setattr(sys, "argv", ["senda", "serve"])
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "127.0.0.1,::1,10.0.0.0/8")
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.called
        kwargs = mock_run.call_args.kwargs
        from senda.config import settings
        assert kwargs["host"] == settings.SERVER_HOST
        assert kwargs["port"] == settings.SERVER_PORT
        assert kwargs["forwarded_allow_ips"] == "127.0.0.1,::1,10.0.0.0/8"


def test_cli_serve_disables_access_log_by_default_and_honors_env(monkeypatch):
    """Verify senda serve disables uvicorn access_log by default to protect search queries in journald."""
    monkeypatch.setattr(sys, "argv", ["senda", "serve"])
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.call_args.kwargs["access_log"] is False

    monkeypatch.setenv("SENDA_ACCESS_LOG", "true")
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.call_args.kwargs["access_log"] is True



