# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""FastAPI Web Application and Sovereign REST API for Senda Search Engine."""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, Query, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from senda.config import settings
from senda.indexer.storage import StorageEngine
from senda.ranking.retriever import SearchRetriever, SearchResultSet


# Pydantic schemas for API documentation and validation
class SearchItemModel(BaseModel):
    url: str
    domain: str
    title: str
    snippet: str
    relevance_score: float


class SearchResponseModel(BaseModel):
    query: str
    total_matches: int
    page: int
    page_size: int
    total_pages: int
    duration_ms: float
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

    # Initialize storage and retrieval services
    app_storage = storage or StorageEngine()
    app_retriever = SearchRetriever(app_storage)

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
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        return response

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Render sovereign search homepage."""
        return templates.TemplateResponse(request=request, name="index.html", context={})

    @app.get("/about", response_class=HTMLResponse)
    async def about(request: Request):
        """Render about and ethics page."""
        return templates.TemplateResponse(request=request, name="about.html", context={})

    @app.get("/privacy", response_class=HTMLResponse)
    async def privacy(request: Request):
        """Render verifiable privacy policy."""
        return templates.TemplateResponse(request=request, name="privacy.html", context={})

    @app.get("/search")
    async def search(
        request: Request,
        q: str = Query(default="", max_length=256),
        p: int = Query(default=1, ge=1),
        format: Optional[str] = Query(default=None),
        accept: Optional[str] = Header(default=None),
    ):
        """Search endpoint supporting both HTML rendering and JSON content negotiation."""
        clean_q = q.strip()
        results = app_retriever.search(clean_q, page=p, page_size=10)

        # Content negotiation
        if format == "json" or (accept and "application/json" in accept and not ("text/html" in accept)):
            return results

        return templates.TemplateResponse(
            request=request,
            name="results.html",
            context={
                "query": clean_q,
                "results": results,
            }
        )

    @app.get("/api/v1/search", response_model=SearchResponseModel)
    async def api_search(
        q: str = Query(..., min_length=1, max_length=256),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=10, ge=1, le=50),
    ):
        """Dedicated JSON search API endpoint."""
        results = app_retriever.search(q.strip(), page=page, page_size=page_size)
        return results

    @app.get("/api/v1/stats", response_model=StatsResponseModel)
    async def api_stats():
        """Retrieve operational index metrics."""
        return app_storage.get_stats()

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
