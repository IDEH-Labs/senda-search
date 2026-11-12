# Senda — Security Policy and Threat Model

SPDX-License-Identifier: GPL-3.0-or-later

## 1. Security Architecture & Threat Model

Senda operates as both a web client (crawler/indexer) and a web server (search API/UI). Security is enforced by default at the transport, parsing, and query layers.

### 1.1 Crawler Defense Mechanisms

1. **Server-Side Request Forgery (SSRF) Prevention:**
   - Pre-flight DNS resolution before any socket connection.
   - Strict socket-level validation rejecting:
     - IPv4 Loopback (`127.0.0.0/8`)
     - IPv6 Loopback (`::1`)
     - Private Networks RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
     - IPv6 Unique Local (`fc00::/7`)
     - Link-Local IPv4/IPv6 (`169.254.0.0/16`, `fe80::/10`)
     - Carrier-Grade NAT (`100.64.0.0/10`)
     - Multicast (`224.0.0.0/4`, `ff00::/8`)
     - Broadcast and Reserved IP space
   - Direct connection to the resolved, verified IP address with explicit TLS Server Name Indication (SNI) and HTTP `Host` headers to prevent DNS Rebinding (`PinningNetworkBackend`).
   - **Tor Special-Use Domain (`.onion`) Hardening:** Tor `.onion` destinations are strictly prohibited from direct resolution and direct TCP connections. They are blocked unconditionally unless an authorized SOCKS5/SOCKS5h proxy is configured. Direct DNS lookup is bypassed entirely for `.onion` to eliminate local DNS leakage, and destination addresses are never substituted with loopback IPs.
   - **Proxy DNS Residual Risk:** When crawling through a proxy for non-`.onion` destinations, pre-flight DNS validation is retained (Decision D1), with the known residual risk of local DNS resolver exposure and potential TOCTOU between local pre-flight checks and proxy-side resolution.

2. **Denial of Service (DoS) & Bomb Protection:**
   - Hard upper limit on payload size: maximum **2 MiB** per document.
   - Streaming response consumption with immediate connection abort when the byte limit is exceeded.
   - Fixed request timeout: **10 seconds** per request.
   - Maximum redirect chain depth: **5 redirects**, with re-validation of each target IP.

3. **Spider Trap Mitigation:**
   - URL length hard limit: **512 characters**.
   - Path segment depth limit: maximum **5 segments**.
   - Query string parameter normalization and tracking-parameter stripping.
   - Canonical URL deduplication via cryptographic SHA-256 hash sets.

4. **Politeness & RFC 9309 Compliance:**
   - Full parser for `robots.txt` honoring `User-agent`, `Disallow`, and `Crawl-delay`.
   - Domain-level rate limiter: minimum 2.0-second delay between requests to the same host by default.
   - Concurrency cap: maximum 1 concurrent connection per host.
   - Transparent, auditable `User-Agent` header including contact and project information.

### 1.2 Search & Interface Defense Mechanisms

1. **SQL Injection Defense:**
   - 100% parameterized SQLite queries. No dynamic string concatenation for FTS5 queries or schema modifications.
   - Strict sanitization and quoting of search terms for the FTS5 query parser.

2. **Cross-Site Scripting (XSS) Prevention & Content Security Policy (CSP):**
   - HTML entity escaping for all search results, snippets, and user-supplied parameters.
   - Strict Content Security Policy (`CSP`) featuring:
     - Dynamic per-request cryptographic nonces (`script-src 'self' 'nonce-{csp_nonce}'`) for authorized inline scripts, eliminating `'unsafe-inline'` script execution.
     - Inline event handlers (e.g., `onclick`) completely eliminated from templates.
     - Strict media boundary: `img-src 'self' data;` preventing IP leakage to third-party CDNs and trackers.
     - Anti-injection directives: `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, and `frame-ancestors 'none'`.
     - `style-src 'self' 'unsafe-inline'` is retained exclusively for dynamic theme tokens and CSS variables.
   - `X-Content-Type-Options: nosniff`.
   - `X-Frame-Options: DENY`.

3. **Referrer & Privacy Leakage Mitigation:**
   - `Referrer-Policy: no-referrer` on all responses and outgoing result links.
   - Direct outgoing links with `rel="noopener noreferrer"`. No click-tracking redirects.
   - Functional cookies (`senda_theme`, `senda_lang`) carry `SameSite=Lax`, `Path=/`, `Max-Age=31536000`, and automatic `Secure` enforcement over HTTPS. Zero tracking cookies, zero session identifiers.

## 2. Reporting a Security Vulnerability

If you discover a security issue or vulnerability in Senda, please report it responsibly:
- Email: **contact@ideh.top**
- PGP Key: Available at <https://ideh.top>

Please do not open public issues for zero-day security vulnerabilities before coordinated disclosure. We commit to acknowledging reports within 48 hours and publishing fixes transparently.
