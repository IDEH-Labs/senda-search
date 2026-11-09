# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Information Retrieval and Ranking Engine for Senda.

Executes sanitized BM25 scoring with ethical field weighting (Title > Headings > Description > Body),
contextual snippet extraction with highlighting, query operators (site:, lang:, -term),
morphological stem expansion, and pagination.
"""

from dataclasses import dataclass, field
import html
import re
import time
from typing import Optional

from senda.indexer.storage import StorageEngine
from senda.ranking.stemmer import MorphologicalStemmer


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


@dataclass(frozen=True)
class ParsedQuery:
    """Structured representation of a user query with extracted operators and FTS5 expression."""
    raw_query: str
    fts_expression: str
    domain_filter: Optional[str] = None
    lang_filter: Optional[str] = None


class QuerySanitizer:
    """Safely sanitizes raw user search queries and extracts structured operators."""

    SPECIAL_CHARS = re.compile(r'[*^{}+~:()]')
    PHRASE_PATTERN = re.compile(r'"([^"]*)"')
    SITE_PATTERN = re.compile(r'\b(?:site|domain):([a-zA-Z0-9.-]+)\b', re.IGNORECASE)
    LANG_PATTERN = re.compile(r'\blang:([a-zA-Z-]+)\b', re.IGNORECASE)

    @classmethod
    def parse(cls, raw_query: str) -> ParsedQuery:
        """Parse raw query into structured filters and safe SQLite FTS5 MATCH expression."""
        if not raw_query:
            return ParsedQuery(raw_query="", fts_expression="")

        query = raw_query.strip()
        if not query:
            return ParsedQuery(raw_query=raw_query, fts_expression="")

        domain_filter: Optional[str] = None
        lang_filter: Optional[str] = None

        # 1. Extract site:/domain: operator
        def extract_domain(match):
            nonlocal domain_filter
            domain_filter = match.group(1).lower()
            return " "

        query = cls.SITE_PATTERN.sub(extract_domain, query)

        # 2. Extract lang: operator
        def extract_lang(match):
            nonlocal lang_filter
            lang_filter = match.group(1).lower()
            return " "

        query = cls.LANG_PATTERN.sub(extract_lang, query)

        # 3. Extract exact quoted phrases
        phrases: list[str] = []
        def extract_phrase(match):
            cleaned = cls.SPECIAL_CHARS.sub(" ", match.group(1)).strip()
            if cleaned:
                phrases.append(f'"{cleaned}"')
            return " "

        remainder = cls.PHRASE_PATTERN.sub(extract_phrase, query)

        # 4. Extract negative terms (-unwanted) and positive terms
        clean_tokens = [t.strip() for t in remainder.split() if t.strip()]

        positive_clauses: list[str] = list(phrases)
        negative_clauses: list[str] = []

        for token in clean_tokens:
            is_negative = token.startswith("-") and len(token) > 1
            raw_token = token[1:] if is_negative else token

            # Strip special characters
            clean_token = cls.SPECIAL_CHARS.sub("", raw_token).replace('"', '').strip()
            if not clean_token:
                continue

            # Skip standalone reserved operators
            if clean_token.upper() in ("AND", "OR", "NOT", "NEAR"):
                continue

            if is_negative:
                negative_clauses.append(f'"{clean_token}"')
            else:
                # Morphological stem expansion for multilingual richness
                root = MorphologicalStemmer.get_root_prefix(clean_token)
                if root and root != clean_token and len(root) >= 3:
                    # Match exact word or morphological root prefix
                    positive_clauses.append(f'("{clean_token}" OR "{root}"*)')
                elif clean_token.isalnum() and len(clean_token) >= 3:
                    positive_clauses.append(f'"{clean_token}"*')
                else:
                    positive_clauses.append(f'"{clean_token}"')

        # Combine into valid SQLite FTS5 expression
        fts_parts: list[str] = []
        if positive_clauses:
            fts_parts.append(" ".join(positive_clauses))

        if negative_clauses:
            # FTS5 syntax: expr1 NOT expr2
            for neg in negative_clauses:
                fts_parts.append(f"NOT {neg}")

        fts_expression = " ".join(fts_parts).strip()

        return ParsedQuery(
            raw_query=raw_query,
            fts_expression=fts_expression,
            domain_filter=domain_filter,
            lang_filter=lang_filter
        )

    @classmethod
    def sanitize(cls, raw_query: str) -> str:
        """Backward-compatible helper returning raw FTS expression."""
        return cls.parse(raw_query).fts_expression


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
        """Execute a ranked full-text search with BM25, query operators, and contextual snippets."""
        start_time = time.perf_counter()

        page = max(1, page)
        page_size = min(max(1, page_size), 50)
        offset = (page - 1) * page_size

        parsed = QuerySanitizer.parse(query)
        if not parsed.fts_expression:
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
            # 1. Count total matching rows filtered by domain and language
            count_sql = """
                SELECT COUNT(*) FROM documents_fts
                JOIN documents d ON d.id = documents_fts.rowid
                WHERE documents_fts MATCH ?
                  AND (? IS NULL OR d.domain = ? OR d.domain LIKE '%.' || ?)
                  AND (? IS NULL OR d.language = ?)
            """
            count_cur = conn.execute(
                count_sql,
                (
                    parsed.fts_expression,
                    parsed.domain_filter,
                    parsed.domain_filter,
                    parsed.domain_filter,
                    parsed.lang_filter,
                    parsed.lang_filter
                )
            )
            total_matches = count_cur.fetchone()[0]

            if total_matches == 0:
                duration = (time.perf_counter() - start_time) * 1000.0
                return SearchResultSet(
                    query=query,
                    sanitized_query=parsed.fts_expression,
                    total_matches=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                    duration_ms=round(duration, 2),
                    items=[]
                )

            total_pages = (total_matches + page_size - 1) // page_size

            # 2. Retrieve ranked rows with BM25, anti-SEO text density boost, snippets, and filters
            query_sql = """
                SELECT
                    d.url,
                    d.domain,
                    d.title,
                    d.description,
                    COALESCE(d.text_density, 0.0) AS text_density,
                    snippet(documents_fts, -1, '<mark>', '</mark>', '...', 28) AS fts_snippet,
                    bm25(documents_fts, ?, ?, ?, ?) AS bm25_score
                FROM documents_fts
                JOIN documents d ON d.id = documents_fts.rowid
                WHERE documents_fts MATCH ?
                  AND (? IS NULL OR d.domain = ? OR d.domain LIKE '%.' || ?)
                  AND (? IS NULL OR d.language = ?)
                ORDER BY (bm25(documents_fts, ?, ?, ?, ?) * (1.0 + COALESCE(d.text_density, 0.0))) ASC
                LIMIT ? OFFSET ?
            """

            rows = conn.execute(
                query_sql,
                (
                    self.WEIGHT_TITLE,
                    self.WEIGHT_HEADINGS,
                    self.WEIGHT_DESCRIPTION,
                    self.WEIGHT_BODY,
                    parsed.fts_expression,
                    parsed.domain_filter,
                    parsed.domain_filter,
                    parsed.domain_filter,
                    parsed.lang_filter,
                    parsed.lang_filter,
                    self.WEIGHT_TITLE,
                    self.WEIGHT_HEADINGS,
                    self.WEIGHT_DESCRIPTION,
                    self.WEIGHT_BODY,
                    page_size,
                    offset
                )
            ).fetchall()

            items: list[SearchResultItem] = []
            for row in rows:
                snippet_text = row["fts_snippet"]
                if not snippet_text or snippet_text.strip() == "...":
                    snippet_text = row["description"] or ""

                # Compute weighted relevance factoring anti-SEO text density
                density_factor = 1.0 + float(row["text_density"])
                final_score = round(-float(row["bm25_score"]) * density_factor, 8)

                items.append(
                    SearchResultItem(
                        url=row["url"],
                        domain=row["domain"],
                        title=row["title"],
                        snippet=snippet_text,
                        relevance_score=final_score,
                    )
                )

        duration = (time.perf_counter() - start_time) * 1000.0

        return SearchResultSet(
            query=query,
            sanitized_query=parsed.fts_expression,
            total_matches=total_matches,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            duration_ms=round(duration, 2),
            items=items
        )
