# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Versioned Curated Seed definitions for Senda ethical crawler."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class SeedDefinition:
    id: str
    url: str
    domain: str
    organization: str
    category: str
    license_hint: str
    why_included: str


CURATED_SEEDS: List[SeedDefinition] = [
    SeedDefinition(
        id="seed-fsf",
        url="https://www.fsf.org/",
        domain="www.fsf.org",
        organization="Free Software Foundation",
        category="software_libre",
        license_hint="FDL / CC BY-ND 4.0",
        why_included="Filosofía fundacional del software libre y directrices éticas.",
    ),
    SeedDefinition(
        id="seed-gnu",
        url="https://www.gnu.org/",
        domain="www.gnu.org",
        organization="Proyecto GNU",
        category="software_libre",
        license_hint="GNU FDL / CC BY-ND",
        why_included="Manuales oficiales y documentación del sistema operativo libre.",
    ),
    SeedDefinition(
        id="seed-eff",
        url="https://www.eff.org/",
        domain="www.eff.org",
        organization="Electronic Frontier Foundation",
        category="derechos_digitales",
        license_hint="CC BY 3.0 US",
        why_included="Análisis sobre derechos digitales, privacidad y criptografía.",
    ),
    SeedDefinition(
        id="seed-archive",
        url="https://archive.org/",
        domain="archive.org",
        organization="Internet Archive",
        category="preservacion",
        license_hint="Dominio Público / CC",
        why_included="Preservación de la memoria cultural y web histórica.",
    ),
    SeedDefinition(
        id="seed-wikipedia",
        url="https://en.wikipedia.org/",
        domain="en.wikipedia.org",
        organization="Wikimedia Foundation",
        category="enciclopedia",
        license_hint="CC BY-SA 4.0",
        why_included="Conocimiento general abierto y colaborativo.",
    ),
    SeedDefinition(
        id="seed-doaj",
        url="https://doaj.org/",
        domain="doaj.org",
        organization="Directory of Open Access Journals",
        category="ciencia_abierta",
        license_hint="CC BY-SA 4.0",
        why_included="Publicaciones científicas revisadas por pares en acceso abierto.",
    ),
    SeedDefinition(
        id="seed-arxiv",
        url="https://arxiv.org/",
        domain="arxiv.org",
        organization="Cornell University",
        category="ciencia_abierta",
        license_hint="Metadatos abiertos arXiv",
        why_included="Preprints de investigación en ciencias exactas y computación.",
    ),
    SeedDefinition(
        id="seed-debian",
        url="https://www.debian.org/",
        domain="www.debian.org",
        organization="Proyecto Debian",
        category="software_libre",
        license_hint="DFSG",
        why_included="Gobernanza comunitaria y sistema universal libre.",
    ),
    SeedDefinition(
        id="seed-datos-gov-co",
        url="https://www.datos.gov.co/",
        domain="www.datos.gov.co",
        organization="Gobierno de Colombia / MinTIC",
        category="datos_publicos",
        license_hint="Datos Abiertos Colombia",
        why_included="Transparencia institucional y datos primarios del Estado.",
    ),
    SeedDefinition(
        id="seed-w3c",
        url="https://www.w3.org/",
        domain="www.w3.org",
        organization="World Wide Web Consortium",
        category="estandares_web",
        license_hint="W3C Document License",
        why_included="Estándares abiertos de la web y accesibilidad WCAG.",
    ),
]


def get_curated_seed_urls(category: Optional[str] = None) -> List[str]:
    """Retrieve filtered list of URLs from the curated seed list."""
    if not category:
        return [s.url for s in CURATED_SEEDS]
    clean_cat = category.strip().lower()
    return [s.url for s in CURATED_SEEDS if s.category == clean_cat]
