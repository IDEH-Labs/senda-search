# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Sovereign and Open Video Search Provider querying federated PeerTube and Internet Archive."""

import urllib.parse
from typing import List, Optional
import httpx

from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds into human-readable MM:SS or HH:MM:SS."""
    if not seconds or seconds <= 0:
        return ""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class EthicalVideoProvider(SearchProvider):
    """Federated and public video search provider (PeerTube SepiaSearch & Internet Archive)."""

    def __init__(
        self,
        timeout: float = 6.0,
        enabled: bool = True,
    ):
        self.timeout = timeout
        self.enabled = enabled

    @property
    def name(self) -> str:
        return "ethical_videos"

    @property
    def is_configured(self) -> bool:
        return self.enabled

    async def search(
        self,
        query: str,
        category: str = "videos",
        page: int = 1,
        page_size: int = 12,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> List[SearchResultItem]:
        """Search videos across federated PeerTube (SepiaSearch) with Internet Archive fallback."""
        clean_q = query.strip()
        if not clean_q or not self.is_configured:
            return []

        items: List[SearchResultItem] = []
        start_idx = max(0, (page - 1) * page_size)

        # 1. Primary: SepiaSearch (PeerTube federated network by Framasoft)
        encoded_q = urllib.parse.quote_plus(clean_q)
        peertube_url = f"https://sepiasearch.org/api/v1/search/videos?search={encoded_q}&count={page_size}&start={start_idx}"

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(peertube_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    for v in data.get("data", []):
                        item = self._parse_peertube_item(v)
                        if item:
                            items.append(item)
        except Exception:
            pass

        # 2. Secondary fallback / enrichment: Internet Archive Movies API if items < page_size
        if len(items) < page_size:
            archive_needed = page_size - len(items)
            archive_url = (
                f"https://archive.org/advancedsearch.php?q={encoded_q}+AND+mediatype:movies"
                f"&fl[]=identifier,title,description,duration,year,publicdate&rows={archive_needed}&page={page}&output=json"
            )
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    resp = await client.get(archive_url, headers=headers)
                    if resp.status_code == 200:
                        docs = resp.json().get("response", {}).get("docs", [])
                        for d in docs:
                            item = self._parse_archive_item(d)
                            if item:
                                items.append(item)
            except Exception:
                pass

        return items[:page_size]

    def _parse_peertube_item(self, v: dict) -> Optional[SearchResultItem]:
        """Convert a SepiaSearch PeerTube video payload into a SearchResultItem."""
        url = v.get("url")
        title = v.get("name")
        if not url or not title:
            return None

        duration_sec = v.get("duration")
        duration_str = format_duration(duration_sec)

        channel_info = v.get("channel") or {}
        channel_name = channel_info.get("displayName") or channel_info.get("name") or "PeerTube"
        account_info = v.get("account") or {}
        account_name = account_info.get("displayName") or account_info.get("name") or ""
        authors = [a for a in (channel_name, account_name) if a]

        # Thumbnail handling
        thumbnail = v.get("thumbnailUrl") or v.get("previewUrl")

        # Views count
        views = v.get("views")
        views_str = f" · {views:,} vistas".replace(",", ".") if views is not None else ""

        snippet = v.get("truncatedDescription") or ""
        if duration_str:
            snippet = f"[{duration_str}{views_str}] {snippet}".strip()

        published_date = v.get("originallyPublishedAt") or v.get("publishedAt")

        return SearchResultItem(
            title=title.strip(),
            url=url,
            snippet=snippet.strip(),
            source=channel_name,
            media_url=thumbnail,
            doc_type="videos",
            source_type="plataforma_abierta",
            content_type="video",
            published_date=published_date,
            date=published_date,
            authors=authors,
            provider_origin="PeerTube / SepiaSearch",
            why_seen="Video federado y abierto en PeerTube (red libre descentralizada) sin rastreo publicitario.",
        )

    def _parse_archive_item(self, d: dict) -> Optional[SearchResultItem]:
        """Convert an Internet Archive movie document into a SearchResultItem."""
        ident = d.get("identifier")
        title = d.get("title")
        if not ident or not title:
            return None

        url = f"https://archive.org/details/{ident}"
        thumbnail = f"https://archive.org/services/img/{ident}"
        snippet = d.get("description") or "Video y película preservada en Internet Archive."
        if isinstance(snippet, list):
            snippet = " ".join(snippet)

        duration = d.get("duration")
        if duration:
            snippet = f"[{duration}] {snippet}".strip()

        date = d.get("publicdate") or d.get("year")

        return SearchResultItem(
            title=title.strip(),
            url=url,
            snippet=snippet.strip(),
            source="Internet Archive",
            media_url=thumbnail,
            doc_type="videos",
            source_type="primaria_oficial",
            content_type="video",
            published_date=str(date) if date else None,
            date=str(date) if date else None,
            provider_origin="Internet Archive",
            why_seen="Video y filmoteca histórica preservada de dominio público o Creative Commons en Internet Archive.",
        )
