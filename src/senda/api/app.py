# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""FastAPI Web Application and Sovereign REST API for Senda Search Engine."""

from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Optional, List
import urllib.parse
from fastapi import FastAPI, Request, Query, Header, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from senda.config import settings
from senda.indexer.storage import StorageEngine
from senda.ranking.retriever import SearchRetriever, SearchResultSet
from senda.providers.aggregator import ProviderAggregator, BANG_SHORTCUTS
from senda.providers.searxng import SearXNGProvider
from senda.providers.brave import BraveSearchProvider
from senda.providers.mojeek import MojeekProvider
from senda.providers.internal import InternalStorageProvider
from senda.providers.openalex import OpenAlexProvider
from senda.providers.fediverse import FediverseProvider
from senda.providers.bluesky import BlueskyProvider
from senda.providers.wikipedia import WikipediaEntityProvider, WikipediaSearchProvider
from senda.providers.news import RealTimeNewsProvider
from senda.providers.images import FreeCultureImageProvider
from senda.providers.videos import EthicalVideoProvider
from senda.providers.crossref import CrossrefProvider
from senda.providers.doaj import DoajProvider
from senda.providers.arxiv import ArxivProvider
from senda.providers.pubmed import PubMedProvider
from senda.providers.base import SearchResultItem
from senda.ai.grounded_synthesis import GroundedSynthesizer
from senda.countries import get_country_name, get_countries_grouped
from senda.calculator import evaluate_math_query
from senda.providers.weather import WeatherProvider
from senda.converters import convert_query
from senda.worldtime import get_world_time
from senda.reader import SovereignReader
from senda.crawler.network_guard import SSRFSecurityViolation
from senda.ranking.goggles import get_available_goggles
from senda.ranking.suggestions import SuggestionEngine
from senda.i18n import (
    resolve_language,
    translate,
    get_translation_catalog,
    detect_query_language,
    SUPPORTED_LANGUAGES,
)


# Pydantic schemas for API documentation and validation
class SearchItemModel(BaseModel):
    url: str
    domain: str
    title: str
    snippet: str
    relevance_score: float
    doc_type: str = "web"
    media_url: Optional[str] = None
    published_at: Optional[str] = None
    license: Optional[str] = None
    source: str = "Senda"
    why_seen: str = ""
    is_sponsored: bool = False

    # Verifiable provenance fields
    canonical_url: Optional[str] = None
    source_type: str = "desconocida"
    content_type: str = "desconocido"
    published_date: Optional[str] = None
    updated_date: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    retraction: Optional[dict] = None
    primary_citations: list[str] = Field(default_factory=list)
    verifications: list[dict] = Field(default_factory=list)
    security_signals: list[str] = Field(default_factory=list)
    source_score: Optional[dict] = None
    provider_origin: str = "Senda"
    ai_provenance: Optional[dict] = None


class SearchResponseModel(BaseModel):
    query: str
    total_matches: int
    page: int
    page_size: int
    total_pages: int
    duration_ms: float
    category: str = "all"
    sort: Optional[str] = None
    time_filter: Optional[str] = None
    items: list[SearchItemModel]
    grounded_synthesis: Optional[dict] = None
    entity_card: Optional[dict] = None
    calculator: Optional[dict] = None
    weather: Optional[dict] = None
    conversion: Optional[dict] = None
    world_time: Optional[dict] = None
    goggle: Optional[str] = None
    custom_goggle: Optional[str] = None
    goggles_catalog: Optional[list] = None
    did_you_mean: Optional[str] = None
    auto_corrected: bool = False
    corrected_query: Optional[str] = None
    original_query: Optional[str] = None


class StatsResponseModel(BaseModel):
    total_documents: int
    total_domains: int
    database_size_bytes: int
    database_path: str


class TakedownRequest(BaseModel):
    domain: Optional[str] = Field(default=None, description="Domain to completely purge.")
    url: Optional[str] = Field(default=None, description="Specific URL to purge.")
    reason: Optional[str] = Field(default=None, description="Reason for removal.")


