# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Real-Time Weather Provider
Open-Data weather engine powered by Open-Meteo (GNU AGPL v3.0).
Provides real-time forecasts, temperatures, and conditions worldwide with:
- Zero API keys
- Zero user tracking, zero cookie persistence
- In-memory TTL caching to avoid redundant calls
- 100% Free Culture & Open Public Meteorological Data (DWD, NOAA, ECMWF)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field


# World Meteorological Organization (WMO) Weather Interpretation Codes (WW)
WMO_CODES: Dict[int, tuple[str, str, str]] = {
    0: ("Cielo despejado", "☀️", "🌙"),
    1: ("Mayormente despejado", "🌤️", "☁️🌙"),
    2: ("Parcialmente nublado", "⛅", "☁️🌙"),
    3: ("Nublado", "☁️", "☁️"),
    45: ("Niebla", "🌫️", "🌫️"),
    48: ("Niebla con escarcha", "🌫️", "🌫️"),
    51: ("Llovizna ligera", "🌦️", "🌧️"),
    53: ("Llovizna moderada", "🌦️", "🌧️"),
    55: ("Llovizna densa", "🌧️", "🌧️"),
    56: ("Llovizna helada leve", "🌧️❄️", "🌧️❄️"),
    57: ("Llovizna helada densa", "🌧️❄️", "🌧️❄️"),
    61: ("Lluvia ligera", "🌧️", "🌧️"),
    63: ("Lluvia moderada", "🌧️", "🌧️"),
    65: ("Lluvia fuerte", "🌧️", "🌧️"),
    66: ("Lluvia helada leve", "🌧️❄️", "🌧️❄️"),
    67: ("Lluvia helada fuerte", "🌧️❄️", "🌧️❄️"),
    71: ("Nieve ligera", "🌨️", "🌨️"),
    73: ("Nieve moderada", "🌨️", "🌨️"),
    75: ("Nieve intensa", "🌨️", "🌨️"),
    77: ("Granizo fino", "🌨️", "🌨️"),
    80: ("Chubascos ligeros", "🌦️", "🌧️"),
    81: ("Chubascos moderados", "🌧️", "🌧️"),
    82: ("Chubascos violentos", "🌧️", "🌧️"),
    85: ("Chubascos de nieve leves", "🌨️", "🌨️"),
    86: ("Chubascos de nieve fuertes", "🌨️", "🌨️"),
    95: ("Tormenta eléctrica", "⛈️", "⛈️"),
    96: ("Tormenta con granizo leve", "⛈️", "⛈️"),
    99: ("Tormenta con granizo fuerte", "⛈️", "⛈️"),
}

SPANISH_DAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


class DailyForecastItem(BaseModel):
    """Forecast for a single upcoming day."""
    date: str
    day_name: str
    temp_max: int
    temp_min: int
    icon: str
    description: str


class WeatherCard(BaseModel):
    """Normalized real-time weather card."""
    city_name: str
    country: str
    admin1: Optional[str] = None
    temperature: float
    apparent_temperature: float
    humidity: int
    wind_speed: float
    precipitation: float
    weather_code: int
    weather_description: str
    weather_icon: str
    icon_type: str = "sun"
    time_period: str = "Día"
    is_day: bool = True
    daily_forecast: List[DailyForecastItem] = Field(default_factory=list)
    source: str = "Open-Meteo & Modelos Meteorológicos Abiertos (DWD, NOAA, ECMWF)"
    license: str = "Datos Abiertos (CC BY 4.0)"
    updated_at: str


