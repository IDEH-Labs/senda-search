# Senda — The Independent, Ethical Web Search Engine

[![License: GPL v3+](https://img.shields.io/badge/License-GPL%20v3%2B-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Privacy: Zero Tracking](https://img.shields.io/badge/Privacy-Zero%20Tracking-brightgreen.svg)](PRIVACY.md)

> **Senda** is an independent, auditable, and sovereign web search engine developed by **IDEH Labs**. Built from scratch to protect the rights of users and third parties alike, Senda delivers neutral, transparent search results without behavioral profiling, ad tracking, or query retention.

---

## Key Principles & Features

- **Zero Tracking by Design:** No user profiling, no query history stored on disk, no IP address logging, and zero advertising trackers or cookies.
- **Independent Index:** Powered by an embedded SQLite FTS5 full-text search engine with BM25 lexical ranking and configurable semantic field weighting.
- **Strict Network & SSRF Protections:** Built-in network guard that pre-resolves DNS and strictly rejects private RFC 1918, loopback, link-local, and multicast IP addresses, mitigating DNS rebinding and internal network probing.
- **RFC 9309 Politeness:** Strictly respects `robots.txt`, enforces domain-level rate limiting (`crawl-delay`), and caps per-host concurrency.
- **Third-Party Rights & Takedown:** Indexes structured metadata (titles, canonical links, bounded text excerpts) rather than full-page piracy mirrors. Provides administrative commands (`purge-domain`, `purge-url`) for immediate domain removal.
- **Multilingual (i18n):** Native interface support with English as primary default, plus Spanish and additional languages.
- **Lightweight & Fully Accessible:** 100% functional without JavaScript. WCAG AAA color contrast, native light/dark themes.

---

## Architecture Overview

```
src/senda/
├── crawler/      # Polite async fetcher, RFC 9309 robots parser, Anti-SSRF network guard
├── frontier/     # Canonical URL normalization, priority queue, spider trap defense
├── extractor/    # Safe DOM parser, metadata extraction, text sanitization
├── indexer/      # SQLite FTS5 engine, document storage, content deduplication
├── ranking/      # BM25 lexical ranking, structural field weighting, snippet generator
├── api/          # FastAPI REST endpoints (/search, /health, /stats) & security headers
├── ui/           # Semantic HTML5/CSS interface with local i18n switcher
└── cli/          # Administrative CLI tools (crawl, search, purge-domain, stats)
```

---

## Installation & Setup (Gentoo Linux / POSIX)

```bash
# Clone the repository
git clone https://github.com/IDEH-Labs/senda-search.git
cd senda-search

# Create and activate a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Run test suite
pytest
```

---

## License

This project is licensed under the **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`). See the [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) files for complete terms and copyright notices.

An **[IDEH Labs](https://ideh.top)** project · [Codeberg](https://codeberg.org/IDEH-Labs)
