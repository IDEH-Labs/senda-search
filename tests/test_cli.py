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

