# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Central configuration for the Senda Search Engine."""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SendaSettings(BaseSettings):
    """Immutable application settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_prefix="SENDA_",
        extra="ignore"
    )

    # Project metadata
    APP_NAME: str = "Senda"
    APP_VERSION: str = "0.1.0"
    APP_URL: str = "https://ideh.top"
    CONTACT_EMAIL: str = "contact@ideh.top"
    ONION_HOST: Optional[str] = Field(
        default=None,
        description="Public Tor v3 .onion hostname for Onion-Location header advertisement."
    )

    # User-Agent strictly declaring identity and contact per RFC 9309 guidelines
    USER_AGENT: str = Field(
        default="SendaBot/0.1 (+https://ideh.top/senda-search; bot@ideh.top)",
        description="Transparent crawler identification header."
    )

    # Storage paths
    DATA_DIR: Path = Path("data")
    DATABASE_NAME: str = "senda.db"

    @property
    def DATABASE_PATH(self) -> Path:
        return self.DATA_DIR / self.DATABASE_NAME

    # Crawler security bounds
    MAX_DOCUMENT_SIZE_BYTES: int = Field(
        default=2 * 1024 * 1024,  # 2 MiB hard limit
        description="Maximum downloaded document size to prevent decompression and DoS bombs."
    )
    REQUEST_TIMEOUT_SECONDS: float = Field(
        default=10.0,
        description="Per-request socket timeout in seconds."
    )
    MAX_REDIRECTS: int = Field(
        default=5,
        description="Maximum redirect depth."
    )

    # Politeness constraints
    DEFAULT_CRAWL_DELAY_SECONDS: float = Field(
        default=2.0,
        description="Minimum politeness interval between requests to the same host."
    )
    MAX_CONCURRENT_HOST_REQUESTS: int = Field(
        default=1,
        description="Strict concurrency limit per domain."
    )

    # Frontier constraints (Spider trap defense)
    MAX_URL_LENGTH: int = Field(
        default=512,
        description="Maximum accepted URL character length."
    )
    MAX_PATH_DEPTH: int = Field(
        default=5,
        description="Maximum directory path depth in URLs."
    )

    # Provider settings
    SEARXNG_URL: str = ""
    BRAVE_API_KEY: str = ""
    MOJEEK_API_KEY: str = ""
    OPENALEX_API_KEY: str = ""
    OPENALEX_ENABLED: bool = True
    OPENALEX_RATE_LIMIT_PER_MINUTE: int = 30
    OPENALEX_CACHE_TTL_SECONDS: int = 3600

    # Open social protocols (strictly isolated to 'social' vertical or explicit opt-in)
    FEDIVERSE_ENABLED: bool = True
    FEDIVERSE_INSTANCE: str = "mastodon.social"
    BLUESKY_ENABLED: bool = True
    BLUESKY_ENDPOINT: str = "https://api.bsky.app"

    # Grounded Extractive Synthesis (Strictly disabled by default; deterministic citations, zero generative hallucination)
    ENABLE_EXTRACTIVE_SYNTHESIS: bool = False
    ENABLE_AI_SYNTHESIS: bool = False  # Legacy backward-compatible alias

    # Regional & Language Defaults (Global por defecto; cero geolocalización invasiva)
    DEFAULT_REGION: str = "all"
    DEFAULT_LANGUAGE: str = "es"

    # Tor Onion Service & Anonymous Crawling
    ONION_HOST: str = Field(
        default="",
        description="Optional Tor .onion hostname (e.g., 'senda...onion') to emit RFC Onion-Location headers."
    )
    CRAWLER_PROXY: str = Field(
        default="",
        description="Optional SOCKS5 or HTTP proxy URL (e.g., 'socks5://127.0.0.1:9050') for Tor crawling."
    )
    CRAWL_DAEMON_INTERVAL_MINUTES: int = Field(
        default=30,
        description="Default interval in minutes between background crawl daemon passes."
    )
    CRAWL_DAEMON_MAX_PAGES: int = Field(
        default=50,
        description="Default maximum documents to index per background crawl cycle."
    )

    # Web service
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    FORWARDED_ALLOW_IPS: str = Field(
        default="127.0.0.1,::1",
        description="Comma-separated list of IP addresses trusted to provide X-Forwarded-* proxy headers."
    )



settings = SendaSettings()
