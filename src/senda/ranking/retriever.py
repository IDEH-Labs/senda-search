# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Information Retrieval and Ranking Engine for Senda.

Executes sanitized BM25 scoring with ethical field weighting (Title > Headings > Description > Body),
contextual snippet extraction with highlighting, and pagination.
"""

from dataclasses import dataclass, field
import html
import re
import time
from typing import Optional

from senda.indexer.storage import StorageEngine


@dataclass(frozen=True)
class SearchResultItem:
    """A single ranked search result item."""
    url: str
    domain: str
    title: str
    snippet: str
    relevance_score: float


@dataclass(frozen=True)
class SearchResultSet:
    """Paginated collection of ranked search results."""
    query: str
    sanitized_query: str
    total_matches: int
    page: int
    page_size: int
    total_pages: int
    duration_ms: float
    items: list[SearchResultItem] = field(default_factory=list)


class QuerySanitizer:
    """Safely sanitizes raw user search queries for SQLite FTS5 syntax."""

    # Characters with special syntax meaning in FTS5 that could trigger syntax errors
    SPECIAL_CHARS = re.compile(r'[*^{}+~:()]')
    PHRASE_PATTERN = re.compile(r'"([^"]*)"')

    @classmethod
    def sanitize(cls, raw_query: str) -> str:
        """Transform user query into an injection-safe, valid FTS5 MATCH expression."""
        if not raw_query:
            return ""

        query = raw_query.strip()
        if not query:
            return ""

        # Extract exact quoted phrases
        phrases: list[str] = []
        def extract_phrase(match):
            cleaned = cls.SPECIAL_CHARS.sub(" ", match.group(1)).strip()
            if cleaned:
                phrases.append(f'"{cleaned}"')
            return " "

        remainder = cls.PHRASE_PATTERN.sub(extract_phrase, query)

        # Remove special characters from remainder
        clean_remainder = cls.SPECIAL_CHARS.sub(" ", remainder)

        # Split remaining words
        tokens = [token.strip() for token in clean_remainder.split() if token.strip()]

        # Filter out standalone SQLite FTS5 operators that could break syntax
        safe_tokens: list[str] = []
        for t in tokens:
            t_upper = t.upper()
            if t_upper in ("AND", "OR", "NOT", "NEAR"):
                continue
            # Escape double quotes if any remained
            clean_token = t.replace('"', '')
            if clean_token:
                # Append prefix matching for better typing experience if token is alphanumeric
                if clean_token.isalnum() and len(clean_token) >= 3:
                    safe_tokens.append(f'"{clean_token}"*')
                else:
                    safe_tokens.append(f'"{clean_token}"')

        all_clauses = phrases + safe_tokens
        if not all_clauses:
            return ""

        return " ".join(all_clauses)


class SearchRetriever:
    """Coordinates search execution against SQLite FTS5."""

    # Field weights for BM25: (title, headings, description, body)
    WEIGHT_TITLE = 10.0
    WEIGHT_HEADINGS = 5.0
    WEIGHT_DESCRIPTION = 3.0
    WEIGHT_BODY = 1.0

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 10
    ) -> SearchResultSet:
        """Execute a ranked full-text search with BM25 and contextual snippets."""
        start_time = time.perf_counter()

        page = max(1, page)
        page_size = min(max(1, page_size), 50)
        offset = (page - 1) * page_size

        sanitized_fts = QuerySanitizer.sanitize(query)
        if not sanitized_fts:
            duration = (time.perf_counter() - start_time) * 1000.0
            return SearchResultSet(
                query=query,
                sanitized_query="",
                total_matches=0,
                page=page,
                page_size=page_size,
                total_pages=0,
                duration_ms=round(duration, 2),
                items=[]
            )

        with self.storage.get_connection() as conn:
            # 1. Count total matching rows
            count_cur = conn.execute(
                """
                SELECT COUNT(*) FROM documents_fts
                WHERE documents_fts MATCH ?
                """,
                (sanitized_fts,)
            )
            total_matches = count_cur.fetchone()[0]

            if total_matches == 0:
                duration = (time.perf_counter() - start_time) * 1000.0
                return SearchResultSet(
                    query=query,
                    sanitized_query=sanitized_fts,
                    total_matches=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                    duration_ms=round(duration, 2),
                    items=[]
                )

            total_pages = (total_matches + page_size - 1) // page_size

            # 2. Retrieve ranked rows with BM25 and highlight snippet
            # BM25 weights: title=10.0, headings=5.0, description=3.0, body=1.0
            # Lower BM25 score means more relevant
            query_sql = """
                SELECT
                    d.url,
                    d.domain,
                    d.title,
                    d.description,
                    snippet(documents_fts, -1, '<mark>', '</mark>', '...', 28) AS fts_snippet,
                    bm25(documents_fts, ?, ?, ?, ?) AS bm25_score
                FROM documents_fts
                JOIN documents d ON d.id = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY bm25_score ASC
                LIMIT ? OFFSET ?
            """

            rows = conn.execute(
                query_sql,
                (
                    self.WEIGHT_TITLE,
                    self.WEIGHT_HEADINGS,
                    self.WEIGHT_DESCRIPTION,
                    self.WEIGHT_BODY,
                    sanitized_fts,
                    page_size,
                    offset
                )
            ).fetchall()

            items: list[SearchResultItem] = []
            for row in rows:
                snippet_text = row["fts_snippet"]
                if not snippet_text or snippet_text.strip() == "...":
                    snippet_text = row["description"] or ""

                items.append(
                    SearchResultItem(
                        url=row["url"],
                        domain=row["domain"],
                        title=row["title"],
                        snippet=snippet_text,
                        relevance_score=round(-float(row["bm25_score"]), 8),  # Negate so higher is better
                    )
                )

        duration = (time.perf_counter() - start_time) * 1000.0

        return SearchResultSet(
            query=query,
            sanitized_query=sanitized_fts,
            total_matches=total_matches,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            duration_ms=round(duration, 2),
            items=items
        )
