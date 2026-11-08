# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import pytest
from senda.frontier.canonical import canonicalize_url, is_spider_trap


def test_scheme_and_host_lowercase():
    raw = "HTTPS://WWW.Example.COM/Path"
    assert canonicalize_url(raw) == "https://www.example.com/Path"


def test_default_ports_stripped():
    assert canonicalize_url("http://example.com:80/page") == "http://example.com/page"
    assert canonicalize_url("https://example.com:443/page") == "https://example.com/page"
    # Non-standard ports preserved
    assert canonicalize_url("http://example.com:8080/page") == "http://example.com:8080/page"


def test_fragments_stripped():
    raw = "https://example.com/docs#installation"
    assert canonicalize_url(raw) == "https://example.com/docs"


def test_tracking_query_params_stripped():
    raw = "https://example.com/item?utm_source=twitter&id=123&fbclid=XYZ&category=books&utm_campaign=spring"
    # Should strip utm_source, fbclid, utm_campaign and sort remaining: category=books&id=123
    assert canonicalize_url(raw) == "https://example.com/item?category=books&id=123"


def test_path_normalization():
    assert canonicalize_url("https://example.com/a//b/./c/") == "https://example.com/a/b/c/"
    assert canonicalize_url("https://example.com/a/b/../c") == "https://example.com/a/c"


def test_unreserved_percent_encoding_decoded():
    # %7E is ~ (tilde, unreserved). %2F is / (reserved, kept or handled)
    assert canonicalize_url("https://example.com/user/%7Ealice") == "https://example.com/user/~alice"


def test_spider_trap_length_exceeded():
    long_url = "https://example.com/" + "a" * 600
    assert is_spider_trap(long_url, max_length=512)


def test_spider_trap_excessive_path_depth():
    deep_url = "https://example.com/level1/level2/level3/level4/level5/level6"
    assert is_spider_trap(deep_url, max_path_depth=5)
    shallow_url = "https://example.com/level1/level2/level3"
    assert not is_spider_trap(shallow_url, max_path_depth=5)


def test_spider_trap_repeated_segments():
    looping_url = "https://example.com/forum/topic/forum/topic/forum/topic"
    assert is_spider_trap(looping_url, max_repeated_segments=2)
    normal_url = "https://example.com/news/2026/11/article"
    assert not is_spider_trap(normal_url, max_repeated_segments=2)
