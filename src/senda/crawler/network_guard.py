# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Network Guard: Anti-SSRF (Server-Side Request Forgery) and DNS validation.

Protects against internal network probing, loopback access, link-local abuse,
and DNS rebinding attacks during web crawling.
"""

import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse


class SSRFSecurityViolation(Exception):
    """Raised when a URL or resolved IP attempts to target a non-public or forbidden destination."""
    pass


class NetworkGuard:
    """Strict network destination validator for the crawler."""

    # Explicitly forbidden CIDR ranges in addition to standard library flags
    ADDITIONAL_BLOCKED_NETWORKS = [
        ipaddress.ip_network("100.64.0.0/10"),    # Carrier-Grade NAT (RFC 6598)
        ipaddress.ip_network("192.0.0.0/24"),     # IETF Protocol Assignments (RFC 6890)
        ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1 (RFC 5737)
        ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2 (RFC 5737)
        ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3 (RFC 5737)
        ipaddress.ip_network("240.0.0.0/4"),      # Reserved for Future Use (RFC 1112)
        ipaddress.ip_network("255.255.255.255/32"), # Limited Broadcast
    ]

    ALLOWED_SCHEMES = frozenset({"http", "https"})

    @classmethod
    def is_ip_allowed(cls, ip: str | ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Verify whether an IP address is a safe, publicly routable unicast address.

        Disallows loopback, private, link-local, multicast, reserved, and CGNAT ranges.
        Unpacks IPv4-mapped IPv6 addresses (e.g., ::ffff:127.0.0.1) before checking.
        """
        if not isinstance(ip, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            try:
                ip = ipaddress.ip_address(ip)
            except ValueError:
                return False

        # Unpack IPv4-mapped IPv6 addresses (::ffff:192.0.2.1)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped

        # Standard Python ipaddress safety checks
        if (
            ip.is_loopback          # 127.0.0.0/8, ::1
            or ip.is_private        # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7
            or ip.is_link_local     # 169.254.0.0/16, fe80::/10 (Critical: AWS/cloud metadata)
            or ip.is_multicast      # 224.0.0.0/4, ff00::/8
            or ip.is_reserved       # IETF reserved
            or ip.is_unspecified    # 0.0.0.0, ::
        ):
            return False

        # Check against additional forbidden blocks (CGNAT, test networks)
        for network in cls.ADDITIONAL_BLOCKED_NETWORKS:
            if ip in network:
                return False

        return True

    @classmethod
    def is_onion_hostname(cls, hostname: Optional[str]) -> bool:
        """Check if hostname is a Tor Special-Use Domain (.onion per RFC 7686)."""
        if not hostname:
            return False
        return hostname.lower().strip().endswith(".onion")

    @classmethod
    def validate_onion_format(cls, hostname: str) -> str:
        """Validate format of a .onion hostname (RFC 7686 / Tor v3 56 chars or v2 16 chars).
        
        Raises SSRFSecurityViolation if malformed.
        Returns normalized lowercase hostname.
        """
        clean = hostname.lower().strip()
        if not clean.endswith(".onion"):
            raise SSRFSecurityViolation(f"Host '{hostname}' is not a .onion address.")
        onion_label = clean[:-6]
        base32_chars = set("abcdefghijklmnopqrstuvwxyz234567")
        if len(onion_label) in (16, 56) and set(onion_label).issubset(base32_chars):
            return clean
        raise SSRFSecurityViolation(f"Invalid Tor .onion address format: '{hostname}'.")

    @classmethod
    def resolve_and_validate(cls, hostname: str, port: int = 443, allow_onion: bool = False) -> list[str]:
        """Resolve DNS for a hostname and verify all returned IP addresses are public.

        Returns a list of validated IP address strings.
        Raises SSRFSecurityViolation if ANY resolved address is forbidden.
        """
        if not hostname:
            raise SSRFSecurityViolation("Empty or missing hostname.")

        # Check if the hostname itself is a raw IP literal
        try:
            ip_literal = ipaddress.ip_address(hostname)
            if not cls.is_ip_allowed(ip_literal):
                raise SSRFSecurityViolation(f"Host '{hostname}' is a forbidden non-public IP literal.")
            return [str(ip_literal)]
        except ValueError:
            pass  # It's a standard domain name or special-use domain

        # Tor Special-Use Domain (.onion per RFC 7686)
        if cls.is_onion_hostname(hostname):
            if not allow_onion:
                raise SSRFSecurityViolation(
                    f"Destino .onion denegado sin proxy Tor SOCKS autorizado: '{hostname}'. "
                    f"Se prohíbe terminantemente la resolución directa y la conexión sin proxy."
                )
            cls.validate_onion_format(hostname)
            # Never resolve .onion via local DNS, and never substitute by 127.0.0.1.
            # Remote SOCKS proxy will handle onion circuit resolution.
            return []

        # Resolve through system resolver
        try:
            addr_info = socket.getaddrinfo(
                hostname,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP
            )
        except (socket.gaierror, socket.herror) as e:
            raise SSRFSecurityViolation(f"DNS resolution failed for '{hostname}': {e}") from e

        if not addr_info:
            raise SSRFSecurityViolation(f"No address records found for hostname '{hostname}'.")

        validated_ips: list[str] = []
        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]

            if not cls.is_ip_allowed(ip_str):
                raise SSRFSecurityViolation(
                    f"DNS resolution for '{hostname}' returned prohibited IP '{ip_str}' (SSRF defense)."
                )
            if ip_str not in validated_ips:
                validated_ips.append(ip_str)

        return validated_ips

    @classmethod
    def validate_url(cls, url: str, allow_onion: bool = False) -> tuple[str, list[str]]:
        """Validate an entire URL against scheme, structure, and SSRF restrictions.

        Returns a tuple of (normalized_scheme_and_host, list_of_validated_ips).
        Raises SSRFSecurityViolation on any violation.
        """
        parsed = urlparse(url)

        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            raise SSRFSecurityViolation(
                f"Prohibited URL scheme '{parsed.scheme}'. Only http and https are permitted."
            )

        hostname = parsed.hostname
        if not hostname:
            raise SSRFSecurityViolation(f"URL '{url}' does not contain a valid hostname.")

        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        validated_ips = cls.resolve_and_validate(hostname, port, allow_onion=allow_onion)

        return f"{parsed.scheme.lower()}://{hostname}", validated_ips
