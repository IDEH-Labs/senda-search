# Changelog

All notable changes to the Senda Search Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-alpha] - 2026-11-08

### Added
- **Core Architecture:** Initial release of the independent, sovereign Senda Search Engine under GNU GPL-3.0-or-later.
- **Network Guard & Socket IP Pinning:** Anti-SSRF and DNS rebinding defense mechanism with `PinningNetworkBackend` and `AntiSSRFTransport` locking outbound TCP sockets exclusively to validated public IPs, closing TOCTOU DNS rebinding attack vectors.
- **RFC 9309 Robots Parser & SQLite Cache:** Strict compliance with Robots Exclusion Standard with persistent SQLite policy caching (24h TTL) to avoid redundant requests to webmasters.
- **URL Frontier & Politeness Queue with DB Persistence:** Domain-isolated queues with configurable delay timers, canonical normalization, tracking parameter stripping, spider trap defense, and SQLite persistence for crash resilience across restarts.
- **Hardened Fetcher:** Streaming HTTP client with MIME-type filtering (`text/html`, `application/xhtml+xml`, `text/plain`), 2 MiB payload limit, and SSRF re-validation on every redirect hop.
- **Document Extractor:** BeautifulSoup-powered extraction of title, meta description, language, headings, and clean body text, with SHA-256 content deduplication hashing.
- **SQLite FTS5 Storage Engine:** Transactional SQLite backend with WAL mode, FTS5 virtual table with `unicode61` tokenizer, automatic synchronization triggers, and takedown purge functions (`purge_url`, `purge_domain`).
- **Retrieval & BM25 Ranking:** Sanitized query parser supporting quoted exact phrases, search operators (`site:<domain>`, `lang:<lang>`, `-negation`), and multi-field weighting ($Title \times 10 > Headings \times 5 > Description \times 3 > Body \times 1$) with contextual snippet highlighting.
- **Anti-SEO Text Density Metric:** Marginalia-inspired prose density heuristic (`text_density = text_len / max(raw_html_len, 1)`) integrated directly into BM25 scoring (`bm25 * (1.0 + text_density)`), ranking rich, informative, handcrafted content higher while demoting bloated ad/SEO marketing pages.
- **Pure-Python Morphological Stemmer:** Dependency-free stemmer for Spanish and English inflectional suffixes enabling accurate root matching without heavy external NLP libraries.
- **Concurrent Multi-Domain Crawler:** Asynchronous worker pool (`CrawlerRunner.crawl_seeds`) with active domain locking and RFC 9309 politeness enforcement, enabling high throughput across diverse hosts with zero per-domain contention.
- **POST Search Query Privacy:** Privacy-preserving `POST /search` endpoint keeping search queries out of the browser URL bar, local navigation history, and intermediary HTTP proxy logs.
- **Sovereign Search Verticals:** Four ethical search categories directly accessible via UI tabs and API (`category=all|web|news|images|library`):
  - 🌐 **Web:** Decentralized, independent web indexed with anti-SEO text density.
  - 📰 **Noticias:** Chronological news and tech policy feeds with extracted publication timestamps.
  - 🖼️ **Imágenes:** Free Culture media index (Wikimedia Commons, Creative Commons, CC0) featuring direct privacy-preserving thumbnails (`referrerpolicy="no-referrer"`) and license attribution badges.
  - 📚 **Biblioteca:** Free knowledge and encyclopedia index covering Wikipedia, Project Gutenberg, GNU Manuals, and Internet Archive.
- **Dedicated Image FTS5 Index:** SQLite `images` and `images_fts` tables with automatic synchronization triggers and BM25 relevance ranking over image metadata and alt text.
- **REST API:** FastAPI application providing `/api/v1/search`, `/api/v1/stats`, `/api/v1/health`, `/api/v1/takedown`, and OpenSearch 1.1 discovery at `/opensearch.xml`.
- **Sovereign Web UI:** Semantic, accessible HTML5 templates functional 100% without JavaScript, featuring automatic dark mode, OpenSearch auto-discovery link, category tabs, and zero external asset calls.
- **Client-Side i18n:** Multi-language support across 8 global languages (English, Spanish, French, German, Portuguese, Italian, Japanese, Chinese) with privacy-preserving local storage.
- **Administrative CLI:** Command-line suite (`senda crawl`, `senda search --category`, `senda stats`, `senda purge-domain`, `senda purge-url`, `senda serve`).
- **Test Suite:** 65 unit and integration tests with 88% codebase coverage.
- **Documentation:** Architecture guide, installation manual for Gentoo Linux / POSIX, administration manual, security threat model, privacy policy, and software bill of materials (SBOM).
