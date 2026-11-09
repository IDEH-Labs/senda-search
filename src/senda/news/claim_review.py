# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Schema.org ClaimReview fact-checking extractor and registry.

Strict Ethics & Verifiable Provenance Enforcement:
- Fact-check verdicts are ALWAYS attributed to the independent verifying organization (IFCN signatory).
- Senda NEVER certifies truth nor emits its own verdicts of 'verdadero' or 'falso'.
- Every verification shown in Senda specifies who reviewed, when, and the attributed conclusion.
"""

from dataclasses import dataclass
import json
import logging
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse

from senda.providers.base import VerificationItem, SearchResultItem

logger = logging.getLogger(__name__)


class ClaimReviewParser:
    """Parser for Schema.org ClaimReview JSON-LD and microdata."""

    @classmethod
    def parse_json_ld(cls, data: Union[str, dict, list]) -> List[VerificationItem]:
        """Extract VerificationItem objects from JSON-LD ClaimReview structures."""
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except Exception as e:
                logger.warning(f"ClaimReviewParser: Error parsing JSON-LD string: {e}")
                return []
        else:
            parsed = data

        items: List[VerificationItem] = []
        if isinstance(parsed, list):
            for block in parsed:
                items.extend(cls.parse_json_ld(block))
            return items

        if not isinstance(parsed, dict):
            return []

        # Handle @graph containers
        if "@graph" in parsed and isinstance(parsed["@graph"], list):
            for node in parsed["@graph"]:
                items.extend(cls.parse_json_ld(node))
            return items

        item_type = parsed.get("@type")
        item_types = [item_type] if isinstance(item_type, str) else (item_type if isinstance(item_type, list) else [])
        if "ClaimReview" not in item_types:
            return []

        # 1. Verifier organization (author)
        author_info = parsed.get("author") or {}
        verifier_name = "Verificador Independiente"
        if isinstance(author_info, dict):
            verifier_name = author_info.get("name") or author_info.get("legalName") or verifier_name
        elif isinstance(author_info, str):
            verifier_name = author_info.strip()

        # 2. Attributed verdict (reviewRating)
        rating_info = parsed.get("reviewRating") or {}
        attributed_verdict = "Evaluación no especificada"
        if isinstance(rating_info, dict):
            attributed_verdict = (
                rating_info.get("alternateName")
                or rating_info.get("ratingValue")
                or attributed_verdict
            )
            # If numeric rating without text label, provide clear context
            if str(attributed_verdict).isdigit():
                attributed_verdict = f"Puntuación {attributed_verdict}/5"
        elif isinstance(rating_info, str):
            attributed_verdict = rating_info.strip()

        # 3. Permanent URL of the analysis
        analysis_url = parsed.get("url") or ""

        # 4. Publication date
        date_published = parsed.get("datePublished")
        if date_published and len(str(date_published)) >= 10:
            date_published = str(date_published)[:10]
        else:
            date_published = None

        if not analysis_url:
            return []

        items.append(
            VerificationItem(
                verifier=str(verifier_name).strip(),
                attributed_verdict=str(attributed_verdict).strip(),
                url=str(analysis_url).strip(),
                date=date_published,
            )
        )
        return items

    @staticmethod
    def format_attribution(item: VerificationItem) -> str:
        """Format strictly attributed text ensuring Senda never claims the verdict as its own."""
        date_str = f" el {item.date}" if item.date else ""
        return f"{item.verifier} concluyó: \"{item.attributed_verdict}\" (publicado{date_str})."


class ClaimReviewRegistry:
    """Registry mapping URLs and analyzed claims to attributed VerificationItems."""

    def __init__(self):
        # Target URL (lowercase) -> list[VerificationItem]
        self._verifications_by_url: Dict[str, List[VerificationItem]] = {}

    def register(self, target_url: str, verification: VerificationItem) -> None:
        """Register an attributed fact-check for a target URL."""
        clean_url = target_url.strip().lower()
        if not clean_url:
            return
        if clean_url not in self._verifications_by_url:
            self._verifications_by_url[clean_url] = []
        self._verifications_by_url[clean_url].append(verification)

    def get_verifications(self, url: str) -> List[VerificationItem]:
        """Retrieve all attributed third-party verifications for a URL."""
        clean_url = url.strip().lower()
        return list(self._verifications_by_url.get(clean_url, []))

    def decorate_search_item(self, item: SearchResultItem) -> SearchResultItem:
        """Attach attributed fact-checks to a SearchResultItem if target URL matches."""
        matches = self.get_verifications(item.url)
        if matches:
            # Combine without duplicating
            existing_urls = {v.url for v in item.verifications}
            for m in matches:
                if m.url not in existing_urls:
                    item.verifications.append(m)
        return item


# Global registry instance
claim_review_registry = ClaimReviewRegistry()
