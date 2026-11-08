# Changelog

All notable changes to the Senda Search Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-alpha] - 2026-11-08

### Added
- **Core Architecture:** Initial release of the independent, sovereign Senda Search Engine under GNU GPL-3.0-or-later.
- **Network Guard:** Anti-SSRF and DNS rebinding defense mechanism preventing requests to loopback, RFC 1918 private subnets, link-local metadata endpoints (`169.254.169.254`), and CGNAT ranges.
- **RFC 9309 Robots Parser:** Strict compliance with Robots Exclusion Standard including path length matching, wildcard `*`, end-anchor `$`, crawl delay extraction, and policy caching.
- **URL Frontier & Politeness Queue:** Domain-isolated queues with configurable delay timers, canonical normalization, tracking parameter stripping, and spider trap defense (loop and depth gating).
- **Hardened Fetcher:** Streaming HTTP client with MIME-type filtering (`text/html`, `application/xhtml+xml`, `text/plain`), 2 MiB payload limit, and SSRF re-validation on every redirect hop.
- **Document Extractor:** BeautifulSoup-powered extraction of title, meta description, language, headings, and clean body text, with SHA-256 content deduplication hashing.
- **SQLite FTS5 Storage Engine:** Transactional SQLite backend with WAL mode, FTS5 virtual table with `unicode61` tokenizer, automatic synchronization triggers, and takedown purge functions (`purge_url`, `purge_domain`).
- **Retrieval & BM25 Ranking:** Sanitized query parser supporting quoted exact phrases and multi-field weighting ($Title \times 10 > Headings \times 5 > Description \times 3 > Body \times 1$) with contextual snippet highlighting.
- **REST API:** FastAPI application providing `/api/v1/search`, `/api/v1/stats`, `/api/v1/health`, and `/api/v1/takedown`.
- **Sovereign Web UI:** Semantic, accessible HTML5 templates functional 100% without JavaScript, featuring automatic dark mode and zero external asset calls.
- **Client-Side i18n:** Multi-language support (English canonical, Spanish, French, German) with privacy-preserving local storage.
- **Administrative CLI:** Command-line suite (`senda crawl`, `senda search`, `senda stats`, `senda purge-domain`, `senda purge-url`, `senda serve`).
- **Test Suite:** 53 unit and integration tests with 90% codebase coverage.
- **Documentation:** Architecture guide, installation manual for Gentoo Linux / POSIX, administration manual, security threat model, privacy policy, and software bill of materials (SBOM).
