# Administration & Maintenance Manual — Senda Search Engine

**License:** GNU GPL-3.0-or-later  
**Scope:** Operational maintenance, database backups, index purging, and takedown procedures.

---

## 1. Directory Structure

```text
/home/user/senda-search/
├── data/
│   ├── senda.db          # Master SQLite database & FTS5 virtual table
│   ├── senda.db-wal      # Write-Ahead Log
│   └── senda.db-shm      # Shared-memory index lock
├── docs/                 # Documentation & Architecture
├── src/senda/            # Core Python package
└── tests/                # Automated pytest suite
```

---

## 2. Database Maintenance & Backups

Senda operates with SQLite in Write-Ahead Log (`WAL`) mode for high concurrency.

### Safe Online Backup
Never copy `senda.db` directly while the server or crawler is running without using SQLite's online backup API or the `.backup` CLI command:

```bash
# Perform an atomic, consistent online backup
sqlite3 data/senda.db ".backup 'data/senda-backup-$(date +%Y%m%d%H%M%S).db'"
```

### Checkpoint and Optimize WAL
To flush transactions from the WAL file back into the primary database:
```bash
sqlite3 data/senda.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

### Full-Text Index Optimization
Periodically, after indexing thousands of documents, optimize the FTS5 B-tree segments to reduce file size and improve query execution times:
```bash
sqlite3 data/senda.db "INSERT INTO documents_fts(documents_fts) VALUES('optimize');"
```

---

## 3. Takedown & GDPR Compliance (Purging Records)

Respecting content owners' rights and privacy requests is a core ethical commitment of Senda. When a website owner requests removal, or if prohibited content is discovered, administrators have two immediate purge tools:

### 3.1. Purging an Entire Domain
Removes all indexed pages belonging to a domain from both the relational table and the full-text search index:
```bash
senda purge-domain example.com
```

Via the REST API:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/takedown \
     -H "Content-Type: application/json" \
     -d '{"domain": "example.com", "reason": "Site owner exclusion request"}'
```

### 3.2. Purging a Specific URL
Removes an exact document URL from the index:
```bash
senda purge-url https://example.com/confidential-document.html
```

Via the REST API:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/takedown \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/confidential-document.html", "reason": "Takedown request"}'
```

---

## 4. Crawling Operations & Rate Limiting

### Transparent Identification
Senda declares its identity and contact information in all outgoing requests via the configured User-Agent header:
```text
User-Agent: SendaBot/0.1 (+https://ideh.top/senda-search; bot@ideh.top)
```

To modify contact information or crawler bounds, override configuration settings via environment variables:
```bash
export SENDA_USER_AGENT="SendaBot/0.1 (+https://my-domain.org; admin@my-domain.org)"
export SENDA_DEFAULT_CRAWL_DELAY_SECONDS=3.0
export SENDA_MAX_DOCUMENT_SIZE_BYTES=3145728 # 3 MiB
```

### Controlled Discovery
When initiating a crawl, always restrict the depth and document count:
```bash
senda crawl https://target-domain.org --max-pages 50 --max-depth 2
```

---

## 5. Security & Privacy Audit Checklist

Before placing Senda in a production environment:
1. Verify that `SERVER_HOST` is bound to `127.0.0.1` unless a hardened reverse proxy (e.g. Nginx, Caddy) handles TLS termination.
2. Confirm reverse proxy forwards `X-Forwarded-For` without logging client queries or IPs in access logs.
3. Validate that `data/` directory permissions are restricted to the service user (`chmod 700 data/`).
4. Execute `pytest -v` after any configuration or environment update to ensure anti-SSRF protections remain uncompromised.
