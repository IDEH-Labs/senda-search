# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

# Reproducible, minimal, non-root container for Senda Search
FROM python:3.12-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SENDA_DATA_DIR=/var/lib/senda \
    SENDA_SERVER_HOST=0.0.0.0 \
    SENDA_SERVER_PORT=8000

# Install build dependencies, sqlite3, and clean up apt cache in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libsqlite3-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Create unprivileged system user and group
RUN groupadd -r -g 10001 senda && \
    useradd -r -u 10001 -g senda -d /var/lib/senda -s /sbin/nologin senda && \
    mkdir -p /var/lib/senda /app && \
    chown -R senda:senda /var/lib/senda /app

WORKDIR /app

# Copy packaging specifications first for optimal layer caching
COPY --chown=senda:senda pyproject.toml /app/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e "."

# Copy application source code and configuration
COPY --chown=senda:senda src/ /app/src/
COPY --chown=senda:senda PRIVACY.md SECURITY.md /app/

# Re-install package in editable mode to register entrypoints
RUN pip install --no-cache-dir -e "."

# Switch to unprivileged user
USER senda

# Expose sovereign search port
EXPOSE 8000

# Health check against local API
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/ || exit 1

# Launch application
CMD ["senda", "serve", "--host", "0.0.0.0", "--port", "8000"]
