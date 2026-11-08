# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""URL Canonicalization and Spider Trap Guards.

Provides canonical normalization, tracking parameter stripping, and spider trap
detection (path loops, depth exhaustion, length overflow).
"""

import posixpath
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, unquote

# Universal tracking and analytics parameters to strip automatically
TRACKING_QUERY_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_cid", "utm_reader", "utm_referrer",
    "fbclid", "gclid", "msclkid", "dclid", "twclid", "yclid",
    "mc_cid", "mc_eid", "_ga", "_gl", "_hsenc", "_hsmi",
    "ref", "source", "trk"
})

UNRESERVED_PATTERNS = re.compile(r"%([0-9a-fA-F]{2})")


def _unreserved_sub(match: re.Match) -> str:
    byte_val = int(match.group(1), 16)
    # RFC 3986 section 2.3: Unreserved characters ALPHA / DIGIT / "-" / "." / "_" / "~"
    if (
        (65 <= byte_val <= 90)    # A-Z
        or (97 <= byte_val <= 122) # a-z
        or (48 <= byte_val <= 57)  # 0-9
        or byte_val in (45, 46, 95, 126) # - . _ ~
    ):
        return chr(byte_val)
    return match.group(0).upper()


def canonicalize_url(url: str) -> str:
    """Transform a raw URL into its canonical, tracking-free representation.

    1. Normalizes scheme and host to lowercase.
    2. Removes default ports (80 for http, 443 for https).
    3. Strips URL fragments (#anchor).
    4. Decodes unreserved percent-encoded characters per RFC 3986.
    5. Normalizes path slashes and relative segments (./, ../).
    6. Strips known marketing/tracking query parameters.
    7. Sorts remaining query parameters alphabetically.
    """
    if not url or not isinstance(url, str):
        return ""

    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return ""

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    # Normalize path
    path = parsed.path
    if not path:
        path = "/"
    else:
        # Collapse double slashes and resolve relative segments safely
        path = re.sub(r"/+", "/", path)
        path = posixpath.normpath(path)
        # Preserve trailing slash if original path had it and it's not root
        if parsed.path.endswith("/") and not path.endswith("/"):
            path += "/"

    # Decode unreserved percent-encoding in path
    path = UNRESERVED_PATTERNS.sub(_unreserved_sub, path)

    # Filter and sort query parameters
    query_str = ""
    if parsed.query:
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_pairs = [
            (k, v) for k, v in pairs if k.lower() not in TRACKING_QUERY_PARAMS
        ]
        if filtered_pairs:
            filtered_pairs.sort(key=lambda item: (item[0], item[1]))
            query_str = urlencode(filtered_pairs)

    # Assemble canonical URL without fragment
    return urlunparse((scheme, netloc, path, "", query_str, ""))


def is_spider_trap(
    url: str,
    max_length: int = 512,
    max_path_depth: int = 5,
    max_repeated_segments: int = 2
) -> bool:
    """Evaluate whether a URL exhibits patterns typical of infinite spider traps.

    - Overly long URLs (character length > max_length)
    - Excessive directory depth (path segment count > max_path_depth)
    - Repeating recursive path loops (e.g. /a/b/a/b/a/b)
    """
    if len(url) > max_length:
        return True

    parsed = urlparse(url)
    segments = [s for s in parsed.path.strip("/").split("/") if s]

    if len(segments) > max_path_depth:
        return True

    # Detect repeated segment loops (e.g., [a, b, a, b] or [page, page])
    segment_counts: dict[str, int] = {}
    for seg in segments:
        segment_counts[seg] = segment_counts.get(seg, 0) + 1
        if segment_counts[seg] > max_repeated_segments:
            return True

    return False
