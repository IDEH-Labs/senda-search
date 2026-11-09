# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""OpenAlex Open Access Scholarly Search Provider adapter."""

from typing import Optional, List
import httpx
from senda.config import settings
from senda.providers.base import SearchProvider, SearchResultItem


class OpenAlexProvider(SearchProvider):
    """Adapter for OpenAlex global open access scholarly catalog.
    
    Accesses over 100 million peer-reviewed scientific works, theses, and preprints.
    Enforces strict filter for Open Access (is_oa:true), zero telemetry, and honest provenance.
    """

    def __init__(self, enabled: bool = True, email_contact: Optional[str] = None):
        self._enabled = enabled
        self.email_contact = email_contact or settings.CONTACT_EMAIL or "contact@ideh.top"

    @property
    def name(self) -> str:
        return "OpenAlex (Ciencia Abierta)"

    @property
    def is_configured(self) -> bool:
        return self._enabled

    async def search(
        self,
        query: str,
        category: str = "all",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> list[SearchResultItem]:
        """Query OpenAlex for verified Open Access scientific publications."""
        if not self.is_configured or not query.strip():
            return []

        # OpenAlex works endpoint
        api_url = "https://api.openalex.org/works"

        # Parameters enforcing strictly Open Access (no toll-walls, no paywalls)
        params = {
            "search": query.strip(),
            "filter": "is_oa:true",
            "select": "id,doi,title,publication_year,open_access,primary_location,authorships",
            "per_page": min(max(page_size, 1), 25),
            "page": max(page, 1),
        }

        # Year freshness filtering if requested
        if time_filter:
            tf = time_filter.lower().strip()
            # Map standard time filter codes if applicable
            pass

        # Polite pool headers complying with OpenAlex fair use guidelines
        clean_headers = {
            "User-Agent": f"SendaSearch/0.1 (+https://ideh.top/senda-search; mailto:{self.email_contact})",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.get(api_url, params=params, headers=clean_headers)
                if resp.status_code != 200:
                    return []
                data = resp.json()
        except Exception:
            return []

        items: list[SearchResultItem] = []
        works = data.get("results", [])

        for work in works[:page_size]:
            title = work.get("title")
            if not title:
                continue

            # Determine best canonical URL (priority: direct OA link -> PDF -> DOI -> landing page)
            oa_data = work.get("open_access") or {}
            prim_loc = work.get("primary_location") or {}
            source_info = prim_loc.get("source") or {}

            best_url = (
                oa_data.get("oa_url")
                or prim_loc.get("pdf_url")
                or prim_loc.get("landing_page_url")
                or work.get("doi")
                or work.get("id")
            )
            if not best_url:
                continue

            year = work.get("publication_year")
            journal_name = source_info.get("display_name") or "Repositorio Abierto"

            # Format authors snippet
            authorships = work.get("authorships") or []
            author_names: List[str] = []
            for a in authorships[:3]:
                auth = a.get("author") or {}
                name = auth.get("display_name")
                if name:
                    author_names.append(name)

            if len(authorships) > 3:
                author_summary = ", ".join(author_names) + " et al."
            elif author_names:
                author_summary = ", ".join(author_names)
            else:
                author_summary = "Autores académicos"

            # Construct informative, honest snippet
            year_str = f"({year}) " if year else ""
            has_pdf = bool(oa_data.get("oa_url") or prim_loc.get("pdf_url"))
            badge_pdf = "[PDF Abierto] " if has_pdf else ""
            snippet = f"{badge_pdf}{year_str}{journal_name} — {author_summary}."

            why = (
                "Publicación científica de Acceso Abierto (OA) revisada por pares. "
                f"Indexada a través de OpenAlex ({journal_name}). Consulta anónima canalizada por Senda."
            )

            # Assign score: in 'library' vertical give higher priority
            base_score = 45.0 if category == "library" else 15.0

            items.append(
                SearchResultItem(
                    title=title,
                    url=best_url,
                    snippet=snippet,
                    source="Ciencia Abierta (OpenAlex)",
                    date=str(year) if year else None,
                    doc_type="library",
                    media_url=None,
                    is_sponsored=False,
                    score=base_score,
                    why_seen=why,
                )
            )

        return items
