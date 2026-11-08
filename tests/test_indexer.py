# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for StorageEngine SQLite FTS5 indexer and purge functionality."""

import pytest
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine


@pytest.fixture
def temp_storage(tmp_path):
    db_file = tmp_path / "test_senda.db"
    return StorageEngine(db_path=db_file)


def test_storage_init_and_stats_empty(temp_storage):
    stats = temp_storage.get_stats()
    assert stats["total_documents"] == 0
    assert stats["total_domains"] == 0
    assert stats["database_size_bytes"] > 0


def test_storage_upsert_and_retrieve(temp_storage):
    doc = ExtractedDocument(
        url="https://fsf.org/about",
        title="About the Free Software Foundation",
        description="Defending computer user freedom worldwide.",
        language="en",
        headings="Our Mission Freedom 0 1 2 3",
        body_text="Free software means the users have the freedom to run, copy, distribute, study, change and improve the software.",
        content_hash="abc123hash",
        outgoing_links=["https://gnu.org"]
    )

    # First insert
    inserted = temp_storage.upsert_document(doc, status_code=200)
    assert inserted is True

    record = temp_storage.get_document_by_url("https://fsf.org/about")
    assert record is not None
    assert record["domain"] == "fsf.org"
    assert record["title"] == "About the Free Software Foundation"
    assert record["content_hash"] == "abc123hash"

    # Verify FTS index entry exists
    with temp_storage.get_connection() as conn:
        res = conn.execute(
            "SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'freedom'"
        ).fetchall()
        assert len(res) == 1

    # Second insert with identical hash -> should not re-insert, returns False
    inserted_again = temp_storage.upsert_document(doc, status_code=200)
    assert inserted_again is False


def test_storage_update_content_hash(temp_storage):
    doc1 = ExtractedDocument(
        url="https://example.com/page",
        title="Initial Title",
        description="Desc",
        language="en",
        headings="Heading",
        body_text="Old body text",
        content_hash="hash1",
    )
    temp_storage.upsert_document(doc1)

    doc2 = ExtractedDocument(
        url="https://example.com/page",
        title="Updated Title",
        description="Desc",
        language="en",
        headings="Heading",
        body_text="New updated text with ethical standards",
        content_hash="hash2",
    )
    updated = temp_storage.upsert_document(doc2)
    assert updated is True

    record = temp_storage.get_document_by_url("https://example.com/page")
    assert record["title"] == "Updated Title"
    assert record["content_hash"] == "hash2"

    # FTS matches new text
    with temp_storage.get_connection() as conn:
        res = conn.execute(
            "SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'ethical'"
        ).fetchall()
        assert len(res) == 1


def test_storage_purge_url_and_domain(temp_storage):
    doc1 = ExtractedDocument(
        url="https://privacy.example.org/doc1",
        title="Doc 1",
        description="",
        language="en",
        headings="",
        body_text="Document one text",
        content_hash="h1",
    )
    doc2 = ExtractedDocument(
        url="https://privacy.example.org/doc2",
        title="Doc 2",
        description="",
        language="en",
        headings="",
        body_text="Document two text",
        content_hash="h2",
    )
    doc3 = ExtractedDocument(
        url="https://other.org/doc3",
        title="Doc 3",
        description="",
        language="en",
        headings="",
        body_text="Document three text",
        content_hash="h3",
    )
    temp_storage.upsert_document(doc1)
    temp_storage.upsert_document(doc2)
    temp_storage.upsert_document(doc3)

    assert temp_storage.get_stats()["total_documents"] == 3

    # Purge single URL
    deleted = temp_storage.purge_url("https://privacy.example.org/doc1")
    assert deleted == 1
    assert temp_storage.get_document_by_url("https://privacy.example.org/doc1") is None
    assert temp_storage.get_stats()["total_documents"] == 2

    # Purge entire domain
    deleted_domain = temp_storage.purge_domain("privacy.example.org")
    assert deleted_domain == 1
    assert temp_storage.get_stats()["total_documents"] == 1
    assert temp_storage.get_stats()["total_domains"] == 1

    # FTS check
    with temp_storage.get_connection() as conn:
        res = conn.execute(
            "SELECT COUNT(*) FROM documents_fts WHERE documents_fts MATCH 'text'"
        ).fetchone()[0]
        assert res == 1
