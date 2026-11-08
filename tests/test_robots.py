# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import pytest
from senda.crawler.robots import RobotsPolicy, RobotsCache


def test_basic_disallow_and_allow():
    content = """
    User-agent: *
    Disallow: /admin
    Disallow: /private/
    Allow: /private/public-preview
    """
    policy = RobotsPolicy(content, default_agent="SendaBot")

    assert policy.is_allowed("https://example.com/index.html")
    assert not policy.is_allowed("https://example.com/admin")
    assert not policy.is_allowed("https://example.com/admin/settings")
    assert not policy.is_allowed("https://example.com/private/secret.pdf")
    # Longest pattern wins: /private/public-preview (len 23) > /private/ (len 9)
    assert policy.is_allowed("https://example.com/private/public-preview")


def test_rfc9309_wildcards_and_anchors():
    content = """
    User-agent: *
    Disallow: /*.gif$
    Disallow: /temp*
    Allow: /temp/keep
    """
    policy = RobotsPolicy(content)

    assert not policy.is_allowed("https://example.com/images/cat.gif")
    # Does not end in .gif
    assert policy.is_allowed("https://example.com/images/cat.gif.html")
    assert not policy.is_allowed("https://example.com/temporary-files")
    assert not policy.is_allowed("https://example.com/temp/discard")
    assert policy.is_allowed("https://example.com/temp/keep")


def test_rfc9309_equal_length_allow_wins_tie():
    # RFC 9309 Section 2.2.2: on equal length, Allow wins
    content = """
    User-agent: *
    Disallow: /page
    Allow: /page
    """
    policy = RobotsPolicy(content)
    assert policy.is_allowed("https://example.com/page")


def test_specific_user_agent_targeting():
    content = """
    User-agent: SendaBot
    Disallow: /forbidden-for-senda
    Crawl-delay: 4.5

    User-agent: *
    Disallow: /forbidden-for-all
    Crawl-delay: 1.0
    """
    policy = RobotsPolicy(content, default_agent="SendaBot")

    # SendaBot specific group applies
    assert not policy.is_allowed("https://example.com/forbidden-for-senda", agent="SendaBot")
    assert policy.is_allowed("https://example.com/forbidden-for-all", agent="SendaBot")
    assert policy.get_crawl_delay(agent="SendaBot") == 4.5

    # Generic bot group applies to OtherBot
    assert policy.is_allowed("https://example.com/forbidden-for-senda", agent="OtherBot")
    assert not policy.is_allowed("https://example.com/forbidden-for-all", agent="OtherBot")
    assert policy.get_crawl_delay(agent="OtherBot") == 1.0


def test_empty_disallow_means_allow_all():
    content = """
    User-agent: *
    Disallow:
    """
    policy = RobotsPolicy(content)
    assert policy.is_allowed("https://example.com/anything")
    assert policy.is_allowed("https://example.com/secret")


def test_robots_cache_ttl():
    cache = RobotsCache(ttl_seconds=1.0)
    policy = RobotsPolicy("User-agent: *\nDisallow: /no")
    cache.set("example.com", policy)

    assert cache.get("example.com") is policy
    cache.invalidate("example.com")
    assert cache.get("example.com") is None
