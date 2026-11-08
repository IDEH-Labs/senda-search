# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Central configuration for the Senda Search Engine."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SendaSettings(BaseSettings):
    """Immutable application settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_prefix="SENDA_",
        env_file=".env",
        extra="ignore"
    )

    # Project metadata
    APP_NAME: str = "Senda"
    APP_VERSION: str = "0.1.0"
    APP_URL: str = "https://ideh.top"
    CONTACT_EMAIL: str = "contact@ideh.top"

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

    # Web service
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000


settings = SendaSettings()
