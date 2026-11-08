# Senda — Privacy Policy and Architecture

SPDX-License-Identifier: GPL-3.0-or-later

## 1. Privacy by Design

Privacy is not a marketing promise; in Senda, it is an immutable architectural constraint.

### 1.1 What We Do NOT Collect
- **No Search Query Logging:** Queries entered into Senda are processed in volatile memory to retrieve results and are never written to disk, databases, or log files.
- **No IP Address Recording:** Server connection logs strip or discard client IP addresses.
- **No Behavioral Profiling:** Senda does not build user profiles, track repeat visitors, or correlate searches over time.
- **No Search History:** No search history is stored on the server.
- **No Cookies:** Senda does not set tracking, session, or advertising cookies.
- **No Third-Party Analytics:** Senda contains zero Google Analytics, zero trackers, zero beacons, zero external telemetry.
- **No External CDNs:** All stylesheets, fonts, and assets are hosted locally on the server. No connections to external CDNs occur when rendering Senda.
- **No Referrer Leakage:** Senda transmits `Referrer-Policy: no-referrer`. Destination websites you click on cannot see the search terms you entered or that you came from Senda.
- **No Click Tracking:** Links to external sites navigate directly to the target URL (`rel="noopener noreferrer"`) without routing through tracking redirectors.

### 1.2 Local Preferences
User interface preferences (such as light/dark theme and language selection) are stored exclusively on your local device in browser `localStorage`. They are never transmitted to or stored by Senda servers.

### 1.3 Auditability
The entirety of Senda's source code is public and licensed under GNU GPL-3.0-or-later. Anyone can inspect, build, run, and audit the application independently to verify these commitments.
