# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import socket
from unittest.mock import patch
import pytest

from senda.crawler.network_guard import NetworkGuard, SSRFSecurityViolation


def test_loopback_ips_blocked():
    assert not NetworkGuard.is_ip_allowed("127.0.0.1")
    assert not NetworkGuard.is_ip_allowed("127.0.1.1")
    assert not NetworkGuard.is_ip_allowed("::1")


def test_rfc1918_private_ips_blocked():
    assert not NetworkGuard.is_ip_allowed("10.0.0.1")
    assert not NetworkGuard.is_ip_allowed("10.254.254.254")
    assert not NetworkGuard.is_ip_allowed("172.16.0.1")
    assert not NetworkGuard.is_ip_allowed("172.31.255.255")
    assert not NetworkGuard.is_ip_allowed("192.168.1.1")
    assert not NetworkGuard.is_ip_allowed("192.168.0.254")
    assert not NetworkGuard.is_ip_allowed("fc00::1")
    assert not NetworkGuard.is_ip_allowed("fd00::dead:beef")


def test_cloud_metadata_link_local_blocked():
    # 169.254.169.254 is the standard AWS / GCP / Azure metadata endpoint
    assert not NetworkGuard.is_ip_allowed("169.254.169.254")
    assert not NetworkGuard.is_ip_allowed("fe80::1")


def test_carrier_grade_nat_blocked():
    assert not NetworkGuard.is_ip_allowed("100.64.0.1")
    assert not NetworkGuard.is_ip_allowed("100.127.255.254")


def test_multicast_and_reserved_blocked():
    assert not NetworkGuard.is_ip_allowed("224.0.0.1")
    assert not NetworkGuard.is_ip_allowed("240.0.0.1")
    assert not NetworkGuard.is_ip_allowed("0.0.0.0")
    assert not NetworkGuard.is_ip_allowed("::")


def test_ipv4_mapped_ipv6_unpacked_and_blocked():
    assert not NetworkGuard.is_ip_allowed("::ffff:127.0.0.1")
    assert not NetworkGuard.is_ip_allowed("::ffff:169.254.169.254")
    assert not NetworkGuard.is_ip_allowed("::ffff:10.0.0.1")


def test_public_ips_allowed():
    assert NetworkGuard.is_ip_allowed("1.1.1.1")
    assert NetworkGuard.is_ip_allowed("8.8.8.8")
    assert NetworkGuard.is_ip_allowed("93.184.216.34")  # example.com
    assert NetworkGuard.is_ip_allowed("2606:2800:220:1:248:1893:25c8:1946")


def test_scheme_validation():
    with pytest.raises(SSRFSecurityViolation, match="Prohibited URL scheme"):
        NetworkGuard.validate_url("file:///etc/passwd")

    with pytest.raises(SSRFSecurityViolation, match="Prohibited URL scheme"):
        NetworkGuard.validate_url("gopher://127.0.0.1:70")

    with pytest.raises(SSRFSecurityViolation, match="Prohibited URL scheme"):
        NetworkGuard.validate_url("ftp://example.com/test")

    with pytest.raises(SSRFSecurityViolation, match="Prohibited URL scheme"):
        NetworkGuard.validate_url("data:text/html,hello")


def test_raw_ip_literal_validation():
    with pytest.raises(SSRFSecurityViolation, match="forbidden non-public IP literal"):
        NetworkGuard.resolve_and_validate("127.0.0.1")

    with pytest.raises(SSRFSecurityViolation, match="forbidden non-public IP literal"):
        NetworkGuard.resolve_and_validate("169.254.169.254")


def test_dns_resolution_returning_private_ip_is_blocked():
    mock_addrinfo = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 80))
    ]
    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with pytest.raises(SSRFSecurityViolation, match="prohibited IP '10.0.0.5'"):
            NetworkGuard.resolve_and_validate("evil-internal.example.org", 80)


def test_tor_onion_address_validation():
    # Valid v3 onion (56 chars base32)
    valid_v3 = "expyuzz5wqqfdgah56trgahphgahpagah56trgahphgahpagah56trga.onion"
    ips = NetworkGuard.resolve_and_validate(valid_v3)
    assert ips == ["127.0.0.1"]

    # Invalid characters in onion address
    with pytest.raises(SSRFSecurityViolation, match="Invalid Tor .onion address format"):
        NetworkGuard.resolve_and_validate("invalid_onion_address!@#.onion")

    # Invalid length
    with pytest.raises(SSRFSecurityViolation, match="Invalid Tor .onion address format"):
        NetworkGuard.resolve_and_validate("short.onion")