class WeatherProvider:
    """Async provider fetching geocoding and real-time forecast."""

    WEATHER_PATTERNS = [
        r"^(?:el\s+)?(?:clima|tiempo|temperatura|pron[oó]stico|weather|forecast)(?:\s+(?:en|de|para|in|for))?\s+([^?]+)",
        r"^(?:c[oó]mo\s+est[aá]\s+el\s+(?:clima|tiempo)\s+(?:en|de)\s+)([^?]+)",
        r"^qu[eé]\s+(?:clima|tiempo)\s+hace\s+en\s+([^?]+)",
        r"(.+?)\s+(?:clima|tiempo|temperatura|pron[oó]stico|weather|forecast)[?]?$",
    ]

    def __init__(self, ttl_seconds: int = 900):
        self.ttl = ttl_seconds
        self._cache: Dict[str, tuple[float, Optional[WeatherCard]]] = {}
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=5.0,
                headers={"User-Agent": "SendaSearch/0.2.0 (https://senda.ideh.top; ethical-search)"},
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def detect_city(self, query: str) -> Optional[tuple[str, bool]]:
        """
        Extract city from query.
        Returns (city_candidate, is_explicit_weather_query).
        """
        if not query:
            return None
        clean = query.strip().rstrip("?¿.").strip()
        if len(clean) < 2 or len(clean) > 80:
            return None

        # Check explicit weather phrases first
        for pat in self.WEATHER_PATTERNS:
            m = re.match(pat, clean, re.IGNORECASE)
            if m:
                city = m.group(1).strip()
                if len(city) >= 2:
                    return (city, True)

        # Disallow queries with search operators or URLs
        if any(token in clean for token in (":", "/", "http", "www.", "-", "+", "!", '"')):
            return None

        # If it's a short 1-3 word query, it could be a direct city name (e.g. "Bogotá", "Madrid")
        words = clean.split()
        if 1 <= len(words) <= 3:
            return (clean, False)

        return None

    async def get_weather(self, query: str) -> Optional[WeatherCard]:
        """Fetch real-time weather if query refers to a city."""
        detected = self.detect_city(query)
        if not detected:
            return None

        city_query, is_explicit = detected
        cache_key = city_query.lower()

        now = time.time()
        if cache_key in self._cache:
            ts, cached_card = self._cache[cache_key]
            if now - ts < self.ttl:
                return cached_card

        client = await self._get_client()

        # 1. Geocode city name via Open-Meteo
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city_query)}&count=3&language=es&format=json"
        try:
            r_geo = await client.get(geo_url)
            if r_geo.status_code != 200:
                self._cache[cache_key] = (now, None)
                return None
            geo_data = r_geo.json()
            results = geo_data.get("results")
            if not results:
                self._cache[cache_key] = (now, None)
                return None

            # Choose the best matching location
            best = None
            for cand in results:
                feature = cand.get("feature_code", "")
                pop = cand.get("population", 0) or 0
                # If explicit weather query, accept any populated place
                if is_explicit:
                    best = cand
                    break
                # If query was just a single word (e.g. "Bogota"), require it to be a city with significant population
                if feature.startswith("PPL") and pop >= 40000:
                    best = cand
                    break
                # Also accept capital / administrative seats
                if feature in ("PPLC", "PPLA", "PPLA2"):
                    best = cand
                    break

            if not best:
                self._cache[cache_key] = (now, None)
                return None

            lat = best["latitude"]
            lon = best["longitude"]
            city_name = best.get("name", city_query.title())
            country = best.get("country", "")
            admin1 = best.get("admin1")

            # Harmonize Colombian administrative geography and avoid redundant names
            if city_name.lower() in ("bogotá", "bogota") and country.lower() == "colombia":
                admin1 = "Cundinamarca · Distrito Capital"
            elif admin1 and admin1.lower() == city_name.lower():
                admin1 = None

            # 2. Fetch current weather and 4-day forecast
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto"
            )
            r_w = await client.get(weather_url)
            if r_w.status_code != 200:
                self._cache[cache_key] = (now, None)
                return None

            w_data = r_w.json()
            curr = w_data.get("current", {})
            daily = w_data.get("daily", {})

            temp = round(curr.get("temperature_2m", 0.0), 1)
            app_temp = round(curr.get("apparent_temperature", temp), 1)
            humidity = int(curr.get("relative_humidity_2m", 0))
            wind = round(curr.get("wind_speed_10m", 0.0), 1)
            precip = round(curr.get("precipitation", 0.0), 1)
            code = int(curr.get("weather_code", 0))
            is_day = bool(curr.get("is_day", 1))

            desc, day_ico, night_ico = WMO_CODES.get(code, ("Condiciones variables", "⛅", "⛅"))
            icon = day_ico if is_day else night_ico

            # Calculate local hour from Open-Meteo local time (auto timezone)
            local_time_raw = curr.get("time", "")
            local_hour = 12
            if local_time_raw and "T" in local_time_raw:
                try:
                    time_part = local_time_raw.split("T")[1]
                    local_hour = int(time_part.split(":")[0])
                except Exception:
                    pass

            # Discern the 4 periods of the day: Madrugada, Mañana, Tarde, Noche
            if 0 <= local_hour < 6:
                time_period = "Madrugada"
            elif 6 <= local_hour < 12:
                time_period = "Mañana"
            elif 12 <= local_hour < 19:
                time_period = "Tarde"
            else:
                time_period = "Noche"

            # Determine vector icon type for rendering
            if is_day:
                if code == 0:
                    icon_type = "sun"
                elif code in (1, 2):
                    icon_type = "cloud_sun"
                elif code == 3:
                    icon_type = "cloud"
                elif code in (45, 48):
                    icon_type = "fog"
                elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
                    icon_type = "rain"
                elif code in (71, 73, 75, 77, 85, 86):
                    icon_type = "snow"
                elif code in (95, 96, 99):
                    icon_type = "thunderstorm"
                else:
                    icon_type = "cloud"
            else:
                if code == 0:
                    icon_type = "moon"
                elif code in (1, 2):
                    icon_type = "cloud_moon"
                elif code == 3:
                    icon_type = "cloud"
                elif code in (45, 48):
                    icon_type = "fog"
                elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
                    icon_type = "rain"
                elif code in (71, 73, 75, 77, 85, 86):
                    icon_type = "snow"
                elif code in (95, 96, 99):
                    icon_type = "thunderstorm"
                else:
                    icon_type = "moon"

            # Build daily forecast (next 4 days)
            daily_items: List[DailyForecastItem] = []
            dates = daily.get("time", [])
            codes = daily.get("weather_code", [])
            maxs = daily.get("temperature_2m_max", [])
            mins = daily.get("temperature_2m_min", [])

            for i in range(min(4, len(dates))):
                d_str = dates[i]
                try:
                    dt = datetime.strptime(d_str, "%Y-%m-%d")
                    day_label = "Hoy" if i == 0 else SPANISH_DAYS[dt.weekday()]
                except Exception:
                    day_label = d_str

                d_code = int(codes[i]) if i < len(codes) else 0
                d_desc, d_ico, _ = WMO_CODES.get(d_code, ("Variable", "⛅", "⛅"))
                d_max = round(maxs[i]) if i < len(maxs) else 0
                d_min = round(mins[i]) if i < len(mins) else 0

                daily_items.append(
                    DailyForecastItem(
                        date=d_str,
                        day_name=day_label,
                        temp_max=d_max,
                        temp_min=d_min,
                        icon=d_ico,
                        description=d_desc,
                    )
                )

            time_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

            card = WeatherCard(
                city_name=city_name,
                country=country,
                admin1=admin1,
                temperature=temp,
                apparent_temperature=app_temp,
                humidity=humidity,
                wind_speed=wind,
                precipitation=precip,
                weather_code=code,
                weather_description=desc,
                weather_icon=icon,
                icon_type=icon_type,
                time_period=time_period,
                is_day=is_day,
                daily_forecast=daily_items,
                updated_at=time_str,
            )

            self._cache[cache_key] = (now, card)
            return card

        except Exception:
            self._cache[cache_key] = (now, None)
            return None
