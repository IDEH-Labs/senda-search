# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""SQLite FTS5 Storage Engine for Senda.

Provides ACID transactional document storage, full-text inverted indexing with BM25,
domain-level indexing stats, and ethical takedown/purge capabilities.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Generator, Optional, Any
from urllib.parse import urlparse

from senda.config import settings
from senda.extractor.parser import ExtractedDocument


SCHEMA_SQL = """
-- Master documents repository
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    language TEXT,
    headings TEXT,
    body TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    first_indexed_at TEXT NOT NULL,
    last_crawled_at TEXT NOT NULL,
    status_code INTEGER DEFAULT 200
);

CREATE INDEX IF NOT EXISTS idx_documents_domain ON documents(domain);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);

-- Full-Text Search Virtual Table using FTS5 with unicode61 tokenizer
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    headings,
    description,
    body,
    content='documents',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

-- Triggers to keep FTS5 synchronized with master documents table
CREATE TRIGGER IF NOT EXISTS trg_documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, headings, description, body)
    VALUES (new.id, new.title, new.headings, new.description, new.body);
END;

CREATE TRIGGER IF NOT EXISTS trg_documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, headings, description, body)
    VALUES ('delete', old.id, old.title, old.headings, old.description, old.body);
END;

CREATE TRIGGER IF NOT EXISTS trg_documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, headings, description, body)
    VALUES ('delete', old.id, old.title, old.headings, old.description, old.body);
    INSERT INTO documents_fts(rowid, title, headings, description, body)
    VALUES (new.id, new.title, new.headings, new.description, new.body);
END;

-- Frontier queue state table
CREATE TABLE IF NOT EXISTS frontier_queue (
    url TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    depth INTEGER DEFAULT 0,
    discovered_at TEXT NOT NULL,
    last_fetched_at TEXT,
    fetch_status TEXT DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_frontier_domain ON frontier_queue(domain);
CREATE INDEX IF NOT EXISTS idx_frontier_status ON frontier_queue(fetch_status);
"""


class StorageEngine:
    """Manages SQLite database connections, migrations, indexing, and purging."""

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path) if db_path else settings.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a configured SQLite connection with WAL mode and foreign keys enabled."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Create schema, tables, triggers, and indices if they do not exist."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def upsert_document(
        self,
        doc: ExtractedDocument,
        status_code: int = 200
    ) -> bool:
        """Insert a new document or update existing if content has changed.

        Returns True if inserted or updated, False if skipped due to identical content_hash.
        """
        domain = urlparse(doc.url).netloc.lower()
        now = datetime.now(timezone.utc).isoformat()

        with self.get_connection() as conn:
            # Check existing document
            cur = conn.execute(
                "SELECT id, content_hash FROM documents WHERE url = ?",
                (doc.url,)
            )
            row = cur.fetchone()

            if row:
                doc_id = row["id"]
                existing_hash = row["content_hash"]
                if existing_hash == doc.content_hash:
                    # Content unchanged; just update last_crawled_at
                    conn.execute(
                        "UPDATE documents SET last_crawled_at = ?, status_code = ? WHERE id = ?",
                        (now, status_code, doc_id)
                    )
                    conn.commit()
                    return False

                # Content changed, update document and trigger FTS re-indexing
                conn.execute(
                    """
                    UPDATE documents SET
                        domain = ?,
                        title = ?,
                        description = ?,
                        language = ?,
                        headings = ?,
                        body = ?,
                        content_hash = ?,
                        last_crawled_at = ?,
                        status_code = ?
                    WHERE id = ?
                    """,
                    (
                        domain,
                        doc.title,
                        doc.description,
                        doc.language,
                        doc.headings,
                        doc.body_text,
                        doc.content_hash,
                        now,
                        status_code,
                        doc_id
                    )
                )
                conn.commit()
                return True
            else:
                conn.execute(
                    """
                    INSERT INTO documents (
                        url, domain, title, description, language,
                        headings, body, content_hash, first_indexed_at,
                        last_crawled_at, status_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc.url,
                        domain,
                        doc.title,
                        doc.description,
                        doc.language,
                        doc.headings,
                        doc.body_text,
                        doc.content_hash,
                        now,
                        now,
                        status_code
                    )
                )
                conn.commit()
                return True

    def get_document_by_url(self, url: str) -> Optional[dict[str, Any]]:
        """Retrieve indexed document record by exact canonical URL."""
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM documents WHERE url = ?", (url,))
            row = cur.fetchone()
            return dict(row) if row else None

    def purge_url(self, url: str) -> int:
        """Remove a document by exact URL (FTS triggers automatically purge index).

        Returns number of deleted documents (0 or 1).
        """
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM documents WHERE url = ?", (url,))
            conn.commit()
            return cur.rowcount

    def purge_domain(self, domain: str) -> int:
        """Remove all documents belonging to a domain (Takedown compliance).

        Returns number of deleted documents.
        """
        domain_normalized = domain.strip().lower()
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM documents WHERE domain = ?", (domain_normalized,))
            conn.commit()
            return cur.rowcount

    def get_stats(self) -> dict[str, Any]:
        """Return operational indexing statistics."""
        with self.get_connection() as conn:
            doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            domain_count = conn.execute("SELECT COUNT(DISTINCT domain) FROM documents").fetchone()[0]

            db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "total_documents": doc_count,
                "total_domains": domain_count,
                "database_size_bytes": db_size_bytes,
                "database_path": str(self.db_path),
            }
