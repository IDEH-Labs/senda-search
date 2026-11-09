# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""FastAPI Web Application and Sovereign REST API for Senda Search Engine."""

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
from senda.providers.base import SearchResultItem


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


class SearchResponseModel(BaseModel):
    query: str
    total_matches: int
    page: int
    page_size: int
    total_pages: int
    duration_ms: float
    category: str = "all"
    items: list[SearchItemModel]


class StatsResponseModel(BaseModel):
    total_documents: int
    total_domains: int
    database_size_bytes: int
    database_path: str


class TakedownRequest(BaseModel):
    domain: Optional[str] = Field(default=None, description="Domain to completely purge.")
    url: Optional[str] = Field(default=None, description="Specific URL to purge.")
    reason: Optional[str] = Field(default=None, description="Reason for removal.")


def create_app(storage: Optional[StorageEngine] = None) -> FastAPI:
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

    # Initialize storage, retrieval and multi-provider aggregator
    app_storage = storage or StorageEngine()
    app_retriever = SearchRetriever(app_storage)

    internal_prov = InternalStorageProvider(app_storage)
    searxng_prov = SearXNGProvider(settings.SEARXNG_URL)
    brave_prov = BraveSearchProvider(settings.BRAVE_API_KEY)
    mojeek_prov = MojeekProvider(settings.MOJEEK_API_KEY)

    app_aggregator = ProviderAggregator(
        internal_provider=internal_prov,
        searxng_provider=searxng_prov,
        brave_provider=brave_prov,
        mojeek_provider=mojeek_prov,
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

    def render_with_theme(name: str, request: Request, context: dict, query_theme: Optional[str] = None) -> Response:
        """Render template with theme and optionally set functional preference cookie."""
        current_theme = resolve_theme(request, query_theme)
        ctx = dict(context)
        ctx["theme"] = current_theme
        ctx["settings"] = settings
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
        return resp

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request, theme: Optional[str] = Query(default=None)):
        """Render search homepage."""
        return render_with_theme("index.html", request, {}, theme)

    @app.get("/about", response_class=HTMLResponse)
    async def about(request: Request, theme: Optional[str] = Query(default=None)):
        """Render about and ethics page."""
        return render_with_theme("about.html", request, {}, theme)

    @app.get("/how-it-works", response_class=HTMLResponse)
    async def how_it_works(request: Request, theme: Optional[str] = Query(default=None)):
        """Render plain language How It Works transparency page."""
        return render_with_theme("how_it_works.html", request, {}, theme)

    @app.get("/privacy", response_class=HTMLResponse)
    async def privacy(request: Request, theme: Optional[str] = Query(default=None)):
        """Render verifiable privacy policy."""
        return render_with_theme("privacy.html", request, {}, theme)

    @app.get("/javascript", response_class=HTMLResponse)
    async def javascript_licenses(request: Request, theme: Optional[str] = Query(default=None)):
        """GNU LibreJS Web Labels page declaring Free JavaScript licenses."""
        return render_with_theme("javascript.html", request, {}, theme)

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
        region: Optional[str] = Query(default=settings.DEFAULT_REGION),
        safe_search: str = Query(default="off"),
        no_ads: bool = Query(default=True),
        theme: Optional[str] = Query(default=None),
    ):
        """Search endpoint supporting HTML rendering and JSON content negotiation across verticals."""
        clean_q = q.strip()
        p_val = p if isinstance(p, int) else 1
        page_val = page if isinstance(page, int) else 1
        current_page = max(p_val, page_val)
        reg = region if isinstance(region, str) else settings.DEFAULT_REGION
        tf = time_filter if isinstance(time_filter, str) else None
        ss = safe_search if isinstance(safe_search, str) else "off"
        na = no_ads if isinstance(no_ads, bool) else True


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

        if cat not in ("all", "web", "news", "images", "videos", "library"):
            cat = "all"

        page_sz = 12 if cat == "images" else 10
        start_t = time.perf_counter()

        # Multi-provider aggregated search
        items_list = await app_aggregator.aggregate(
            query=clean_q,
            category=cat,
            page=current_page,
            page_size=page_sz,
            time_filter=tf,
            region=reg,
            safe_search=ss,
            no_ads=na,
        )


        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)

        # Fallback to local retriever counts for pagination estimation
        local_res = app_retriever.search(clean_q, page=current_page, page_size=page_sz, category=cat if cat != "all" else "all")
        total_matches = max(len(items_list), local_res.total_matches)
        total_pages = max(1, (total_matches + page_sz - 1) // page_sz) if total_matches > 0 else 1

        formatted_items = []
        for it in items_list:
            domain_name = urllib.parse.urlparse(it.url).netloc
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
                )
            )

        results_data = SearchResponseModel(
            query=clean_q,
            total_matches=total_matches,
            page=current_page,
            page_size=page_sz,
            total_pages=total_pages,
            duration_ms=duration_ms,
            category=cat,
            items=formatted_items,
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
                "safe_search": ss,
            },
            theme,
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
        if cat not in ("all", "web", "news", "images", "videos", "library"):
            cat = "all"

        try:
            p = max(1, int(form_data.get("p", ["1"])[0]))
        except ValueError:
            p = 1

        theme = form_data.get("theme", [None])[0]

        return await search(request, q=q, category=cat, p=p, format=format, accept=accept, theme=theme)

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
