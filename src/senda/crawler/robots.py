# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Robots Exclusion Standard parser conforming strictly to IETF RFC 9309.

Provides rule matching (wildcard '*' and end-anchor '$'), rule precedence
(most specific path wins, allow beats disallow on tie), crawl-delay parsing,
and domain policy caching.
"""

import fnmatch
import re
import time
from typing import Optional
from urllib.parse import urlparse, unquote


class RobotsRule:
    """Represents a single Allow or Disallow rule in a robots.txt file."""

    def __init__(self, path_pattern: str, is_allow: bool):
        self.pattern = path_pattern.strip()
        self.is_allow = is_allow
        # Compile RFC 9309 pattern to regex:
        # '*' matches any sequence of characters
        # '$' at end matches end of path
        # Special regex characters are escaped except '*' and '$'
        self.regex = self._compile_rfc9309(self.pattern)

    @staticmethod
    def _compile_rfc9309(pattern: str) -> re.Pattern:
        if not pattern:
            return re.compile(r"^")  # Matches empty pattern

        # RFC 9309 Section 2.2.2: Pattern characters
        parts = []
        has_end_anchor = pattern.endswith("$")
        clean_pattern = pattern[:-1] if has_end_anchor else pattern

        for char in clean_pattern:
            if char == "*":
                parts.append(".*")
            else:
                parts.append(re.escape(char))

        regex_str = "^" + "".join(parts)
        if has_end_anchor:
            regex_str += "$"

        return re.compile(regex_str)

    def matches(self, path: str) -> bool:
        if not self.pattern:
            return False
        return bool(self.regex.match(path))

    @property
    def length(self) -> int:
        return len(self.pattern)


class RobotsGroup:
    """A collection of rules and directives applying to matched user-agents."""

    def __init__(self):
        self.user_agents: list[str] = []
        self.rules: list[RobotsRule] = []
        self.crawl_delay: Optional[float] = None

    def is_allowed(self, path: str) -> bool:
        """Evaluate path against rules according to RFC 9309 precedence:

        1. The most specific (longest pattern) match determines the outcome.
        2. On equal length match, Allow takes precedence over Disallow.
        3. If no rules match, the path is allowed by default.
        """
        matching_rules = [r for r in self.rules if r.matches(path)]
        if not matching_rules:
            return True

        # Sort by rule pattern length descending (longest pattern wins)
        # In case of tie, allow (is_allow=True) sorts before disallow (is_allow=False)
        matching_rules.sort(key=lambda r: (r.length, r.is_allow), reverse=True)
        winner = matching_rules[0]
        return winner.is_allow


class RobotsPolicy:
    """Parsed robots.txt document representing a website's crawling policy."""

    def __init__(self, content: str, default_agent: str = "SendaBot"):
        self.raw_content = content
        self.default_agent = default_agent.lower()
        self.groups: list[RobotsGroup] = []
        self._parse(content)

    def _parse(self, content: str) -> None:
        current_group: Optional[RobotsGroup] = None
        in_user_agent_block = False

        for raw_line in content.splitlines():
            # Strip comments
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            val = value.strip()

            if key == "user-agent":
                agent_name = val.lower()
                if not in_user_agent_block:
                    current_group = RobotsGroup()
                    self.groups.append(current_group)
                    in_user_agent_block = True
                if current_group:
                    current_group.user_agents.append(agent_name)
            else:
                in_user_agent_block = False
                if current_group is None:
                    continue

                if key == "allow":
                    current_group.rules.append(RobotsRule(val, is_allow=True))
                elif key == "disallow":
                    # An empty Disallow means "allow everything" in robots.txt standard
                    if val == "":
                        current_group.rules.append(RobotsRule("/", is_allow=True))
                    else:
                        current_group.rules.append(RobotsRule(val, is_allow=False))
                elif key == "crawl-delay":
                    try:
                        delay = float(val)
                        if delay >= 0:
                            current_group.crawl_delay = delay
                    except ValueError:
                        pass

    def get_group_for_agent(self, agent: Optional[str] = None) -> RobotsGroup:
        target_agent = (agent or self.default_agent).lower()

        # RFC 9309: First look for exact or substring match of our agent
        for group in self.groups:
            for ua in group.user_agents:
                if ua in target_agent or target_agent in ua:
                    return group

        # Otherwise look for wildcard '*'
        for group in self.groups:
            if "*" in group.user_agents:
                return group

        # Default empty group (everything allowed)
        return RobotsGroup()

    def is_allowed(self, url: str, agent: Optional[str] = None) -> bool:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        # Unquote path per RFC 9309 section 2.2.1
        clean_path = unquote(path)
        group = self.get_group_for_agent(agent)
        return group.is_allowed(clean_path)

    def get_crawl_delay(self, agent: Optional[str] = None) -> Optional[float]:
        group = self.get_group_for_agent(agent)
        return group.crawl_delay


class RobotsCache:
    """In-memory cache for parsed domain robots.txt policies with TTL."""

    def __init__(self, ttl_seconds: float = 86400.0):  # 24 hours default
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[float, RobotsPolicy]] = {}

    def get(self, domain: str) -> Optional[RobotsPolicy]:
        now = time.time()
        if domain in self._cache:
            created_at, policy = self._cache[domain]
            if now - created_at < self.ttl:
                return policy
            del self._cache[domain]
        return None

    def set(self, domain: str, policy: RobotsPolicy) -> None:
        self._cache[domain] = (time.time(), policy)

    def invalidate(self, domain: str) -> None:
        self._cache.pop(domain, None)

    def clear(self) -> None:
        self._cache.clear()


class RobotsPolicyManager:
    """High-level manager coordinating domain robots.txt fetching and evaluation."""

    def __init__(self, cache: Optional[RobotsCache] = None):
        self._cache = cache or RobotsCache()

    def has_policy(self, domain: str) -> bool:
        return self._cache.get(domain) is not None

    def register_policy(self, domain: str, content: str) -> RobotsPolicy:
        policy = RobotsPolicy(content)
        self._cache.set(domain, policy)
        return policy

    def register_empty_policy(self, domain: str) -> RobotsPolicy:
        policy = RobotsPolicy("User-agent: *\nAllow: /\n")
        self._cache.set(domain, policy)
        return policy

    def is_allowed(self, url: str, user_agent: Optional[str] = None) -> bool:
        domain = urlparse(url).netloc.lower()
        policy = self._cache.get(domain)
        if policy is None:
            return True
        return policy.is_allowed(url, user_agent)

    def get_crawl_delay(self, domain: str, user_agent: Optional[str] = None) -> Optional[float]:
        policy = self._cache.get(domain)
        if policy is None:
            return None
        return policy.get_crawl_delay(user_agent)

