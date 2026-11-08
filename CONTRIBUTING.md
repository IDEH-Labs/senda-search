# Contributing to Senda Search Engine

Thank you for your interest in contributing to **Senda**!

Senda is dedicated to defending computer user freedom, privacy by design, and technological sovereignty. We welcome contributions that preserve the integrity, ethics, and rigor of the project.

---

## 1. Ethical Commitments & Philosophy

All contributors agree to uphold the **Four Software Freedoms** defined by the Free Software Foundation:
- **Freedom 0:** The freedom to run the program as you wish, for any purpose.
- **Freedom 1:** The freedom to study how the program works, and change it so it does your computing as you wish.
- **Freedom 2:** The freedom to redistribute copies so you can help others.
- **Freedom 3:** The freedom to distribute copies of your modified versions to others.

### Zero-Compromise Directives
- **Zero Profiling / Telemetry:** We will never accept pull requests that introduce user tracking, analytics, tracking cookies, advertising identifiers, or telemetry.
- **Zero Anti-Bot Circumvention:** The crawler must never attempt to bypass CAPTCHAs, paywalls, access controls, or RFC 9309 `robots.txt` exclusions.
- **Auditable Security:** Any code modifying network routing or URL handling must undergo strict anti-SSRF verification.

---

## 2. Licensing & Intellectual Property

Senda is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.

- **SPDX Identifiers:** Every source code file (`.py`, `.html`, `.css`, `.js`, `.sh`) must include the standardized SPDX headers:
  ```python
  # SPDX-License-Identifier: GPL-3.0-or-later
  # SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>
  ```
- **Dependencies:** All newly proposed third-party dependencies must have Free Software licenses compatible with GPL-3.0 (e.g. MIT, BSD, Apache 2.0, Public Domain) and must be documented in `SBOM.md`.

---

## 3. Development Workflow

### Setting up the Environment
```bash
git clone https://github.com/ideh-labs/senda-search.git
cd senda-search
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Code Style Guidelines
- Format Python code adhering to **PEP 8**.
- Use explicit type annotations for all public functions, classes, and methods.
- Document classes and functions with clear docstrings explaining security assumptions.

### Test Requirements
No pull request will be merged without corresponding automated tests:
```bash
# Run pytest with coverage
pytest -v --cov=senda
```
- Test coverage must remain at or above **85%**.
- All tests must execute deterministically without requiring external network connections.

---

## 4. Submitting Changes

1. Create a feature branch: `git checkout -b feat/my-enhancement`.
2. Commit your changes using conventional commits: `feat(retriever): improve bm25 token weighting`.
3. Push to your fork and submit a Pull Request / Merge Request with a comprehensive description of the changes and ethical justification.