def create_app(
    storage: Optional[StorageEngine] = None,
    openalex_provider: Optional[OpenAlexProvider] = None,
    enable_federated_providers: bool = True,
) -> FastAPI:
    """Create and configure the sovereign FastAPI application."""
    app = FastAPI(
        title="Senda Search Engine",
        description="Independent, verifiable, privacy-first search engine API.",
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url=None,
    )

    # Resolve static and template directories
    base_dir = Path(__file__).resolve().parent.parent
    static_dir = base_dir / "ui" / "static"
    templates_dir = base_dir / "ui" / "templates"

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    templates = Jinja2Templates(directory=str(templates_dir))

    def format_human_date(value: Optional[str]) -> str:
        """Format ISO 8601 publication dates into friendly human recency strings."""
        if not value:
            return ""
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = now - dt
            seconds = delta.total_seconds()
            if seconds < 0:
                return "Hace instantes"
            if seconds < 60:
                return "Hace segundos"
            if seconds < 3600:
                minutes = max(1, int(seconds // 60))
                return f"Hace {minutes} min"
            if seconds < 86400:
                hours = max(1, int(seconds // 3600))
                return f"Hace {hours} h"
            if seconds < 86400 * 7:
                days = max(1, int(seconds // 86400))
                return f"Hace {days} d"
            if seconds < 86400 * 30:
                weeks = max(1, int(seconds // (86400 * 7)))
                return f"Hace {weeks} sem"
            if seconds < 86400 * 365:
                months = max(1, int(seconds // (86400 * 30)))
                return f"Hace {months} m"
            years = max(1, int(seconds // (86400 * 365)))
            return f"Hace {years} a"
        except Exception:
            return str(value)[:10]

    templates.env.filters["human_date"] = format_human_date

    # Initialize storage, retrieval and multi-provider aggregator
    app_storage = storage or StorageEngine()
    app_retriever = SearchRetriever(app_storage)

    internal_prov = InternalStorageProvider(app_storage)
    searxng_prov = SearXNGProvider(settings.SEARXNG_URL)
    brave_prov = BraveSearchProvider(settings.BRAVE_API_KEY)
    mojeek_prov = MojeekProvider(settings.MOJEEK_API_KEY)
    openalex_prov = openalex_provider or OpenAlexProvider(
        api_key=settings.OPENALEX_API_KEY,
        enabled=settings.OPENALEX_ENABLED,
    )
    fediverse_prov = FediverseProvider(
        instance=settings.FEDIVERSE_INSTANCE,
        enabled=settings.FEDIVERSE_ENABLED,
    )
    bluesky_prov = BlueskyProvider(
        endpoint=settings.BLUESKY_ENDPOINT,
        enabled=settings.BLUESKY_ENABLED,
    )

    wiki_search_prov = WikipediaSearchProvider() if enable_federated_providers else None
    news_prov = RealTimeNewsProvider() if enable_federated_providers else None
    images_prov = FreeCultureImageProvider() if enable_federated_providers else None
    videos_prov = EthicalVideoProvider() if enable_federated_providers else None
    crossref_prov = CrossrefProvider() if enable_federated_providers else None
    doaj_prov = DoajProvider() if enable_federated_providers else None
    arxiv_prov = ArxivProvider() if enable_federated_providers else None
    pubmed_prov = PubMedProvider() if enable_federated_providers else None

    app_synthesizer = GroundedSynthesizer(enabled=settings.ENABLE_AI_SYNTHESIS)
    app_wiki_entity = WikipediaEntityProvider()
    app_weather = WeatherProvider()
    app_reader = SovereignReader()
    app_suggestions = SuggestionEngine()

    app_aggregator = ProviderAggregator(
        internal_provider=internal_prov,
        searxng_provider=searxng_prov,
        brave_provider=brave_prov,
        mojeek_provider=mojeek_prov,
        openalex_provider=openalex_prov,
        fediverse_provider=fediverse_prov,
        bluesky_provider=bluesky_prov,
        wikipedia_search_provider=wiki_search_prov,
        news_provider=news_prov,
        image_provider=images_prov,
        video_provider=videos_prov,
        crossref_provider=crossref_prov,
        doaj_provider=doaj_prov,
        arxiv_provider=arxiv_prov,
        pubmed_provider=pubmed_prov,
    )

    # Privacy and Hardening Middleware
    @app.middleware("http")
    async def sovereign_privacy_headers(request: Request, call_next):
        """Enforce zero-leakage HTTP security headers on all responses."""
        response = await call_next(request)
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "interest-cohort=(), geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src * data:; "
            "frame-ancestors 'none';"
        )
        # Advertise Tor Onion Service to Tor Browser per RFC / Tor Project standard
        if settings.ONION_HOST:
            onion_raw = settings.ONION_HOST.strip().rstrip("/")
            if not onion_raw.startswith("http://") and not onion_raw.startswith("https://"):
                onion_raw = f"http://{onion_raw}"
            q_part = f"?{request.url.query}" if request.url.query else ""
            response.headers["Onion-Location"] = f"{onion_raw}{request.url.path}{q_part}"

        return response

    @app.middleware("http")
    async def head_request_middleware(request: Request, call_next):
        """Handle RFC 9110 HTTP HEAD requests by serving headers without payload body."""
        is_head = request.method == "HEAD"
        if is_head:
            request.scope["method"] = "GET"
        response = await call_next(request)
        if is_head:
            return Response(
                content=b"",
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        return response

    def resolve_theme(request: Request, query_theme: Optional[str] = None) -> str:
        """Resolve theme: query parameter > cookie > default ('dark')."""
        if query_theme in ("light", "dark"):
            return query_theme
        cookie_val = request.cookies.get("senda_theme")
        if cookie_val in ("light", "dark"):
            return cookie_val
        return "dark"

    def render_with_theme(
        name: str,
        request: Request,
        context: dict,
        query_theme: Optional[str] = None,
        query_lang: Optional[str] = None,
    ) -> Response:
        """Render template with theme, multilingual i18n, and optionally set functional preference cookies."""
        current_theme = resolve_theme(request, query_theme)
        current_lang = resolve_language(request, query_lang or request.query_params.get("lang"))
        catalog = get_translation_catalog(current_lang)

        next_theme = "light" if current_theme == "dark" else "dark"
        next_theme_url_obj = request.url.include_query_params(theme=next_theme)
        theme_toggle_url = next_theme_url_obj.path + ("?" + next_theme_url_obj.query if next_theme_url_obj.query else "")

        home_params = {}
        if current_theme != "dark":
            home_params["theme"] = current_theme
        if current_lang != "es":
            home_params["lang"] = current_lang
        home_query = urllib.parse.urlencode(home_params)
        home_url = f"/?{home_query}" if home_query else "/"

        ctx = dict(context)
        ctx["theme"] = current_theme
        ctx["theme_toggle_url"] = theme_toggle_url
        ctx["home_url"] = home_url
        ctx["lang"] = current_lang
        ctx["tr"] = catalog
        ctx["supported_languages"] = SUPPORTED_LANGUAGES
        ctx["settings"] = settings
        ctx["countries_grouped"] = get_countries_grouped()
        ctx["current_country_name"] = get_country_name(context.get("region"))
        resp = templates.TemplateResponse(request=request, name=name, context=ctx)
        if query_theme in ("light", "dark"):
            resp.set_cookie(
                key="senda_theme",
                value=current_theme,
                max_age=31536000,
                samesite="lax",
                path="/",
                httponly=False,
            )
        if query_lang and query_lang.lower().strip()[:2] in SUPPORTED_LANGUAGES:
            resp.set_cookie(
                key="senda_lang",
                value=current_lang,
                max_age=31536000,
                samesite="lax",
                path="/",
                httponly=False,
            )
        return resp

    @app.get("/", response_class=HTMLResponse)
    async def home(
        request: Request,
        theme: Optional[str] = Query(default=None),
        lang: Optional[str] = Query(default=None),
    ):
        """Render search homepage."""
        return render_with_theme("index.html", request, {}, theme, lang)

    @app.get("/about", response_class=HTMLResponse)
    async def about(
        request: Request,
        theme: Optional[str] = Query(default=None),
        lang: Optional[str] = Query(default=None),
    ):
        """Render about and ethics page."""
        return render_with_theme("about.html", request, {}, theme, lang)

    @app.get("/how-it-works", response_class=HTMLResponse)
    async def how_it_works(
        request: Request,
        theme: Optional[str] = Query(default=None),
        lang: Optional[str] = Query(default=None),
    ):
        """Render plain language How It Works transparency page."""
        return render_with_theme("how_it_works.html", request, {}, theme, lang)

    @app.get("/privacy", response_class=HTMLResponse)
    async def privacy(
        request: Request,
        theme: Optional[str] = Query(default=None),
        lang: Optional[str] = Query(default=None),
    ):
        """Render verifiable privacy policy."""
        return render_with_theme("privacy.html", request, {}, theme, lang)

    @app.get("/javascript", response_class=HTMLResponse)
    async def javascript_licenses(
        request: Request,
        theme: Optional[str] = Query(default=None),
        lang: Optional[str] = Query(default=None),
    ):
        """GNU LibreJS Web Labels page declaring Free JavaScript licenses."""
        return render_with_theme("javascript.html", request, {}, theme, lang)

    @app.get("/reader")
    async def reader_view(
        url: str = Query(default="", description="URL de la página a leer"),
    ):
        """Redirect legacy reader mode requests directly to target URL (browsers natively feature reader mode)."""
        clean_url = url.strip()
        if clean_url and (clean_url.startswith("http://") or clean_url.startswith("https://")):
            return RedirectResponse(url=clean_url, status_code=302)
        return RedirectResponse(url="/", status_code=302)

    @app.get("/opensearch.xml")
    async def opensearch(request: Request):
        """OpenSearch 1.1 Description Document for auto-discovery by web browsers."""
        base_url = str(request.base_url).rstrip("/")
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>{settings.APP_NAME}</ShortName>
    <Description>{settings.APP_NAME} — Buscador web libre y ético</Description>
    <InputEncoding>UTF-8</InputEncoding>
    <Image width="16" height="16" type="image/png">{base_url}/static/img/favicon.png</Image>
    <Image width="64" height="64" type="image/png">{base_url}/static/img/senda-icon-48.png</Image>
    <Url type="text/html" method="get" template="{base_url}/search?q={{searchTerms}}"/>
    <Url type="application/x-suggestions+json" method="get" template="{base_url}/api/v1/search?q={{searchTerms}}"/>
</OpenSearchDescription>"""
        return Response(content=xml_content, media_type="application/opensearchdescription+xml")

    @app.get("/manifest.webmanifest")
    async def webmanifest(request: Request):
        """PWA Web App Manifest declaring Senda icons and theme colors."""
        manifest = {
            "name": settings.APP_NAME,
            "short_name": settings.APP_NAME,
            "description": "Buscador web ético, rápido y privado",
            "start_url": "/",
            "display": "minimal-ui",
            "background_color": "#080c14",
            "theme_color": "#080c14",
            "icons": [
                {
                    "src": "/static/img/senda-icon-48.png",
                    "sizes": "48x48",
                    "type": "image/png"
                },
                {
                    "src": "/static/img/senda-icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/img/senda-icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/img/senda-symbol-adaptive.svg",
                    "sizes": "512x512",
                    "type": "image/svg+xml"
                }
            ]
        }
        return JSONResponse(content=manifest, media_type="application/manifest+json")

    @app.get("/search")
    async def search(
        request: Request,
        q: str = Query(default="", max_length=256),
        category: str = Query(default="all"),
        p: int = Query(default=1, ge=1),
        page: int = Query(default=1, ge=1),
        format: Optional[str] = Query(default=None),
        accept: Optional[str] = Header(default=None),
        time_filter: Optional[str] = Query(default=None),
        sort: Optional[str] = Query(default=None),
        region: Optional[str] = Query(default=settings.DEFAULT_REGION),
        safe_search: str = Query(default="off"),
        no_ads: bool = Query(default=True),
        academic: bool = Query(default=False),
        social: bool = Query(default=False),
        synthesis: bool = Query(default=False),
        goggle: Optional[str] = Query(default=None),
        custom_goggle: Optional[str] = Query(default=None),
        anti_slop: bool = Query(default=True),
        clustering: bool = Query(default=True),
        literal: bool = Query(default=False),
        theme: Optional[str] = Query(default=None),
        lang: Optional[str] = Query(default=None),
    ):
        """Search endpoint supporting HTML rendering and JSON content negotiation across verticals."""
        clean_q = q.strip()
        is_literal = literal or (clean_q.startswith('"') and clean_q.endswith('"'))
        auto_corrected = False
        corrected_query: Optional[str] = None
        original_query: Optional[str] = None
        did_you_mean: Optional[str] = None

        user_lang = resolve_language(request, lang)
        query_lang = detect_query_language(clean_q, fallback_lang=user_lang)
        p_val = p if isinstance(p, int) else 1
        page_val = page if isinstance(page, int) else 1
        current_page = max(p_val, page_val)
        reg = region if isinstance(region, str) else settings.DEFAULT_REGION
        tf = time_filter if isinstance(time_filter, str) else None
        sort_val = sort.lower().strip() if isinstance(sort, str) and sort.strip() else None
        ss = safe_search if isinstance(safe_search, str) else "off"
        na = no_ads if isinstance(no_ads, bool) else True
        ac = academic if isinstance(academic, bool) else False
        soc = social if isinstance(social, bool) else False
        synth = synthesis if isinstance(synthesis, bool) else False
        goggle_val = goggle.strip() if isinstance(goggle, str) and goggle.strip() else None
        custom_goggle_val = custom_goggle.strip() if isinstance(custom_goggle, str) and custom_goggle.strip() else None

        # Bang shortcuts: redirect immediately to target without intermediate tracking
        bang_redir = ProviderAggregator.detect_bang(clean_q)
        if bang_redir:
            dest_url, _ = bang_redir
            return RedirectResponse(url=dest_url, status_code=302)

        # Maps vertical redirect to OpenStreetMap
        cat = category.lower().strip()
        if cat == "maps":
            osm_url = f"https://www.openstreetmap.org/search?query={urllib.parse.quote_plus(clean_q)}"
            return RedirectResponse(url=osm_url, status_code=302)

        if cat not in ("all", "web", "news", "images", "videos", "library", "social", "smallweb", "community"):
            cat = "all"

        # News defaults to freshest date sorting unless user explicitly opted for relevance
        if cat == "news" and not sort_val:
            sort_val = "date"

        page_sz = 12 if cat == "images" else 10
        start_t = time.perf_counter()

        # Multi-provider aggregated search (OpenAlex strictly opt-in/library; Social strictly opt-in/social)
        items_list = await app_aggregator.aggregate(
            query=clean_q,
            category=cat,
            page=current_page,
            page_size=page_sz,
            time_filter=tf,
            sort=sort_val,
            region=reg,
            safe_search=ss,
            no_ads=na,
            opt_in_academic=ac,
            opt_in_social=(cat == "social" or soc),
            goggle=goggle_val,
            custom_goggle=custom_goggle_val,
            anti_slop=anti_slop,
            clustering=clustering,
        )

        # Typo tolerance & Did-you-mean engine (Sovereign, non-tracking, offline-first)
        if not is_literal and clean_q and len(clean_q) >= 3:
            if len(items_list) == 0:
                # Case A: Zero results found for imprecise query -> suggest & auto-fallback
                suggested_q = await app_suggestions.suggest(clean_q, lang=query_lang)
                if suggested_q and suggested_q.lower() != clean_q.lower():
                    fallback_items = await app_aggregator.aggregate(
                        query=suggested_q,
                        category=cat,
                        page=current_page,
                        page_size=page_sz,
                        time_filter=tf,
                        sort=sort_val,
                        region=reg,
                        safe_search=ss,
                        no_ads=na,
                        opt_in_academic=ac,
                        opt_in_social=(cat == "social" or soc),
                        goggle=goggle_val,
                        custom_goggle=custom_goggle_val,
                        anti_slop=anti_slop,
                        clustering=clustering,
                    )
                    if len(fallback_items) > 0:
                        items_list = fallback_items
                        auto_corrected = True
                        corrected_query = suggested_q
                        original_query = clean_q
                    else:
                        did_you_mean = suggested_q
            else:
                # Case B: Results exist, but check if there's an authoritative suggestion
                suggested_q = await app_suggestions.suggest(clean_q, lang=query_lang)
                if suggested_q and suggested_q.lower() != clean_q.lower():
                    did_you_mean = suggested_q

        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)

        # Fallback to local retriever counts for pagination estimation
        search_q_for_local = corrected_query if auto_corrected and corrected_query else clean_q
        local_res = app_retriever.search(search_q_for_local, page=current_page, page_size=page_sz, category=cat if cat != "all" else "all")
        total_matches = max(len(items_list), local_res.total_matches)
        total_pages = max(1, (total_matches + page_sz - 1) // page_sz) if total_matches > 0 else 1

        formatted_items = []
        for it in items_list:
            # Prioritize verified source_domain or publisher over syndicated aggregator URLs
            source_dom = getattr(it, "source_domain", None)
            item_dom = getattr(it, "domain", None)
            url_netloc = ""
            try:
                url_netloc = urllib.parse.urlparse(it.url).netloc.lower()
            except Exception:
                pass

            resolved_domain = source_dom or (item_dom if item_dom and item_dom != "news.google.com" else "") or url_netloc
            if resolved_domain.startswith("www."):
                resolved_domain = resolved_domain[4:]

            # Never allow news.google.com syndication domain to shadow authentic editorial outlets
            if not resolved_domain or resolved_domain == "news.google.com":
                publisher_name = getattr(it, "source", "") or ""
                if publisher_name and publisher_name not in ("Senda", "Google", "news.google.com"):
                    clean_pub = publisher_name.lower().replace(" ", "").replace("«", "").replace("»", "")
                    resolved_domain = clean_pub if "." in clean_pub else f"{clean_pub}.com"
                else:
                    resolved_domain = "prensa"

            domain_name = resolved_domain
            
            # Map verifiable provenance fields safely
            retraction_dict = None
            if it.retraction:
                retraction_dict = {
                    "estado": it.retraction.status,
                    "fuente": it.retraction.source,
                    "fecha": it.retraction.date,
                    "notice_url": it.retraction.notice_url,
                }

            verif_list = [
                {
                    "verificador": v.verifier,
                    "veredicto_atribuido": v.attributed_verdict,
                    "url": v.url,
                    "fecha": v.date,
                }
                for v in (it.verifications or [])
            ]

            score_dict = None
            if it.source_score:
                score_dict = {
                    "versión_rúbrica": it.source_score.rubric_version,
                    "factores": it.source_score.factores,
                    "nota": it.source_score.nota,
                }

            ai_dict = None
            if it.ai_provenance:
                if isinstance(it.ai_provenance, dict):
                    ai_dict = it.ai_provenance
                else:
                    ai_dict = {
                        "señal_declarada": getattr(it.ai_provenance, "declared_signal", None) or getattr(it.ai_provenance, "señal_declarada", None),
                        "estado": getattr(it.ai_provenance, "status", None) or getattr(it.ai_provenance, "estado", "no determinado"),
                    }

            formatted_items.append(
                SearchItemModel(
                    url=it.url,
                    domain=domain_name,
                    title=it.title,
                    snippet=it.snippet,
                    relevance_score=it.score,
                    doc_type=it.doc_type,
                    media_url=it.media_url,
                    published_at=it.date,
                    source=it.source,
                    why_seen=it.why_seen,
                    is_sponsored=it.is_sponsored,
                    canonical_url=it.canonical_url or it.url,
                    source_type=it.source_type,
                    content_type=it.content_type,
                    published_date=it.published_date or it.date,
                    updated_date=it.updated_date,
                    authors=it.authors,
                    corrections=it.corrections,
                    retraction=retraction_dict,
                    primary_citations=it.primary_citations,
                    verifications=verif_list,
                    security_signals=it.security_signals,
                    source_score=score_dict,
                    provider_origin=it.provider_origin,
                    ai_provenance=ai_dict,
                )
            )

        card_query = corrected_query if auto_corrected and corrected_query else clean_q

        # Grounded AI Synthesis (Strictly grounded in retrieved items; never hallucinates)
        grounded_data = None
        if (settings.ENABLE_AI_SYNTHESIS or synth) and clean_q:
            synth_res = app_synthesizer.synthesize(card_query, items_list, force=synth)
            if synth_res:
                grounded_data = synth_res.model_dump()

        # Verifiable Encyclopedic Entity Card (Wikipedia & Wikidata on-demand)
        entity_data = None
        if current_page == 1 and card_query and cat in ("all", "web", "library"):
            entity_card_obj = await app_wiki_entity.get_entity(card_query, lang=query_lang, fetch_official_website=True)
            if entity_card_obj:
                entity_data = entity_card_obj.model_dump()

        # Instant Sovereign Calculator Card
        calculator_data = None
        if current_page == 1 and clean_q:
            calc_obj = evaluate_math_query(clean_q)
            if calc_obj:
                calculator_data = calc_obj.model_dump()

        # Instant Sovereign Unit & Currency Converter Card
        conversion_data = None
        if current_page == 1 and clean_q:
            conv_obj = await convert_query(clean_q)
            if conv_obj:
                conversion_data = conv_obj.model_dump()

        # Instant Sovereign World Time Card
        world_time_data = None
        if current_page == 1 and clean_q:
            wt_obj = get_world_time(clean_q)
            if wt_obj:
                world_time_data = wt_obj.model_dump()

        # Instant Sovereign Real-Time Weather Card (Open-Meteo Open Data)
        weather_data = None
        if current_page == 1 and clean_q and cat in ("all", "web"):
            weather_card_obj = await app_weather.get_weather(clean_q)
            if weather_card_obj:
                weather_data = weather_card_obj.model_dump()

        results_data = SearchResponseModel(
            query=clean_q,
            total_matches=total_matches,
            page=current_page,
            page_size=page_sz,
            total_pages=total_pages,
            duration_ms=duration_ms,
            category=cat,
            sort=sort_val,
            time_filter=tf,
            items=formatted_items,
            grounded_synthesis=grounded_data,
            entity_card=entity_data,
            calculator=calculator_data,
            weather=weather_data,
            conversion=conversion_data,
            world_time=world_time_data,
            goggle=goggle_val,
            custom_goggle=custom_goggle_val,
            goggles_catalog=get_available_goggles(),
            did_you_mean=did_you_mean,
            auto_corrected=auto_corrected,
            corrected_query=corrected_query,
            original_query=original_query,
        )

        # Content negotiation
        if format == "json" or (accept and "application/json" in accept and not ("text/html" in accept)):
            return results_data

        return render_with_theme(
            "results.html",
            request,
            {
                "query": clean_q,
                "category": cat,
                "results": results_data,
                "region": reg,
                "time_filter": tf,
                "sort": sort_val,
                "safe_search": ss,
                "grounded_synthesis": grounded_data,
                "entity_card": entity_data,
                "calculator": calculator_data,
                "weather": weather_data,
                "conversion": conversion_data,
                "world_time": world_time_data,
                "goggle": goggle_val,
                "custom_goggle": custom_goggle_val,
                "goggles_catalog": get_available_goggles(),
                "anti_slop": anti_slop,
                "clustering": clustering,
                "synthesis": synth,
                "did_you_mean": did_you_mean,
                "auto_corrected": auto_corrected,
                "corrected_query": corrected_query,
                "original_query": original_query,
                "literal": is_literal,
            },
            query_theme=theme,
            query_lang=lang,
        )

    @app.post("/search")
    async def post_search(
        request: Request,
        format: Optional[str] = Query(default=None),
        accept: Optional[str] = Header(default=None),
    ):
        """Search endpoint for POST requests (prevents search queries from lingering in browser history)."""
        body_bytes = await request.body()
        form_data = urllib.parse.parse_qs(body_bytes.decode("utf-8", errors="replace"))

        q = form_data.get("q", [""])[0].strip()
        cat = form_data.get("category", ["all"])[0].lower().strip()
        if cat not in ("all", "web", "news", "images", "videos", "library", "social", "smallweb", "community"):
            cat = "all"

        try:
            p = max(1, int(form_data.get("p", ["1"])[0]))
        except ValueError:
            p = 1

        theme = form_data.get("theme", [None])[0]
        lang = form_data.get("lang", [None])[0]
        time_filter = form_data.get("time_filter", [None])[0]
        sort = form_data.get("sort", [None])[0]
        region = form_data.get("region", [settings.DEFAULT_REGION])[0]
        safe_search = form_data.get("safe_search", ["off"])[0]
        academic = form_data.get("academic", ["false"])[0].lower() in ("true", "1")
        social = form_data.get("social", ["false"])[0].lower() in ("true", "1")
        synthesis = form_data.get("synthesis", ["false"])[0].lower() in ("true", "1")
        goggle = form_data.get("goggle", [None])[0]
        custom_goggle = form_data.get("custom_goggle", [None])[0]
        anti_slop = form_data.get("anti_slop", ["true"])[0].lower() in ("true", "1")
        clustering = form_data.get("clustering", ["true"])[0].lower() in ("true", "1")
        literal = form_data.get("literal", ["false"])[0].lower() in ("true", "1")

        return await search(
            request,
            q=q,
            category=cat,
            p=p,
            format=format,
            accept=accept,
            time_filter=time_filter,
            sort=sort,
            region=region,
            safe_search=safe_search,
            academic=academic,
            social=social,
            synthesis=synthesis,
            goggle=goggle,
            custom_goggle=custom_goggle,
            anti_slop=anti_slop,
            clustering=clustering,
            literal=literal,
            theme=theme,
            lang=lang,
        )

    @app.get("/api/v1/search", response_model=SearchResponseModel)
    async def api_search(
        q: str = Query(..., min_length=1, max_length=256),
        category: str = Query(default="all"),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=10, ge=1, le=50),
    ):
        """Dedicated JSON search API endpoint."""
        cat = category.lower().strip()
        if cat not in ("all", "web", "news", "images", "videos", "library"):
            cat = "all"
        results = app_retriever.search(q.strip(), page=page, page_size=page_size, category=cat)
        return results

    @app.get("/api/v1/stats", response_model=StatsResponseModel)
    async def api_stats():
        """Retrieve operational index metrics."""
        return app_storage.get_stats()

    @app.get("/api/v1/bangs")
    async def api_bangs():
        """List active bang operators."""
        return {
            prefix: {"template": tpl, "service": srv}
            for prefix, (tpl, srv) in BANG_SHORTCUTS.items()
        }

    @app.get("/health")
    async def health_check():
        """Top-level health check endpoint for reverse proxies and monitors."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    @app.get("/api/v1/health")
    async def api_health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    @app.post("/api/v1/takedown")
    async def api_takedown(payload: TakedownRequest):
        """Process an ethical domain or URL takedown / index purge."""
        if not payload.domain and not payload.url:
            raise HTTPException(status_code=400, detail="Must provide either 'domain' or 'url' to purge.")

        purged_count = 0
        if payload.url:
            purged_count += app_storage.purge_url(payload.url)
        elif payload.domain:
            purged_count += app_storage.purge_domain(payload.domain)

        return {
            "status": "success",
            "purged_records": purged_count,
            "target": payload.url or payload.domain,
        }

    return app


app = create_app()
