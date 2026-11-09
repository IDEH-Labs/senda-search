# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Retraction cross-referencing registry for academic works.

Powered by open metadata from Crossref and Retraction Watch CC0 datasets.
Cross-references DOIs and canonical URLs to detect retracted papers, expressions of
concern, and corrigenda.
"""

import logging
from typing import Optional, Dict
from senda.providers.base import RetractionInfo

logger = logging.getLogger(__name__)


class RetractionRegistry:
    """In-memory and persistent registry for retracted scientific works."""

    def __init__(self):
        # Normalized DOI (lowercase) -> RetractionInfo
        self._retractions_by_doi: Dict[str, RetractionInfo] = {}

    def register(
        self,
        doi: str,
        status: str = "retractada",
        source: str = "Crossref / Retraction Watch",
        date: Optional[str] = None,
        notice_url: Optional[str] = None,
    ) -> None:
        """Register a known retracted work."""
        clean_doi = self.normalize_doi(doi)
        if clean_doi:
            self._retractions_by_doi[clean_doi] = RetractionInfo(
                status=status,
                source=source,
                date=date,
                notice_url=notice_url,
            )

    @staticmethod
    def normalize_doi(doi: Optional[str]) -> Optional[str]:
        """Strip DOI resolver prefixes and lowercase."""
        if not doi:
            return None
        clean = doi.strip().lower()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
        return clean.strip()

    def check(self, doi: Optional[str]) -> Optional[RetractionInfo]:
        """Check if a DOI is retracted.
        
        Returns RetractionInfo if registered, or None if no retraction record exists.
        """
        clean_doi = self.normalize_doi(doi)
        if not clean_doi:
            return None
        return self._retractions_by_doi.get(clean_doi)


# Global retraction registry instance
retraction_registry = RetractionRegistry()
