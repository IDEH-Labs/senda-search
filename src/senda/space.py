# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Space & Astronomical Knowledge Engine.

Provides instant, verified, and ad-free astronomical knowledge cards
for celestial bodies, deep-space missions, and space exploration agencies.
Grounded in official NASA and ESA open-access public data.

Zero tracking, 100% public domain / open science.
"""

from __future__ import annotations

import unicodedata
from typing import Dict, List, Optional
from pydantic import BaseModel

from senda.ranking.suggestions import damerau_levenshtein_distance


class SpaceCard(BaseModel):
    """Structured verifiable space knowledge card."""
    title: str
    category: str
    description: str
    key_facts: Dict[str, str]
    mission_highlights: List[str]
    image_url: Optional[str] = None
    source: str = "NASA / ESA Open Science"
    source_url: str
    license: str = "Dominio Público (NASA / ESA Open Access)"


def _norm(s: str) -> str:
    s = s.lower().strip()
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


SPACE_ENTITIES: Dict[str, SpaceCard] = {
    "marte": SpaceCard(
        title="Marte",
        category="Planeta telúrico • Sistema Solar",
        description=(
            "Cuarto planeta desde el Sol y segundo más pequeño del sistema solar. "
            "Conocido como el «Planeta Rojo» debido al óxido de hierro predominante en su superficie. "
            "Posee la montaña más alta del sistema solar (Monte Olimpo) y valles gigantescos."
        ),
        key_facts={
            "Distancia media al Sol": "227,9 millones de km (1,52 UA)",
            "Duración del día (sol)": "24 horas y 37 minutos",
            "Duración del año": "687 días terrestres",
            "Gravedad superficial": "3,72 m/s² (0,38 de la Tierra)",
            "Satélites naturales": "2 (Fobos y Deimos)",
            "Atmósfera principal": "Dióxido de carbono (95,3%)",
        },
        mission_highlights=[
            "Rover Perseverance (2021-presente): búsqueda de biofirmas antiguas y recolección de muestras",
            "Rover Curiosity (2012-presente): exploración del cráter Gale y habitabilidad pasada",
            "Telescopio Espacial y sondas orbitales (MRO, Mars Express)",
        ],
        image_url="https://images-assets.nasa.gov/image/PIA04304/PIA04304~thumb.jpg",
        source="NASA Science Mars Exploration",
        source_url="https://science.nasa.gov/mars/",
    ),
    "jupiter": SpaceCard(
        title="Júpiter",
        category="Gigante gaseoso • Sistema Solar",
        description=(
            "El planeta más grande del sistema solar, con una masa más de dos veces superior a la de todos los demás planetas juntos. "
            "Famoso por su Gran Mancha Roja, una tormenta colosal activa desde hace siglos, y su potente campo magnético."
        ),
        key_facts={
            "Distancia media al Sol": "778,5 millones de km (5,2 UA)",
            "Duración del día": "9 horas y 56 minutos",
            "Duración del año": "11,86 años terrestres",
            "Diámetro ecuatorial": "142.984 km (11 veces la Tierra)",
            "Satélites confirmados": "95 (incluye a Ío, Europa, Ganímedes y Calisto)",
            "Atmósfera principal": "Hidrógeno (90%) y Helio (10%)",
        },
        mission_highlights=[
            "Sonda Juno (NASA, 2016-presente): estructura interna, atmósfera profunda y auroras polares",
            "Misión JUICE (ESA, 2023): en ruta hacia las lunas heladas de Júpiter",
            "Misión Europa Clipper (NASA, 2024): exploración del océano subterráneo de Europa",
        ],
        image_url="https://images-assets.nasa.gov/image/PIA22949/PIA22949~thumb.jpg",
        source="NASA Science Jupiter",
        source_url="https://science.nasa.gov/jupiter/",
    ),
    "saturno": SpaceCard(
        title="Saturno",
        category="Gigante gaseoso • Sistema Solar",
        description=(
            "Sexto planeta desde el Sol, célebre por su espectacular y complejo sistema de anillos compuestos por partículas de hielo y roca. "
            "Es el planeta menos denso del sistema solar (flotaría en agua) y posee una fascinante luna con atmósfera densa (Titán) y otra con géiseres (Encélado)."
        ),
        key_facts={
            "Distancia media al Sol": "1.434 millones de km (9,58 UA)",
            "Duración del día": "10 horas y 33 minutos",
            "Duración del año": "29,45 años terrestres",
            "Diámetro ecuatorial": "120.536 km (9,4 veces la Tierra)",
            "Satélites confirmados": "146 lunas descubiertas",
            "Sistema de anillos": "Extensión de 282.000 km, grosor medio de solo 10 metros",
        },
        mission_highlights=[
            "Misión Cassini-Huygens (NASA/ESA, 2004-2017): exploración orbital y aterrizaje en Titán",
            "Descubrimiento de géiseres de agua salada en el polo sur de Encélado",
        ],
        image_url="https://images-assets.nasa.gov/image/PIA18274/PIA18274~thumb.jpg",
        source="NASA Science Saturn",
        source_url="https://science.nasa.gov/saturn/",
    ),
    "luna": SpaceCard(
        title="La Luna",
        category="Satélite natural • Tierra",
        description=(
            "Único satélite natural permanente de la Tierra y quinto más grande del sistema solar. "
            "Modula las mareas terrestres, estabiliza la inclinación del eje de la Tierra y es el único cuerpo celeste más allá de nuestro planeta pisado por seres humanos."
        ),
        key_facts={
            "Distancia media a la Tierra": "384.400 km",
            "Diámetro": "3.474 km (aproximadamente un cuarto de la Tierra)",
            "Periodo orbital y rotación": "27,3 días (rotación sincrónica, siempre muestra la misma cara)",
            "Gravedad superficial": "1,62 m/s² (1/6 de la Tierra)",
            "Temperatura": "De -130 °C en la noche a 120 °C en el día lunar",
        },
        mission_highlights=[
            "Programa Apolo (1969-1972): 12 astronautas caminaron sobre la superficie lunar",
            "Programa Artemis (NASA/ESA/socios internacionales): retorno humano sostenible y base lunar",
            "Sonda Lunar Reconnaissance Orbiter (LRO): cartografía de alta resolución y depósitos de hielo en los polos",
        ],
        image_url="https://images-assets.nasa.gov/image/PIA00405/PIA00405~thumb.jpg",
        source="NASA Moon Exploration",
        source_url="https://science.nasa.gov/moon/",
    ),
    "james_webb": SpaceCard(
        title="Telescopio Espacial James Webb (JWST)",
        category="Observatorio espacial infrarrojo • Misión internacional",
        description=(
            "El telescopio espacial de ciencia astronómica más potente y complejo jamás construido. "
            "Desarrollado conjuntamente por la NASA, la ESA y la Agencia Espacial Canadiense (CSA). "
            "Opera en el infrarrojo para observar las primeras galaxias formadas tras el Big Bang y estudiar atmósferas de exoplanetas."
        ),
        key_facts={
            "Lanzamiento": "25 de diciembre de 2021 (Cohete Ariane 5, Guayana Francesa)",
            "Ubicación orbital": "Punto de Lagrange L2 Sol-Tierra (1,5 millones de km de la Tierra)",
            "Diámetro del espejo primario": "6,5 metros (18 segmentos hexagonales de berilio recubiertos de oro)",
            "Escudo térmico": "5 capas de Kapton del tamaño de una pista de tenis",
            "Longitudes de onda": "Infrarrojo cercano y medio (0,6 a 28 micrómetros)",
        },
        mission_highlights=[
            "Primera imagen de campo profundo más nítida del universo distante (SMACS 0723)",
            "Detección de vapor de agua y dióxido de carbono en atmósferas de exoplanetas",
            "Observación de guarderías estelares (Pilares de la Creación, Nebulosa de Carina)",
        ],
        image_url="https://images-assets.nasa.gov/image/GSFC_20171208_archive_e001465/GSFC_20171208_archive_e001465~thumb.jpg",
        source="NASA / ESA Webb Space Telescope",
        source_url="https://webb.nasa.gov/",
    ),
    "hubble": SpaceCard(
        title="Telescopio Espacial Hubble",
        category="Observatorio espacial óptico y ultravioleta • NASA / ESA",
        description=(
            "Uno de los instrumentos científicos más revolucionarios de la historia de la humanidad. "
            "En órbita terrestre baja desde 1990, ha realizado más de 1,5 millones de observaciones científicas que determinaron la edad del universo y confirmaron la existencia de agujeros negros supermasivos."
        ),
        key_facts={
            "Lanzamiento": "24 de abril de 1990 (Transbordador espacial Discovery, STS-31)",
            "Órbita": "Órbita terrestre baja (540 km de altitud)",
            "Diámetro del espejo primario": "2,4 metros",
            "Velocidad": "27.300 km/h (completa una órbita cada 95 minutos)",
            "Espectro óptico": "Luz visible, ultravioleta y parte del infrarrojo cercano",
        },
        mission_highlights=[
            "Medición precisa de la tasa de expansión del universo (Constante de Hubble)",
            "Imágenes del Hubble Deep Field (miles de galaxias en un punto diminuto del cielo)",
            "Más de 30 años de servicio científico continuado",
        ],
        image_url="https://images-assets.nasa.gov/image/PIA15422/PIA15422~thumb.jpg",
        source="NASA / ESA Hubble Mission",
        source_url="https://science.nasa.gov/mission/hubble/",
    ),
    "iss": SpaceCard(
        title="Estación Espacial Internacional (EEI / ISS)",
        category="Laboratorio de microgravedad en órbita • Cooperación internacional",
        description=(
            "El objeto artificial más grande en órbita terrestre y el laboratorio de investigación científica habitado continuamente desde noviembre del año 2000. "
            "Es un proyecto conjunto de las agencias espaciales NASA, Roscosmos, ESA, JAXA y CSA."
        ),
        key_facts={
            "Altitud orbital": "Aproximadamente 408 km sobre la Tierra",
            "Velocidad de traslación": "27.600 km/h (16 amaneceres y atardeceres cada día)",
            "Masa": "Aproximadamente 450 toneladas",
            "Envergadura solar": "109 metros (similar a un campo de fútbol)",
            "Tripulación habitual": "7 astronautas e investigadores",
        },
        mission_highlights=[
            "Más de 3.000 experimentos científicos en biología humana, física de fluidos y materiales",
            "Demostración de tecnologías críticas para futuras misiones a la Luna y Marte",
            "Cooperación pacífica internacional continua en el espacio",
        ],
        image_url="https://images-assets.nasa.gov/image/iss064e054179/iss064e054179~thumb.jpg",
        source="NASA International Space Station",
        source_url="https://science.nasa.gov/international-space-station/",
    ),
}

SPACE_ALIASES: Dict[str, str] = {
    "marte": "marte",
    "planeta marte": "marte",
    "el planeta rojo": "marte",
    "mars": "marte",
    "jupiter": "jupiter",
    "planeta jupiter": "jupiter",
    "saturno": "saturno",
    "planeta saturno": "saturno",
    "anillos de saturno": "saturno",
    "luna": "luna",
    "la luna": "luna",
    "luna terrestre": "luna",
    "moon": "luna",
    "james webb": "james_webb",
    "telescopio james webb": "james_webb",
    "jwst": "james_webb",
    "telescopio webb": "james_webb",
    "hubble": "hubble",
    "telescopio hubble": "hubble",
    "telescopio espacial hubble": "hubble",
    "iss": "iss",
    "eei": "iss",
    "estacion espacial": "iss",
    "estacion espacial internacional": "iss",
    "international space station": "iss",
}


def evaluate_space_query(query: str) -> Optional[SpaceCard]:
    """
    Evaluate if query matches a prominent space body or mission.
    Supports alias lookups and edit-distance typo tolerance.
    Deterministic, offline, zero-tracking.
    """
    clean_q = _norm(query)
    if not clean_q or len(clean_q) < 3:
        return None

    if clean_q in SPACE_ALIASES:
        return SPACE_ENTITIES.get(SPACE_ALIASES[clean_q])

    for alias, canonical_key in SPACE_ALIASES.items():
        if alias == clean_q or f" {alias} " in f" {clean_q} ":
            return SPACE_ENTITIES.get(canonical_key)

    max_d = 1 if len(clean_q) < 7 else 2
    best_match: Optional[str] = None
    best_dist = 999

    for alias, canonical_key in SPACE_ALIASES.items():
        if abs(len(alias) - len(clean_q)) <= max_d:
            dist = damerau_levenshtein_distance(clean_q, alias)
            if dist <= max_d and dist < best_dist:
                best_dist = dist
                best_match = canonical_key
                if dist == 1:
                    break

    if best_match:
        return SPACE_ENTITIES.get(best_match)

    return None
