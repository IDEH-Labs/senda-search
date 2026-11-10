# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Goggles & Domain Ranking Engine
Inspired by Brave Goggles and Kagi Domain Lenses.
Empowers users to customize or apply community-defined ranking rulesets.
Works 100% server-side with zero JavaScript required.
Compatible with Tor Browser (Safest mode) and GNU LibreJS.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
import urllib.parse

from senda.providers.base import SearchResultItem


class SovereignGoggle(BaseModel):
    """User-defined or preset ranking lens."""
    id: str
    name: str
    description: str
    boost_domains: Set[str] = set()
    bury_domains: Set[str] = set()
    discard_domains: Set[str] = set()
    boost_weight: float = 40.0
    bury_weight: float = 40.0


# Built-in sovereign community presets
PRESET_GOGGLES: Dict[str, SovereignGoggle] = {
    "tech_libre": SovereignGoggle(
        id="tech_libre",
        name="Software Libre & Documentación",
        description="Prioriza repositorios libres, wikis comunitarias y documentación técnica oficial; descarta granjas SEO.",
        boost_domains={
            "codeberg.org", "gnu.org", "fsf.org", "kernel.org", "archlinux.org",
            "debian.org", "eff.org", "wikipedia.org", "framasoft.org", "kde.org",
            "gnome.org", "freebsd.org", "gentoo.org", "alpinelinux.org", "fedoraproject.org"
        },
        bury_domains={"quora.com", "medium.com"},
        discard_domains={"pinterest.com", "geeksforgeeks.org", "javatpoint.com", "w3schools.com"},
        boost_weight=45.0,
        bury_weight=35.0,
    ),
    "no_content_farms": SovereignGoggle(
        id="no_content_farms",
        name="Sin Granjas de Contenido ni Muros",
        description="Filtra sitios de agregación masiva, clickbait para anuncios y plataformas de pago agresivas.",
        discard_domains={
            "pinterest.com", "quora.com", "expertreviews.co.uk", "bestproducts.com",
            "ezinearticles.com", "buzzfeed.com", "thesun.co.uk", "dailymail.co.uk"
        },
        bury_domains={"forbes.com", "businessinsider.com"},
        boost_weight=20.0,
        bury_weight=40.0,
    ),
    "science_primary": SovereignGoggle(
        id="science_primary",
        name="Ciencia & Fuentes Primarias",
        description="Prioriza repositorios de acceso abierto, artículos revisados por pares y registros enciclopédicos.",
        boost_domains={
            "arxiv.org", "doaj.org", "openalex.org", "crossref.org", "ncbi.nlm.nih.gov",
            "scielo.org", "redalyc.org", "nature.com", "science.org", "plos.org",
            "wikipedia.org", "wikidata.org"
        },
        discard_domains={"pinterest.com", "quora.com"},
        boost_weight=50.0,
        bury_weight=30.0,
    ),
    "small_web": SovereignGoggle(
        id="small_web",
        name="Webs Personales & Bitácoras",
        description="Rescata blogs personales, bitácoras y publicaciones humanas; descarta megacorporaciones.",
        boost_domains={
            "bearblog.dev", "neocities.org", "mataroa.blog", "writefreely.org",
            "fediverse.party", "mastodon.social", "github.io", "gitlab.io",
            "codeberg.page", "srht.site", "gemini.circumlunar.space"
        },
        discard_domains={
            "amazon.com", "facebook.com", "instagram.com", "tiktok.com",
            "pinterest.com", "linkedin.com", "forbes.com", "businessinsider.com"
        },
        boost_weight=60.0,
        bury_weight=45.0,
    ),
}


def get_available_goggles() -> List[Dict[str, str]]:
    """Return catalog of available lenses for UI dropdowns."""
    catalog = [{"id": "", "name": "Estándar (Sin lente)", "description": "Ranking neutral de Senda sin filtros especiales"}]
    for g in PRESET_GOGGLES.values():
        catalog.append({"id": g.id, "name": g.name, "description": g.description})
    return catalog


def get_preset_goggle(goggle_id: Optional[str]) -> Optional[SovereignGoggle]:
    """Retrieve preconfigured lens by identifier."""
    if not goggle_id:
        return None
    return PRESET_GOGGLES.get(goggle_id.strip().lower())


def parse_goggle_dsl(text: str, name: str = "Lente Personalizada") -> SovereignGoggle:
    """
    Parse standard Brave Goggle DSL / text ruleset into a SovereignGoggle.
    Supported syntax:
      $discard,site=example.com
      $boost=3,site=example.org
      $down=2,site=example.net
    """
    goggle = SovereignGoggle(
        id="custom",
        name=name,
        description="Reglas definidas por el usuario",
        boost_domains=set(),
        bury_domains=set(),
        discard_domains=set(),
    )

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Syntax: $discard,site=domain.com
        if line.startswith("$discard"):
            m = re.search(r"site=([a-zA-Z0-9.-]+)", line, re.I)
            if m:
                goggle.discard_domains.add(m.group(1).lower().strip())
        elif line.startswith("$boost"):
            m = re.search(r"site=([a-zA-Z0-9.-]+)", line, re.I)
            if m:
                goggle.boost_domains.add(m.group(1).lower().strip())
        elif line.startswith("$down") or line.startswith("$bury"):
            m = re.search(r"site=([a-zA-Z0-9.-]+)", line, re.I)
            if m:
                goggle.bury_domains.add(m.group(1).lower().strip())

    return goggle


def match_domain_in_set(domain: str, target_set: Set[str]) -> bool:
    """Check if domain matches or is subdomain of any domain in target_set."""
    domain = domain.lower().strip()
    if domain in target_set:
        return True
    return any(domain.endswith("." + t) for t in target_set)


def apply_goggle_rules(
    items: List[SearchResultItem],
    goggle: Optional[SovereignGoggle],
) -> List[SearchResultItem]:
    """
    Apply lens rules (boost, bury, discard) to a list of SearchResultItem.
    """
    if not goggle or not items:
        return items

    filtered: List[SearchResultItem] = []

    for item in items:
        try:
            domain = urllib.parse.urlparse(item.url).netloc.lower().strip()
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            domain = ""

        # 1. Discard
        if match_domain_in_set(domain, goggle.discard_domains):
            continue

        # 2. Boost
        if match_domain_in_set(domain, goggle.boost_domains):
            item.score += goggle.boost_weight
            item.why_seen = f"[Lente: {goggle.name} — Dominio promovido] {item.why_seen}".strip()

        # 3. Bury
        elif match_domain_in_set(domain, goggle.bury_domains):
            item.score -= goggle.bury_weight
            item.why_seen = f"[Lente: {goggle.name} — Dominio relegado] {item.why_seen}".strip()

        filtered.append(item)

    # Re-sort descending by updated score
    filtered.sort(key=lambda x: x.score, reverse=True)
    return filtered
