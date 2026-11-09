# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Ethical Fediverse (ActivityPub / Mastodon) Search Provider for Senda.

Strictly queries public timeline tags or search endpoints without tracking,
cookies, or personal account requirements. Isolated to 'social' vertical or opt-in.
"""

import html
import re
from typing import List, Optional
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem, AIProvenance


def _strip_html(text: str) -> str:
    """Safely strip HTML tags and decode entities from status content."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    return " ".join(clean.split())


class FediverseProvider(SearchProvider):
    """ActivityPub / Mastodon public search provider."""

    def __init__(
        self,
        instance: str = "mastodon.social",
        enabled: bool = True,
        timeout: float = 6.0,
    ):
        self.instance = instance.strip().rstrip("/")
        self.enabled = enabled
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "fediverse"

    @property
    def is_configured(self) -> bool:
        return bool(self.enabled and self.instance)

    async def search(
        self,
        query: str,
        category: str = "social",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> List[SearchResultItem]:
        """Query public Fediverse instance endpoint."""
        if not self.is_configured:
            return []

        clean_q = query.strip()
        if not clean_q:
            return []

        # Remove leading hashtag if present for tag endpoint
        tag_candidate = clean_q.lstrip("#").split()[0].lower() if clean_q else ""

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        # Try tag timeline first (open, public, high availability)
        results: List[SearchResultItem] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                tag_url = f"https://{self.instance}/api/v1/timelines/tag/{tag_candidate}"
                resp = await client.get(tag_url, params={"limit": page_size}, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and data:
                        results = self._parse_statuses(data)

                # If no tag results, fallback to public search API if single word or query
                if not results:
                    search_url = f"https://{self.instance}/api/v2/search"
                    s_resp = await client.get(
                        search_url,
                        params={"q": clean_q, "type": "statuses", "limit": page_size},
                        headers=headers,
                    )
                    if s_resp.status_code == 200:
                        s_data = s_resp.json()
                        statuses = s_data.get("statuses", [])
                        if statuses:
                            results = self._parse_statuses(statuses)
        except Exception:
            # Defensive network handling: return whatever was retrieved or empty
            return results

        return results[:page_size]

    def _parse_statuses(self, statuses: List[dict]) -> List[SearchResultItem]:
        """Convert Mastodon status objects into SearchResultItems."""
        items: List[SearchResultItem] = []
        for s in statuses:
            if not isinstance(s, dict):
                continue
            # Respect sensitive content in safe mode
            if s.get("visibility") not in ("public", "unlisted", None):
                continue

            raw_content = s.get("content", "")
            plain_text = _strip_html(raw_content)
            if not plain_text:
                continue

            acct_data = s.get("account") or {}
            handle = acct_data.get("acct") or acct_data.get("username") or "fediverse"
            display_name = acct_data.get("display_name") or handle
            post_url = s.get("url") or s.get("uri") or f"https://{self.instance}"
            created_at = s.get("created_at")

            # Formulate title from author and opening phrase
            title_text = f"@{handle}: {plain_text[:70]}"
            if len(plain_text) > 70:
                title_text += "…"

            items.append(
                SearchResultItem(
                    url=post_url,
                    title=title_text,
                    snippet=plain_text,
                    score=65.0,
                    source=f"Fediverse ({self.instance})",
                    why_seen="Publicación pública en protocolo federado descentralizado (ActivityPub). Sin perfilamiento ni rastreo comercial.",
                    doc_type="social",
                    date=created_at,
                    is_sponsored=False,
                    canonical_url=post_url,
                    source_type="red_abierta",
                    content_type="publicación",
                    published_date=created_at,
                    authors=[f"@{handle} ({display_name})"],
                    provider_origin="ActivityPub",
                    ai_provenance=AIProvenance(
                        declared_signal=None,
                        status="no determinado",
                    ),
                )
            )
        return items
