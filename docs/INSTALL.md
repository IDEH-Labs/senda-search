# Installation & Operations Manual — Senda Search Engine

**Platform:** Gentoo Linux x86_64 / POSIX-compliant Linux  
**Runtime:** Python >= 3.12 (Tested on Python 3.14)  
**License:** GNU GPL-3.0-or-later  

---

## 1. System Requirements

### Hardware Requirements
- **CPU:** 1 core x86_64 (2+ cores recommended for concurrent crawling).
- **RAM:** Minimum 512 MiB (1 GiB+ recommended for large FTS indices).
- **Storage:** NVMe or SSD recommended for SQLite WAL read/write throughput.

### Software Prerequisites (Gentoo Linux)
Ensure Python and SQLite with FTS5 support are installed. On Gentoo:
```bash
# Verify SQLite has FTS5 enabled (standard in dev-db/sqlite)
emerge --ask dev-db/sqlite dev-lang/python:3.14
```

---

## 2. Installation via Python Virtual Environment

Clone the repository and prepare the isolated virtual environment:

```bash
# Clone the repository
git clone https://github.com/ideh-labs/senda-search.git
cd senda-search

# Create isolated Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install package in editable mode
pip install --upgrade pip
pip install -e ".[dev]"
```

Verify that the CLI command is correctly installed:
```bash
senda --help
```

---

## 3. Running Automated Tests

Run the full test suite with test coverage reporting:
```bash
pytest -v --cov=senda
```
All 53 test assertions must pass with zero errors.

---

## 4. Initial Crawling & Index Population

To seed your local search engine with free software resources:
```bash
# Crawl the Free Software Foundation site (max 10 pages, depth 1)
senda crawl https://fsf.org --max-pages 10 --max-depth 1

# Crawl the GNU Project site
senda crawl https://www.gnu.org --max-pages 10 --max-depth 1

# Check current index metrics
senda stats
```

---

## 5. Running the Web Search Interface & API

Start the web server locally:
```bash
senda serve --host 127.0.0.1 --port 8000
```
Open your browser to `http://127.0.0.1:8000`.

---

## 6. Gentoo Linux Service Deployment

### 6.1. OpenRC Service (Default Gentoo Init)
Create the configuration file `/etc/conf.d/senda`:
```sh
# /etc/conf.d/senda
SENDA_USER="senda"
SENDA_GROUP="senda"
SENDA_DIR="/var/lib/senda"
SENDA_HOST="127.0.0.1"
SENDA_PORT="8000"
```

Create the OpenRC init script `/etc/init.d/senda`:
```sh
#!/sbin/openrc-run
# Senda Search Engine OpenRC init script

name="senda"
description="Senda Sovereign Search Engine"

command="/var/lib/senda/.venv/bin/senda"
command_args="serve --host ${SENDA_HOST} --port ${SENDA_PORT}"
command_user="${SENDA_USER}:${SENDA_GROUP}"
command_background="yes"
pidfile="/run/senda.pid"
directory="${SENDA_DIR}"

depend() {
    need net
    after firewall
}
```

Make it executable and enable the service:
```bash
chmod +x /etc/init.d/senda
rc-update add senda default
rc-service senda start
```

### 6.2. systemd Unit (Alternative)
For systemd-based Gentoo profiles:
```ini
# /etc/systemd/system/senda.service
[Unit]
Description=Senda Sovereign Search Engine
After=network.target

[Service]
Type=simple
User=senda
Group=senda
WorkingDirectory=/var/lib/senda
ExecStart=/var/lib/senda/.venv/bin/senda serve --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5s

# Hardening
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/senda/data
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable --now senda
```
