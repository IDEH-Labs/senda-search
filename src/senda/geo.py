# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Geographic & OpenStreetMap Knowledge Engine.

Provides instant, verifiable, and tracking-free geographic cards
with direct links and embed coordinates for OpenStreetMap (OSM).

Zero Google Maps cookies, zero location surveillance, 100% open cartography.
"""

from __future__ import annotations

import unicodedata
from typing import Dict, Optional
from pydantic import BaseModel

from senda.ranking.suggestions import damerau_levenshtein_distance


class GeoCard(BaseModel):
    """Structured verifiable geographic knowledge card."""
    city_name: str
    admin_region: str
    country: str
    latitude: float
    longitude: float
    coordinates_str: str
    population: Optional[str] = None
    altitude: Optional[str] = None
    osm_map_url: str
    osm_embed_url: str
    source: str = "OpenStreetMap Contributors"
    license: str = "Open Database License (ODbL) / Cartografía Libre"


def _norm(s: str) -> str:
    s = s.lower().strip()
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


# High-frequency global cities and capitals
GLOBAL_CITIES: Dict[str, GeoCard] = {
    "bogota": GeoCard(
        city_name="Bogotá, D.C.",
        admin_region="Cundinamarca (Distrito Capital)",
        country="Colombia",
        latitude=4.7110,
        longitude=-74.0721,
        coordinates_str="4°42′40″N 74°04′20″O",
        population="Aprox. 7.9 millones de habitantes",
        altitude="2.625 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=4.7110&mlon=-74.0721#map=12/4.7110/-74.0721",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-74.20,4.55,-73.95,4.85&layer=mapnik&marker=4.7110,-74.0721",
    ),
    "madrid": GeoCard(
        city_name="Madrid",
        admin_region="Comunidad de Madrid",
        country="España",
        latitude=40.4168,
        longitude=-3.7038,
        coordinates_str="40°25′01″N 3°42′14″O",
        population="Aprox. 3.4 millones de habitantes (6.7M área metropolitana)",
        altitude="657 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=40.4168&mlon=-3.7038#map=12/40.4168/-3.7038",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-3.82,40.32,-3.58,40.52&layer=mapnik&marker=40.4168,-3.7038",
    ),
    "buenos_aires": GeoCard(
        city_name="Buenos Aires (CABA)",
        admin_region="Ciudad Autónoma de Buenos Aires",
        country="Argentina",
        latitude=-34.6037,
        longitude=-58.3816,
        coordinates_str="34°36′13″S 58°22′54″O",
        population="Aprox. 3.1 millones de habitantes (15M Gran Buenos Aires)",
        altitude="25 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=-34.6037&mlon=-58.3816#map=12/-34.6037/-58.3816",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-58.53,-34.70,-58.23,-34.50&layer=mapnik&marker=-34.6037,-58.3816",
    ),
    "ciudad_de_mexico": GeoCard(
        city_name="Ciudad de México (CDMX)",
        admin_region="Valle de México",
        country="México",
        latitude=19.4326,
        longitude=-99.1332,
        coordinates_str="19°25′57″N 99°07′60″O",
        population="Aprox. 9.2 millones de habitantes (21.8M zona metropolitana)",
        altitude="2.240 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=19.4326&mlon=-99.1332#map=12/19.4326/-99.1332",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-99.28,19.30,-98.98,19.55&layer=mapnik&marker=19.4326,-99.1332",
    ),
    "lima": GeoCard(
        city_name="Lima",
        admin_region="Provincia de Lima",
        country="Perú",
        latitude=-12.0464,
        longitude=-77.0428,
        coordinates_str="12°02′47″S 77°02′34″O",
        population="Aprox. 10.0 millones de habitantes",
        altitude="154 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=-12.0464&mlon=-77.0428#map=12/-12.0464/-77.0428",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-77.15,-12.15,-76.90,-11.95&layer=mapnik&marker=-12.0464,-77.0428",
    ),
    "santiago": GeoCard(
        city_name="Santiago de Chile",
        admin_region="Región Metropolitana de Santiago",
        country="Chile",
        latitude=-33.4489,
        longitude=-70.6693,
        coordinates_str="33°26′56″S 70°40′09″O",
        population="Aprox. 6.2 millones de habitantes",
        altitude="570 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=-33.4489&mlon=-70.6693#map=12/-33.4489/-70.6693",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-70.78,-33.55,-70.55,-33.35&layer=mapnik&marker=-33.4489,-70.6693",
    ),
    "paris": GeoCard(
        city_name="París",
        admin_region="Île-de-France",
        country="Francia",
        latitude=48.8566,
        longitude=2.3522,
        coordinates_str="48°51′24″N 2°21′08″E",
        population="Aprox. 2.1 millones de habitantes (12.3M área metropolitana)",
        altitude="35 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=48.8566&mlon=2.3522#map=12/48.8566/2.3522",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=2.25,48.80,2.45,48.91&layer=mapnik&marker=48.8566,2.3522",
    ),
    "londres": GeoCard(
        city_name="Londres (London)",
        admin_region="Gran Londres (Greater London)",
        country="Reino Unido",
        latitude=51.5074,
        longitude=-0.1278,
        coordinates_str="51°30′26″N 0°07′39″O",
        population="Aprox. 8.9 millones de habitantes",
        altitude="25 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=51.5074&mlon=-0.1278#map=12/51.5074/-0.1278",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-0.25,51.45,0.00,51.56&layer=mapnik&marker=51.5074,-0.1278",
    ),
    "tokio": GeoCard(
        city_name="Tokio (Tokyo)",
        admin_region="Prefectura de Tokio (Kanto)",
        country="Japón",
        latitude=35.6762,
        longitude=139.6503,
        coordinates_str="35°40′34″N 139°39′01″E",
        population="Aprox. 14.0 millones de habitantes (37.4M Gran Tokio)",
        altitude="40 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=35.6762&mlon=139.6503#map=12/35.6762/139.6503",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=139.55,35.60,139.78,35.75&layer=mapnik&marker=35.6762,139.6503",
    ),
    "roma": GeoCard(
        city_name="Roma",
        admin_region="Lacio (Lazio)",
        country="Italia",
        latitude=41.9028,
        longitude=12.4964,
        coordinates_str="41°54′10″N 12°29′47″E",
        population="Aprox. 2.8 millones de habitantes",
        altitude="21 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=41.9028&mlon=12.4964#map=12/41.9028/12.4964",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=12.38,41.83,12.60,41.97&layer=mapnik&marker=41.9028,12.4964",
    ),
    "berlin": GeoCard(
        city_name="Berlín",
        admin_region="Estado federado de Berlín",
        country="Alemania",
        latitude=52.5200,
        longitude=13.4050,
        coordinates_str="52°31′12″N 13°24′18″E",
        population="Aprox. 3.7 millones de habitantes",
        altitude="34 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=52.5200&mlon=13.4050#map=12/52.5200/13.4050",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=13.25,52.45,13.55,52.58&layer=mapnik&marker=52.5200,13.4050",
    ),
    "nueva_york": GeoCard(
        city_name="Nueva York (New York City)",
        admin_region="Estado de Nueva York",
        country="Estados Unidos",
        latitude=40.7128,
        longitude=-74.0060,
        coordinates_str="40°42′46″N 74°00′22″O",
        population="Aprox. 8.3 millones de habitantes",
        altitude="10 m s. n. m.",
        osm_map_url="https://www.openstreetmap.org/?mlat=40.7128&mlon=-74.0060#map=12/40.7128/-74.0060",
        osm_embed_url="https://www.openstreetmap.org/export/embed.html?bbox=-74.15,40.65,-73.85,40.80&layer=mapnik&marker=40.7128,-74.0060",
    ),
}

GEO_ALIASES: Dict[str, str] = {
    "bogota": "bogota",
    "bogota dc": "bogota",
    "bogota colombia": "bogota",
    "madrid": "madrid",
    "madrid espana": "madrid",
    "buenos aires": "buenos_aires",
    "caba": "buenos_aires",
    "buenos aires argentina": "buenos_aires",
    "cdmx": "ciudad_de_mexico",
    "ciudad de mexico": "ciudad_de_mexico",
    "mexico df": "ciudad_de_mexico",
    "lima": "lima",
    "lima peru": "lima",
    "santiago": "santiago",
    "santiago de chile": "santiago",
    "paris": "paris",
    "paris francia": "paris",
    "londres": "londres",
    "london": "londres",
    "tokio": "tokio",
    "tokyo": "tokio",
    "roma": "roma",
    "roma italia": "roma",
    "berlin": "berlin",
    "nueva york": "nueva_york",
    "new york": "nueva_york",
    "nyc": "nueva_york",
}


def evaluate_geo_query(query: str) -> Optional[GeoCard]:
    """
    Evaluate if query matches a major world city or geographic location.
    Supports alias lookups and typo tolerance.
    Deterministic, offline, zero-tracking.
    """
    clean_q = _norm(query)
    if not clean_q or len(clean_q) < 3:
        return None

    if clean_q in GEO_ALIASES:
        return GLOBAL_CITIES.get(GEO_ALIASES[clean_q])

    for alias, canonical_key in GEO_ALIASES.items():
        if alias == clean_q or f" {alias} " in f" {clean_q} ":
            return GLOBAL_CITIES.get(canonical_key)

    max_d = 1 if len(clean_q) < 7 else 2
    best_match: Optional[str] = None
    best_dist = 999

    for alias, canonical_key in GEO_ALIASES.items():
        if abs(len(alias) - len(clean_q)) <= max_d:
            dist = damerau_levenshtein_distance(clean_q, alias)
            if dist <= max_d and dist < best_dist:
                best_dist = dist
                best_match = canonical_key
                if dist == 1:
                    break

    if best_match:
        return GLOBAL_CITIES.get(best_match)

    return None
