# Senda — Production Deployment Guide

SPDX-License-Identifier: GPL-3.0-or-later
SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

This guide outlines the end-to-end procedure for deploying the **Senda Sovereign Search Engine** on a production Linux server (Gentoo Linux x86_64 or Debian/Ubuntu LTS) under the domain `senda.ideh.top`.

---

## 1. System Requirements

- **Operating System:** Gentoo Linux x86_64 (recommended), Debian 12+, or Ubuntu 24.04 LTS.
- **Hardware Minimums:**
  - 2 vCPU cores.
  - 4 GiB RAM.
  - 50 GiB NVMe / SSD disk storage.
  - Public static IPv4 / IPv6 address.
- **Network Ports:** Port `80` (HTTP ACME) and `443` (HTTPS TLS).

---

## 2. Automated Turnkey Installation

Clone the repository and run the automated installer:

```bash
git clone https://codeberg.org/IDEH-Labs/senda-search.git /opt/senda/repo
cd /opt/senda/repo
sudo ./deploy/setup-production.sh
```

The installer performs the following automatically:
1. Creates dedicated system user and group `senda:senda`.
2. Initializes `/var/lib/senda` with secure permissions (`750`).
3. Installs the ethical seed catalog into `/etc/senda/ethical_seeds.txt`.
4. Provisions Python virtual environment at `/opt/senda/venv` and installs Senda.
5. Installs and enables init units (`OpenRC` on Gentoo or `systemd` on Debian).
6. Configures periodic crawler timer and SQLite WAL optimization cron jobs.

---

## 3. Reverse Proxy & TLS Configuration

### 3.1 Obtaining TLS Certificate via Let's Encrypt

```bash
sudo certbot certonly --standalone -d senda.ideh.top
```

### 3.2 Option A: Nginx (Recommended)

1. Copy the pre-hardened sovereign Nginx configuration:
   ```bash
   sudo cp deploy/nginx/senda.conf /etc/nginx/sites-available/senda.conf
   sudo ln -sf /etc/nginx/sites-available/senda.conf /etc/nginx/sites-enabled/
   ```
2. Verify configuration and reload:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx   # On systemd
   # OR
   sudo rc-service nginx reload  # On Gentoo OpenRC
   ```

### 3.3 Option B: Caddy (Automatic HTTPS)

If using Caddy:
```bash
sudo cp deploy/caddy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

---

## 4. Starting the Service

### On Gentoo Linux (OpenRC):
```bash
sudo rc-service senda start
sudo rc-update add senda default
```

### On Debian/Ubuntu (systemd):
```bash
sudo systemctl start senda.service
sudo systemctl start senda-crawler.timer
```

Verify service status:
```bash
curl -I https://senda.ideh.top/api/v1/health
```
Expected output:
```http
HTTP/2 200 
referrer-policy: no-referrer
x-content-type-options: nosniff
x-frame-options: DENY
content-type: application/json
```

---

## 5. Initial Crawl Execution

To populate your sovereign database immediately with the curated seeds:

```bash
sudo -u senda /opt/senda/venv/bin/senda crawl \
    --seeds-file /etc/senda/ethical_seeds.txt \
    --max-pages 2000 \
    --max-depth 2
```

Inspect index statistics:
```bash
sudo -u senda /opt/senda/venv/bin/senda stats
```

---

## 6. Senda Browser Android Integration

Once `https://senda.ideh.top` is live:
1. Open **Senda Browser Android** (built with GeckoView).
2. Navigate to `https://senda.ideh.top`.
3. The browser will detect the OpenSearch tag `<link rel="search">` and prompt:
   *"Add Senda as your default search engine"*.
4. In `EngineSettings.kt`, set:
   ```kotlin
   const val DEFAULT_SEARCH_ENGINE = "https://senda.ideh.top/search?q=%s"
   ```
