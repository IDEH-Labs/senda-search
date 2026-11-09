# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Auditable threat intelligence engine and hard-block gating.

Enforces strictly objective harm blocking:
1. Malware activo (verificado por feeds CC0 como URLhaus / abuse.ch).
2. Phishing y suplantación de identidad comprobable.
3. Fraude y estafas financieras comprobables.
4. Material de Abuso Sexual Infantil (CSAM) - Tolerancia cero, bloqueo inmediato sin descarga.

All other domains are labeled ('sin evaluar' or qualified warnings), NEVER hidden or silently removed.
Every hard block generates an auditable record linked to docs/APELACIONES.md.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import logging
from typing import Optional, Set, Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ThreatCategory(str, Enum):
    MALWARE = "malware"
    PHISHING = "phishing"
    FRAUD = "fraude"
    CSAM = "abuso_infantil"


@dataclass(frozen=True)
class BlockAuditEvent:
    """Immutable audit record generated whenever an objective harm hard-block occurs."""
    timestamp: str
    url: str
    domain: str
    url_sha256: str
    category: ThreatCategory
    feed_source: str
    rule_id: str
    appeal_url: str = "/docs/APELACIONES.md"
    appeal_notice: str = "Apelación pública y gratuita disponible según docs/APELACIONES.md"


class ThreatGuard:
    """Zero-compromise security filter enforcing objective harm gating and privacy-preserving prefix checks."""

    def __init__(self):
        # Exact blocked URLs (normalized lowercase) -> (Category, Feed, RuleID)
        self._blocked_urls: Dict[str, tuple[ThreatCategory, str, str]] = {}
        # Blocked domains -> (Category, Feed, RuleID)
        self._blocked_domains: Dict[str, tuple[ThreatCategory, str, str]] = {}
        # SHA-256 prefixes (first 8 hex chars) for privacy-preserving checks
        self._blocked_hash_prefixes: Dict[str, tuple[ThreatCategory, str, str]] = {}
        # Auditable log of all technical blocks executed
        self._audit_log: List[BlockAuditEvent] = []

    @property
    def audit_log(self) -> List[BlockAuditEvent]:
        return list(self._audit_log)

    def register_threat(
        self,
        target: str,
        category: ThreatCategory,
        feed_source: str,
        rule_id: str,
        is_domain: bool = False,
    ) -> None:
        """Register a verified threat entry into the local offline database."""
        clean = target.strip().lower()
        if not clean:
            return

        if is_domain:
            self._blocked_domains[clean] = (category, feed_source, rule_id)
        else:
            self._blocked_urls[clean] = (category, feed_source, rule_id)
            # Register 8-character SHA-256 prefix for privacy-preserving prefix queries
            sha256_full = hashlib.sha256(clean.encode("utf-8")).hexdigest()
            prefix = sha256_full[:8]
            self._blocked_hash_prefixes[prefix] = (category, feed_source, rule_id)

    def check_url(self, url: str) -> tuple[bool, Optional[ThreatCategory], Optional[str]]:
        """Evaluate a URL against objective harm lists.
        
        Returns:
            (is_blocked, category, explanation)
            - is_blocked=True strictly for MALWARE, PHISHING, FRAUD, CSAM.
            - Otherwise is_blocked=False.
        """
        if not url:
            return False, None, None

        clean_url = url.strip().lower()
        try:
            parsed = urlparse(clean_url)
            domain = parsed.hostname or ""
        except Exception:
            domain = ""

        # 1. Check exact URL match
        if clean_url in self._blocked_urls:
            category, feed, rule_id = self._blocked_urls[clean_url]
            self._record_block(url, domain, category, feed, rule_id)
            return True, category, f"Bloqueo duro por daño objetivo ({category.value}) atribuido a {feed}."

        # 2. Check domain-level match
        if domain and domain in self._blocked_domains:
            category, feed, rule_id = self._blocked_domains[domain]
            self._record_block(url, domain, category, feed, rule_id)
            return True, category, f"Bloqueo duro de dominio por daño objetivo ({category.value}) atribuido a {feed}."

        # 3. Check SHA-256 prefix
        url_sha256 = hashlib.sha256(clean_url.encode("utf-8")).hexdigest()
        prefix = url_sha256[:8]
        if prefix in self._blocked_hash_prefixes:
            category, feed, rule_id = self._blocked_hash_prefixes[prefix]
            self._record_block(url, domain, category, feed, rule_id)
            return True, category, f"Bloqueo duro por prefijo de hash criptográfico ({category.value}) atribuido a {feed}."

        return False, None, None

    def check_hash_prefix(self, prefix_hex: str) -> tuple[bool, Optional[ThreatCategory]]:
        """Privacy-preserving hash prefix lookup without transmitting the full target URL."""
        norm_prefix = prefix_hex.strip().lower()[:8]
        if norm_prefix in self._blocked_hash_prefixes:
            cat, _, _ = self._blocked_hash_prefixes[norm_prefix]
            return True, cat
        return False, None

    def _record_block(
        self,
        url: str,
        domain: str,
        category: ThreatCategory,
        feed_source: str,
        rule_id: str,
    ) -> None:
        """Internal auditable logging of blocks."""
        # For CSAM, never log or store raw query text/payload; hash strictly
        safe_url = "[URL_PROTEGIDA_CSAM]" if category == ThreatCategory.CSAM else url
        sha256 = hashlib.sha256(url.encode("utf-8")).hexdigest()
        now_iso = datetime.now(timezone.utc).isoformat()

        event = BlockAuditEvent(
            timestamp=now_iso,
            url=safe_url,
            domain=domain,
            url_sha256=sha256,
            category=category,
            feed_source=feed_source,
            rule_id=rule_id,
        )
        self._audit_log.append(event)
        logger.warning(
            f"ThreatGuard: Bloqueo duro ejecutado en '{domain}' por '{category.value}'. "
            f"Regla: {rule_id}. Fuente: {feed_source}."
        )


# Global singleton instance
threat_guard = ThreatGuard()
