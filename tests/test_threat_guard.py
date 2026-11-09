# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for ThreatGuard: objective harm blocking, hash prefixes, and audit logging."""

import hashlib
import pytest
from senda.security.threat_guard import ThreatGuard, ThreatCategory


def test_threat_guard_clean_url():
    tg = ThreatGuard()
    is_blocked, cat, exp = tg.check_url("https://fsf.org/free-software")
    assert is_blocked is False
    assert cat is None
    assert exp is None
    assert len(tg.audit_log) == 0


def test_threat_guard_malware_exact_url():
    tg = ThreatGuard()
    malicious_url = "http://malware-sample.example.org/bad.exe"
    tg.register_threat(
        target=malicious_url,
        category=ThreatCategory.MALWARE,
        feed_source="URLhaus (abuse.ch)",
        rule_id="UH-2026-001",
        is_domain=False,
    )

    is_blocked, cat, exp = tg.check_url(malicious_url)
    assert is_blocked is True
    assert cat == ThreatCategory.MALWARE
    assert "URLhaus" in (exp or "")

    assert len(tg.audit_log) == 1
    event = tg.audit_log[0]
    assert event.url == malicious_url
    assert event.domain == "malware-sample.example.org"
    assert event.category == ThreatCategory.MALWARE
    assert "APELACIONES.md" in event.appeal_notice


def test_threat_guard_domain_level_phishing():
    tg = ThreatGuard()
    tg.register_threat(
        target="fake-bank-login.xyz",
        category=ThreatCategory.PHISHING,
        feed_source="PhishTank",
        rule_id="PT-2026-999",
        is_domain=True,
    )

    is_blocked, cat, exp = tg.check_url("https://fake-bank-login.xyz/portal/auth")
    assert is_blocked is True
    assert cat == ThreatCategory.PHISHING
    assert "PhishTank" in (exp or "")


def test_threat_guard_hash_prefix_privacy_preserving():
    tg = ThreatGuard()
    bad_url = "https://fraudulent-crypto-drain.com/claim"
    tg.register_threat(
        target=bad_url,
        category=ThreatCategory.FRAUD,
        feed_source="Official Regulatory Alert",
        rule_id="FRAUD-007",
        is_domain=False,
    )

    # Calculate 8-char SHA-256 prefix
    sha256 = hashlib.sha256(bad_url.encode("utf-8")).hexdigest()
    prefix = sha256[:8]

    matched, cat = tg.check_hash_prefix(prefix)
    assert matched is True
    assert cat == ThreatCategory.FRAUD

    # Non-existent prefix
    matched_fake, _ = tg.check_hash_prefix("00000000")
    assert matched_fake is False


def test_threat_guard_csam_redaction_and_zero_payload():
    tg = ThreatGuard()
    target_url = "http://csam-report.example.net/flagged"
    tg.register_threat(
        target=target_url,
        category=ThreatCategory.CSAM,
        feed_source="Certified Law Enforcement Hash List",
        rule_id="CSAM-HASH-441",
        is_domain=False,
    )

    is_blocked, cat, _ = tg.check_url(target_url)
    assert is_blocked is True
    assert cat == ThreatCategory.CSAM

    # Check that audit log masks URL
    assert len(tg.audit_log) == 1
    event = tg.audit_log[0]
    assert event.url == "[URL_PROTEGIDA_CSAM]"
    assert event.category == ThreatCategory.CSAM
