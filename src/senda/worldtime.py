# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign World Time Engine
Deterministic, zero-telemetry world clock based on standard IANA Time Zones.
Works 100% server-side with zero JavaScript required.
Compatible with Tor Browser (Safest mode) and GNU LibreJS.
"""

from __future__ import annotations

import datetime
import re
from typing import Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel


class WorldTimeResult(BaseModel):
    """Normalized structured world time card."""
    query_location: str
    display_name: str
    time_24: str
    time_12: str
    date_formatted: str
    timezone_name: str
    timezone_abbr: str
    utc_offset: str
    is_day: bool
    day_icon: str
    icon_type: str = "sun"
    time_period: str = "Día"
    utc_diff_text: str
    source: str = "Senda Sovereign Engine (Base de Datos IANA)"


# Curated dictionary of common cities, capitals, countries and timezone acronyms
WORLD_TIMEZONES = {
    # Colombia & Latin America
    "bogota": ("Bogotá, Colombia", "America/Bogota"),
    "bogotá": ("Bogotá, Colombia", "America/Bogota"),
    "medellin": ("Medellín, Colombia", "America/Bogota"),
    "medellín": ("Medellín, Colombia", "America/Bogota"),
    "cali": ("Cali, Colombia", "America/Bogota"),
    "barranquilla": ("Barranquilla, Colombia", "America/Bogota"),
    "cartagena": ("Cartagena, Colombia", "America/Bogota"),
    "bucaramanga": ("Bucaramanga, Colombia", "America/Bogota"),
    "colombia": ("Colombia", "America/Bogota"),
    "buenos aires": ("Buenos Aires, Argentina", "America/Argentina/Buenos_Aires"),
    "argentina": ("Argentina", "America/Argentina/Buenos_Aires"),
    "santiago": ("Santiago, Chile", "America/Santiago"),
    "chile": ("Santiago, Chile", "America/Santiago"),
    "lima": ("Lima, Perú", "America/Lima"),
    "peru": ("Lima, Perú", "America/Lima"),
    "perú": ("Lima, Perú", "America/Lima"),
    "quito": ("Quito, Ecuador", "America/Guayaquil"),
    "guayaquil": ("Guayaquil, Ecuador", "America/Guayaquil"),
    "ecuador": ("Ecuador", "America/Guayaquil"),
    "caracas": ("Caracas, Venezuela", "America/Caracas"),
    "venezuela": ("Caracas, Venezuela", "America/Caracas"),
    "la paz": ("La Paz, Bolivia", "America/La_Paz"),
    "bolivia": ("La Paz, Bolivia", "America/La_Paz"),
    "montevideo": ("Montevideo, Uruguay", "America/Montevideo"),
    "uruguay": ("Montevideo, Uruguay", "America/Montevideo"),
    "asuncion": ("Asunción, Paraguay", "America/Asuncion"),
    "asunción": ("Asunción, Paraguay", "America/Asuncion"),
    "paraguay": ("Asunción, Paraguay", "America/Asuncion"),
    "mexico": ("Ciudad de México, México", "America/Mexico_City"),
    "méxico": ("Ciudad de México, México", "America/Mexico_City"),
    "cdmx": ("Ciudad de México, México", "America/Mexico_City"),
    "ciudad de mexico": ("Ciudad de México, México", "America/Mexico_City"),
    "ciudad de méxico": ("Ciudad de México, México", "America/Mexico_City"),
    "guadalajara": ("Guadalajara, México", "America/Mexico_City"),
    "monterrey": ("Monterrey, México", "America/Monterrey"),
    "cancun": ("Cancún, México", "America/Cancun"),
    "cancún": ("Cancún, México", "America/Cancun"),
    "tijuana": ("Tijuana, México", "America/Tijuana"),
    "sao paulo": ("São Paulo, Brasil", "America/Sao_Paulo"),
    "são paulo": ("São Paulo, Brasil", "America/Sao_Paulo"),
    "rio de janeiro": ("Río de Janeiro, Brasil", "America/Sao_Paulo"),
    "brasilia": ("Brasilia, Brasil", "America/Sao_Paulo"),
    "brasil": ("Brasilia, Brasil", "America/Sao_Paulo"),
    "brazil": ("Brasilia, Brasil", "America/Sao_Paulo"),
    "panama": ("Panamá", "America/Panama"),
    "panamá": ("Panamá", "America/Panama"),
    "san jose": ("San José, Costa Rica", "America/Costa_Rica"),
    "san josé": ("San José, Costa Rica", "America/Costa_Rica"),
    "costa rica": ("Costa Rica", "America/Costa_Rica"),
    "guatemala": ("Guatemala", "America/Guatemala"),
    "san salvador": ("San Salvador, El Salvador", "America/El_Salvador"),
    "tegucigalpa": ("Tegucigalpa, Honduras", "America/Tegucigalpa"),
    "managua": ("Managua, Nicaragua", "America/Managua"),
    "la habana": ("La Habana, Cuba", "America/Havana"),
    "cuba": ("Cuba", "America/Havana"),
    "santo domingo": ("Santo Domingo, Rep. Dominicana", "America/Santo_Domingo"),
    "san juan": ("San Juan, Puerto Rico", "America/Puerto_Rico"),
    "puerto rico": ("San Juan, Puerto Rico", "America/Puerto_Rico"),

    # Spain & Europe
    "madrid": ("Madrid, España", "Europe/Madrid"),
    "barcelona": ("Barcelona, España", "Europe/Madrid"),
    "valencia": ("Valencia, España", "Europe/Madrid"),
    "sevilla": ("Sevilla, España", "Europe/Madrid"),
    "bilbao": ("Bilbao, España", "Europe/Madrid"),
    "espana": ("España (Península)", "Europe/Madrid"),
    "españa": ("España (Península)", "Europe/Madrid"),
    "canarias": ("Islas Canarias, España", "Atlantic/Canary"),
    "londres": ("Londres, Reino Unido", "Europe/London"),
    "london": ("Londres, Reino Unido", "Europe/London"),
    "reino unido": ("Reino Unido", "Europe/London"),
    "uk": ("Reino Unido", "Europe/London"),
    "paris": ("París, Francia", "Europe/Paris"),
    "parís": ("París, Francia", "Europe/Paris"),
    "francia": ("Francia", "Europe/Paris"),
    "france": ("Francia", "Europe/Paris"),
    "berlin": ("Berlín, Alemania", "Europe/Berlin"),
    "berlín": ("Berlín, Alemania", "Europe/Berlin"),
    "alemania": ("Alemania", "Europe/Berlin"),
    "germany": ("Alemania", "Europe/Berlin"),
    "roma": ("Roma, Italia", "Europe/Rome"),
    "rome": ("Roma, Italia", "Europe/Rome"),
    "italia": ("Italia", "Europe/Rome"),
    "italy": ("Italia", "Europe/Rome"),
    "amsterdam": ("Ámsterdam, Países Bajos", "Europe/Amsterdam"),
    "ámsterdam": ("Ámsterdam, Países Bajos", "Europe/Amsterdam"),
    "paises bajos": ("Países Bajos", "Europe/Amsterdam"),
    "lisboa": ("Lisboa, Portugal", "Europe/Lisbon"),
    "portugal": ("Portugal", "Europe/Lisbon"),
    "bruselas": ("Bruselas, Bélgica", "Europe/Brussels"),
    "belgica": ("Bélgica", "Europe/Brussels"),
    "suiza": ("Suiza", "Europe/Zurich"),
    "zurich": ("Zúrich, Suiza", "Europe/Zurich"),
    "ginebra": ("Ginebra, Suiza", "Europe/Zurich"),
    "viena": ("Viena, Austria", "Europe/Vienna"),
    "austria": ("Austria", "Europe/Vienna"),
    "estocolmo": ("Estocolmo, Suecia", "Europe/Stockholm"),
    "suecia": ("Suecia", "Europe/Stockholm"),
    "oslo": ("Oslo, Noruega", "Europe/Oslo"),
    "noruega": ("Noruega", "Europe/Oslo"),
    "copenhague": ("Copenhague, Dinamarca", "Europe/Copenhagen"),
    "helsinki": ("Helsinki, Finlandia", "Europe/Helsinki"),
    "atenas": ("Atenas, Grecia", "Europe/Athens"),
    "grecia": ("Grecia", "Europe/Athens"),
    "moscu": ("Moscú, Rusia", "Europe/Moscow"),
    "moscú": ("Moscú, Rusia", "Europe/Moscow"),
    "rusia": ("Moscú, Rusia", "Europe/Moscow"),
    "kiev": ("Kiev, Ucrania", "Europe/Kyiv"),
    "varsovia": ("Varsovia, Polonia", "Europe/Warsaw"),
    "polonia": ("Polonia", "Europe/Warsaw"),
    "dublin": ("Dublín, Irlanda", "Europe/Dublin"),
    "dublín": ("Dublín, Irlanda", "Europe/Dublin"),
    "irlanda": ("Irlanda", "Europe/Dublin"),

    # North America
    "nueva york": ("Nueva York, EE. UU.", "America/New_York"),
    "new york": ("Nueva York, EE. UU.", "America/New_York"),
    "nyc": ("Nueva York, EE. UU.", "America/New_York"),
    "washington": ("Washington D.C., EE. UU.", "America/New_York"),
    "miami": ("Miami, Florida, EE. UU.", "America/New_York"),
    "boston": ("Boston, EE. UU.", "America/New_York"),
    "chicago": ("Chicago, Illinois, EE. UU.", "America/Chicago"),
    "los angeles": ("Los Ángeles, California, EE. UU.", "America/Los_Angeles"),
    "los ángeles": ("Los Ángeles, California, EE. UU.", "America/Los_Angeles"),
    "la": ("Los Ángeles, California, EE. UU.", "America/Los_Angeles"),
    "san francisco": ("San Francisco, California, EE. UU.", "America/Los_Angeles"),
    "seattle": ("Seattle, Washington, EE. UU.", "America/Los_Angeles"),
    "dallas": ("Dallas, Texas, EE. UU.", "America/Chicago"),
    "houston": ("Houston, Texas, EE. UU.", "America/Chicago"),
    "denver": ("Denver, Colorado, EE. UU.", "America/Denver"),
    "las vegas": ("Las Vegas, Nevada, EE. UU.", "America/Los_Angeles"),
    "honolulu": ("Honolulu, Hawái, EE. UU.", "Pacific/Honolulu"),
    "hawai": ("Hawái, EE. UU.", "Pacific/Honolulu"),
    "hawái": ("Hawái, EE. UU.", "Pacific/Honolulu"),
    "toronto": ("Toronto, Canadá", "America/Toronto"),
    "montreal": ("Montreal, Canadá", "America/Toronto"),
    "vancouver": ("Vancouver, Canadá", "America/Vancouver"),
    "canada": ("Canadá (Este)", "America/Toronto"),
    "canadá": ("Canadá (Este)", "America/Toronto"),

    # Asia & Middle East
    "tokio": ("Tokio, Japón", "Asia/Tokyo"),
    "tokyo": ("Tokio, Japón", "Asia/Tokyo"),
    "japon": ("Japón", "Asia/Tokyo"),
    "japón": ("Japón", "Asia/Tokyo"),
    "seul": ("Seúl, Corea del Sur", "Asia/Seoul"),
    "seúl": ("Seúl, Corea del Sur", "Asia/Seoul"),
    "corea": ("Corea del Sur", "Asia/Seoul"),
    "corea del sur": ("Corea del Sur", "Asia/Seoul"),
    "pekin": ("Pekín, China", "Asia/Shanghai"),
    "pekín": ("Pekín, China", "Asia/Shanghai"),
    "beijing": ("Pekín, China", "Asia/Shanghai"),
    "shanghai": ("Shanghái, China", "Asia/Shanghai"),
    "shanghái": ("Shanghái, China", "Asia/Shanghai"),
    "china": ("China", "Asia/Shanghai"),
    "hong kong": ("Hong Kong", "Asia/Hong_Kong"),
    "taiwan": ("Taiwán", "Asia/Taipei"),
    "taiwán": ("Taiwán", "Asia/Taipei"),
    "singapur": ("Singapur", "Asia/Singapore"),
    "singapore": ("Singapur", "Asia/Singapore"),
    "bangkok": ("Bangkok, Tailandia", "Asia/Bangkok"),
    "tailandia": ("Tailandia", "Asia/Bangkok"),
    "nueva delhi": ("Nueva Delhi, India", "Asia/Kolkata"),
    "new delhi": ("Nueva Delhi, India", "Asia/Kolkata"),
    "india": ("India", "Asia/Kolkata"),
    "dubai": ("Dubái, EAU", "Asia/Dubai"),
    "dubái": ("Dubái, EAU", "Asia/Dubai"),
    "doha": ("Doha, Catar", "Asia/Qatar"),
    "estambul": ("Estambul, Turquía", "Europe/Istanbul"),
    "turquia": ("Turquía", "Europe/Istanbul"),
    "turquía": ("Turquía", "Europe/Istanbul"),
    "jerusalen": ("Jerusalén, Israel", "Asia/Jerusalem"),
    "jerusalén": ("Jerusalén, Israel", "Asia/Jerusalem"),
    "tel aviv": ("Tel Aviv, Israel", "Asia/Jerusalem"),
    "riyadh": ("Riad, Arabia Saudita", "Asia/Riyadh"),
    "riad": ("Riad, Arabia Saudita", "Asia/Riyadh"),

    # Oceania & Africa
    "sidney": ("Sídney, Australia", "Australia/Sydney"),
    "sídney": ("Sídney, Australia", "Australia/Sydney"),
    "sydney": ("Sídney, Australia", "Australia/Sydney"),
    "melbourne": ("Melbourne, Australia", "Australia/Melbourne"),
    "brisbane": ("Brisbane, Australia", "Australia/Brisbane"),
    "australia": ("Sídney, Australia", "Australia/Sydney"),
    "auckland": ("Auckland, Nueva Zelanda", "Pacific/Auckland"),
    "nueva zelanda": ("Nueva Zelanda", "Pacific/Auckland"),
    "el cairo": ("El Cairo, Egipto", "Africa/Cairo"),
    "cairo": ("El Cairo, Egipto", "Africa/Cairo"),
    "egipto": ("Egipto", "Africa/Cairo"),
    "johanesburgo": ("Johannesburgo, Sudáfrica", "Africa/Johannesburg"),
    "sudafrica": ("Sudáfrica", "Africa/Johannesburg"),
    "sudáfrica": ("Sudáfrica", "Africa/Johannesburg"),
    "nairobi": ("Nairobi, Kenia", "Africa/Nairobi"),
    "casablanca": ("Casablanca, Marruecos", "Africa/Casablanca"),
    "marruecos": ("Marruecos", "Africa/Casablanca"),

    # Direct Timezone Acronyms
    "utc": ("Tiempo Universal Coordinado (UTC)", "UTC"),
    "gmt": ("Greenwich Mean Time (GMT)", "GMT"),
}

SPANISH_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
SPANISH_MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def format_spanish_date(dt: datetime.datetime) -> str:
    """Format datetime into friendly Spanish text."""
    day_name = SPANISH_DAYS[dt.weekday()]
    month_name = SPANISH_MONTHS[dt.month - 1]
    return f"{day_name}, {dt.day} de {month_name} de {dt.year}"


def get_world_time(query: str) -> Optional[WorldTimeResult]:
    """
    Examine search query for time intent in a given city or timezone.
    Deterministic, instant, zero tracking.
    """
    if not query:
        return None
    raw = query.strip().rstrip("?¿.").strip()
    if len(raw) > 70:
        return None

    # Matching patterns:
    # 1. "hora en Tokio", "hora de Quito", "que hora es en Bogota", "hora actual en Madrid"
    # 2. "time in Tokyo", "current time in London", "time London"
    # 3. "hora Tokio", "hora UTC"
    pattern = re.compile(
        r"^(?:(?:qu[eé]\s+hora\s+es(?:\s+(?:en|de))?|hora\s+actual(?:\s+(?:en|de))?|hora(?:\s+(?:en|de))?|current\s+time\s+(?:in|for|of)?|time\s+(?:in|for|of)?|time)\s+)?(.+)$",
        re.IGNORECASE,
    )
    m = pattern.match(raw)
    if not m:
        return None

    target = m.group(1).strip().lower()

    # Avoid capturing generic search terms that happen to start with nothing or look like calculations
    is_time_explicit = bool(re.search(r"\b(hora|time)\b", raw, re.IGNORECASE))
    if not is_time_explicit and target not in ("utc", "gmt"):
        return None

    # Strip leading prepositions if any were left in target
    target = re.sub(r"^(?:en|de|in|of|for)\s+", "", target).strip()

    # Clean target of trailing words like "hoy", "ahora", "today", "now"
    target = re.sub(r"\b(hoy|ahora|today|now)\b", "", target).strip().rstrip("?¿.").strip()

    if not target:
        return None

    # Lookup in WORLD_TIMEZONES
    tz_info_match = WORLD_TIMEZONES.get(target)
    if not tz_info_match:
        # Try checking if target ends with one of the keys or vice versa
        for k, v in WORLD_TIMEZONES.items():
            if target == k or target.endswith(f" {k}") or target.startswith(f"{k} "):
                tz_info_match = v
                break

    if not tz_info_match:
        return None

    display_name, tz_identifier = tz_info_match
    try:
        tz = ZoneInfo(tz_identifier)
        now_tz = datetime.datetime.now(tz)
    except Exception:
        return None

    time_24 = now_tz.strftime("%H:%M")
    time_12 = now_tz.strftime("%I:%M %p").lstrip("0")
    date_formatted = format_spanish_date(now_tz)

    tz_abbr = now_tz.strftime("%Z")
    offset = now_tz.strftime("%z")
    # Format offset from +0900 to UTC+09:00
    if offset:
        sign = offset[0]
        hours = offset[1:3]
        mins = offset[3:5]
        if mins == "00":
            utc_offset = f"UTC{sign}{int(hours)}"
        else:
            utc_offset = f"UTC{sign}{int(hours)}:{mins}"
    else:
        utc_offset = "UTC"

    # Discern the 4 periods of the day: Madrugada, Mañana, Tarde, Noche
    hour = now_tz.hour
    if 0 <= hour < 6:
        time_period = "Madrugada"
        is_day = False
        icon_type = "moon"
    elif 6 <= hour < 12:
        time_period = "Mañana"
        is_day = True
        icon_type = "sun"
    elif 12 <= hour < 19:
        time_period = "Tarde"
        is_day = True
        icon_type = "sun"
    else:  # 19 <= hour < 24
        time_period = "Noche"
        is_day = False
        icon_type = "moon"

    day_icon = "☀️" if is_day else "🌙"

    # Calculate difference relative to UTC
    offset_seconds = now_tz.utcoffset().total_seconds() if now_tz.utcoffset() else 0
    offset_hours = offset_seconds / 3600.0
    if offset_hours == 0:
        utc_diff_text = "Mismo huso horario que UTC"
    elif offset_hours > 0:
        utc_diff_text = f"{offset_hours:g} h por delante de UTC"
    else:
        utc_diff_text = f"{abs(offset_hours):g} h por detrás de UTC"

    return WorldTimeResult(
        query_location=target,
        display_name=display_name,
        time_24=time_24,
        time_12=time_12,
        date_formatted=date_formatted,
        timezone_name=tz_identifier,
        timezone_abbr=tz_abbr,
        utc_offset=utc_offset,
        is_day=is_day,
        day_icon=day_icon,
        icon_type=icon_type,
        time_period=time_period,
        utc_diff_text=utc_diff_text,
    )
