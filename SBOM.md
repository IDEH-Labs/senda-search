# Senda — Software Bill of Materials (SBOM)

SPDX-License-Identifier: GPL-3.0-or-later

## Overview
This document records every external software library and component utilized by Senda, their exact license, upstream repository, and architectural justification. Senda adheres strictly to GNU GPL-3.0-or-later compatibility.

| Component | Version Constraint | License (SPDX) | Upstream URL | Purpose / Justification |
|---|---|---|---|---|
| **Python** | `>= 3.12` | Python-2.0 | <https://www.python.org> | Core runtime environment. |
| **SQLite FTS5** | Bundled with Python | Public Domain / BLESSING | <https://www.sqlite.org> | Zero-dependency embedded full-text search engine with BM25 ranking and Unicode61 tokenizer. |
| **FastAPI** | `>= 0.115` | MIT | <https://github.com/fastapi/fastapi> | High-performance, strictly-typed ASGI web framework for the search API. |
| **Uvicorn** | `>= 0.30` | BSD-3-Clause | <https://github.com/encode/uvicorn> | Lightweight ASGI server implementation. |
| **HTTPX** | `>= 0.27` | BSD-3-Clause | <https://github.com/encode/httpx> | Next-generation asynchronous HTTP client for the crawler with granular transport controls. |
| **Beautiful Soup 4** | `>= 4.12` | MIT | <https://www.crummy.com/software/BeautifulSoup/> | Safe DOM parsing and semantic tag extraction using standard library `html.parser`. |
| **Pydantic** | `>= 2.8` | MIT | <https://github.com/pydantic/pydantic> | Data validation and type enforcement for configuration and API schemas. |
| **pytest** | `>= 8.0` (dev) | MIT | <https://github.com/pytest-dev/pytest> | Automated test framework. |
| **pytest-asyncio**| `>= 0.24` (dev) | Apache-2.0 | <https://github.com/pytest-dev/pytest-asyncio> | Asynchronous test execution for crawler and API. |

All above licenses (MIT, BSD-3-Clause, Apache-2.0, Python-2.0, Public Domain) are recognized by the Free Software Foundation (FSF) as fully compatible with GNU GPL-3.0-or-later.
