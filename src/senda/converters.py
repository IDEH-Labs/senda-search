# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Unit & Currency Converter
Deterministic, zero-telemetry conversion engine for physical units and open exchange rates.
Works 100% server-side with zero JavaScript required.
Compatible with Tor Browser (Safest mode) and GNU LibreJS.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel
import httpx


class ConversionResult(BaseModel):
    """Normalized structured conversion card."""
    from_value: float
    from_unit: str
    to_value: float
    to_unit: str
    formatted_from: str
    formatted_to: str
    category: str  # 'currency', 'length', 'weight', 'temperature', 'speed', 'data'
    formula: Optional[str] = None
    rate_date: Optional[str] = None
    source: str = "Senda Sovereign Engine"
    license: str = "Datos Abiertos (Open Data)"


# Physical units conversion tables (Normalized to SI base units)
LENGTH_UNITS = {
    # Base: meters (m)
    "m": ("m", "metros", 1.0),
    "metro": ("m", "metros", 1.0),
    "metros": ("m", "metros", 1.0),
    "meter": ("m", "metros", 1.0),
    "meters": ("m", "metros", 1.0),
    "km": ("km", "kilómetros", 1000.0),
    "kilometro": ("km", "kilómetros", 1000.0),
    "kilometros": ("km", "kilómetros", 1000.0),
    "kilómetro": ("km", "kilómetros", 1000.0),
    "kilómetros": ("km", "kilómetros", 1000.0),
    "cm": ("cm", "centímetros", 0.01),
    "centimetro": ("cm", "centímetros", 0.01),
    "centímetros": ("cm", "centímetros", 0.01),
    "mm": ("mm", "milímetros", 0.001),
    "milla": ("mi", "millas", 1609.344),
    "millas": ("mi", "millas", 1609.344),
    "mile": ("mi", "millas", 1609.344),
    "miles": ("mi", "millas", 1609.344),
    "pie": ("ft", "pies", 0.3048),
    "pies": ("ft", "pies", 0.3048),
    "ft": ("ft", "pies", 0.3048),
    "foot": ("ft", "pies", 0.3048),
    "feet": ("ft", "pies", 0.3048),
    "pulgada": ("in", "pulgadas", 0.0254),
    "pulgadas": ("in", "pulgadas", 0.0254),
    "in": ("in", "pulgadas", 0.0254),
    "inch": ("in", "pulgadas", 0.0254),
    "inches": ("in", "pulgadas", 0.0254),
    "yarda": ("yd", "yardas", 0.9144),
    "yardas": ("yd", "yardas", 0.9144),
    "yd": ("yd", "yardas", 0.9144),
}

WEIGHT_UNITS = {
    # Base: kilograms (kg)
    "kg": ("kg", "kilogramos", 1.0),
    "kilo": ("kg", "kilogramos", 1.0),
    "kilos": ("kg", "kilogramos", 1.0),
    "kilogramo": ("kg", "kilogramos", 1.0),
    "kilogramos": ("kg", "kilogramos", 1.0),
    "g": ("g", "gramos", 0.001),
    "gramo": ("g", "gramos", 0.001),
    "gramos": ("g", "gramos", 0.001),
    "mg": ("mg", "miligramos", 0.000001),
    "libra": ("lb", "libras", 0.45359237),
    "libras": ("lb", "libras", 0.45359237),
    "lb": ("lb", "libras", 0.45359237),
    "lbs": ("lb", "libras", 0.45359237),
    "onza": ("oz", "onzas", 0.0283495),
    "onzas": ("oz", "onzas", 0.0283495),
    "oz": ("oz", "onzas", 0.0283495),
    "tonelada": ("t", "toneladas", 1000.0),
    "toneladas": ("t", "toneladas", 1000.0),
}

SPEED_UNITS = {
    # Base: km/h
    "km/h": ("km/h", "km/h", 1.0),
    "kmh": ("km/h", "km/h", 1.0),
    "mph": ("mph", "millas/h", 1.609344),
    "m/s": ("m/s", "metros/s", 3.6),
    "nudos": ("kn", "nudos", 1.852),
    "kn": ("kn", "nudos", 1.852),
}

DATA_UNITS = {
    # Base: Megabytes (MB)
    "b": ("B", "Bytes", 1.0 / (1024 * 1024)),
    "bytes": ("B", "Bytes", 1.0 / (1024 * 1024)),
    "kb": ("KB", "Kilobytes", 1.0 / 1024),
    "mb": ("MB", "Megabytes", 1.0),
    "gb": ("GB", "Gigabytes", 1024.0),
    "tb": ("TB", "Terabytes", 1024.0 * 1024.0),
}

# Currency normalization map to ISO 4217 codes
CURRENCIES = {
    "usd": "USD",
    "dolar": "USD",
    "dólar": "USD",
    "dolares": "USD",
    "dólares": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "$": "USD",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "€": "EUR",
    "cop": "COP",
    "peso colombiano": "COP",
    "pesos colombianos": "COP",
    "pesos": "COP",
    "gbp": "GBP",
    "libra esterlina": "GBP",
    "libras esterlinas": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
    "£": "GBP",
    "mxn": "MXN",
    "peso mexicano": "MXN",
    "pesos mexicanos": "MXN",
    "ars": "ARS",
    "peso argentino": "ARS",
    "pesos argentinos": "ARS",
    "clp": "CLP",
    "peso chileno": "CLP",
    "pesos chilenos": "CLP",
    "pen": "PEN",
    "sol": "PEN",
    "soles": "PEN",
    "soles peruanos": "PEN",
    "brl": "BRL",
    "real": "BRL",
    "reales": "BRL",
    "real brasileño": "BRL",
    "jpy": "JPY",
    "yen": "JPY",
    "yenes": "JPY",
    "¥": "JPY",
    "cad": "CAD",
    "dolar canadiense": "CAD",
    "chf": "CHF",
    "franco suizo": "CHF",
    "aud": "AUD",
    "dolar australiano": "AUD",
}

# Verified baseline exchange rates relative to USD (fallback for Tor/offline)
BASELINE_USD_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "COP": 4350.0,
    "GBP": 0.79,
    "MXN": 19.8,
    "ARS": 1050.0,
    "CLP": 960.0,
    "PEN": 3.75,
    "BRL": 5.65,
    "JPY": 152.0,
    "CAD": 1.38,
    "CHF": 0.88,
    "AUD": 1.51,
}

_LIVE_RATES_CACHE: Dict[str, float] = {}
_LAST_RATES_FETCH: float = 0.0


def format_number(val: float) -> str:
    """Format float cleanly with commas and up to 4 significant decimals."""
    if abs(val) >= 1e12 or (0 < abs(val) < 1e-4):
        return f"{val:.4e}"
    if val.is_integer():
        return f"{int(val):,}"
    rounded = round(val, 4)
    if rounded.is_integer():
        return f"{int(rounded):,}"
    # Format with clean decimal representation
    return f"{rounded:,.4f}".rstrip("0").rstrip(".")


def convert_temperature(val: float, from_u: str, to_u: str) -> Optional[ConversionResult]:
    """Convert Celsius, Fahrenheit, Kelvin."""
    from_u = from_u.replace("°", "").strip().lower()
    to_u = to_u.replace("°", "").strip().lower()

    valid_temps = {"c", "celsius", "centigrados", "centígrados", "f", "fahrenheit", "k", "kelvin"}
    if from_u not in valid_temps or to_u not in valid_temps:
        return None

    # Normalize from unit to 'c'
    if from_u in ("c", "celsius", "centigrados", "centígrados"):
        c_val = val
        from_label = "°C (Celsius)"
    elif from_u in ("f", "fahrenheit"):
        c_val = (val - 32.0) * (5.0 / 9.0)
        from_label = "°F (Fahrenheit)"
    elif from_u in ("k", "kelvin"):
        c_val = val - 273.15
        from_label = "K (Kelvin)"
    else:
        return None

    # Convert c_val to target unit
    if to_u in ("c", "celsius", "centigrados", "centígrados"):
        res = c_val
        to_label = "°C (Celsius)"
        formula = "Valor en Celsius"
    elif to_u in ("f", "fahrenheit"):
        res = (c_val * 9.0 / 5.0) + 32.0
        to_label = "°F (Fahrenheit)"
        formula = "(°C × 9/5) + 32"
    elif to_u in ("k", "kelvin"):
        res = c_val + 273.15
        to_label = "K (Kelvin)"
        formula = "°C + 273.15"
    else:
        return None

    return ConversionResult(
        from_value=val,
        from_unit=from_label,
        to_value=res,
        to_unit=to_label,
        formatted_from=f"{format_number(val)} {from_label}",
        formatted_to=f"{format_number(res)} {to_label}",
        category="temperature",
        formula=formula,
    )


async def get_currency_rates() -> Dict[str, float]:
    """Fetch live rates from open ECB/Frankfurter API with 6-hour TTL cache."""
    global _LIVE_RATES_CACHE, _LAST_RATES_FETCH
    now = time.time()
    if _LIVE_RATES_CACHE and (now - _LAST_RATES_FETCH < 21600):
        return _LIVE_RATES_CACHE

    rates = dict(BASELINE_USD_RATES)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("https://api.frankfurter.dev/v1/latest?from=USD")
            if resp.status_code == 200:
                data = resp.json()
                live_rates = data.get("rates", {})
                for k, v in live_rates.items():
                    if isinstance(v, (int, float)):
                        rates[k] = float(v)
    except Exception:
        pass

    _LIVE_RATES_CACHE = rates
    _LAST_RATES_FETCH = now
    return rates


async def convert_query(query: str) -> Optional[ConversionResult]:
    """
    Examine search query for unit or currency conversion intent.
    Deterministic, zero tracking, safe in Tor Browser.
    """
    if not query:
        return None
    raw = query.strip().rstrip("?¿.").strip()
    if len(raw) > 90:
        return None

    # Natural language pattern: [convertir] <val> <unit1> a/en/to/in <unit2>
    pattern = re.compile(
        r"^(?:(?:cu[aá]nto\s+es|convertir|convierte|convert)\s+)?([\d.,]+)\s*([a-zA-Z°$€£¥\/\s]+?)\s+(?:a|en|to|in)\s+([a-zA-Z°$€£¥\/\s]+)$",
        re.IGNORECASE,
    )
    m = pattern.match(raw)
    if not m:
        return None

    val_str, from_raw, to_raw = m.group(1), m.group(2).strip().lower(), m.group(3).strip().lower()
    try:
        val = float(val_str.replace(",", "."))
    except ValueError:
        return None

    # 1. Temperature conversion
    temp_res = convert_temperature(val, from_raw, to_raw)
    if temp_res:
        return temp_res

    # 2. Length conversion
    if from_raw in LENGTH_UNITS and to_raw in LENGTH_UNITS:
        from_sym, from_name, from_base = LENGTH_UNITS[from_raw]
        to_sym, to_name, to_base = LENGTH_UNITS[to_raw]
        meters = val * from_base
        res = meters / to_base
        return ConversionResult(
            from_value=val,
            from_unit=from_name,
            to_value=res,
            to_unit=to_name,
            formatted_from=f"{format_number(val)} {from_sym}",
            formatted_to=f"{format_number(res)} {to_sym}",
            category="length",
            formula=f"1 {from_sym} = {format_number(from_base / to_base)} {to_sym}",
        )

    # 3. Weight conversion
    if from_raw in WEIGHT_UNITS and to_raw in WEIGHT_UNITS:
        from_sym, from_name, from_base = WEIGHT_UNITS[from_raw]
        to_sym, to_name, to_base = WEIGHT_UNITS[to_raw]
        kg = val * from_base
        res = kg / to_base
        return ConversionResult(
            from_value=val,
            from_unit=from_name,
            to_value=res,
            to_unit=to_name,
            formatted_from=f"{format_number(val)} {from_sym}",
            formatted_to=f"{format_number(res)} {to_sym}",
            category="weight",
            formula=f"1 {from_sym} = {format_number(from_base / to_base)} {to_sym}",
        )

    # 4. Speed conversion
    if from_raw in SPEED_UNITS and to_raw in SPEED_UNITS:
        from_sym, from_name, from_base = SPEED_UNITS[from_raw]
        to_sym, to_name, to_base = SPEED_UNITS[to_raw]
        kmh = val * from_base
        res = kmh / to_base
        return ConversionResult(
            from_value=val,
            from_unit=from_name,
            to_value=res,
            to_unit=to_name,
            formatted_from=f"{format_number(val)} {from_sym}",
            formatted_to=f"{format_number(res)} {to_sym}",
            category="speed",
            formula=f"1 {from_sym} = {format_number(from_base / to_base)} {to_sym}",
        )

    # 5. Data conversion
    if from_raw in DATA_UNITS and to_raw in DATA_UNITS:
        from_sym, from_name, from_base = DATA_UNITS[from_raw]
        to_sym, to_name, to_base = DATA_UNITS[to_raw]
        mb = val * from_base
        res = mb / to_base
        return ConversionResult(
            from_value=val,
            from_unit=from_name,
            to_value=res,
            to_unit=to_name,
            formatted_from=f"{format_number(val)} {from_sym}",
            formatted_to=f"{format_number(res)} {to_sym}",
            category="data",
            formula=f"1 {from_sym} = {format_number(from_base / to_base)} {to_sym}",
        )

    # 6. Currency conversion
    curr_from = CURRENCIES.get(from_raw)
    curr_to = CURRENCIES.get(to_raw)
    if curr_from and curr_to:
        rates = await get_currency_rates()
        rate_from = rates.get(curr_from, 1.0)
        rate_to = rates.get(curr_to, 1.0)
        # Convert val in curr_from to USD, then to curr_to
        usd_val = val / rate_from
        res = usd_val * rate_to
        single_rate = rate_to / rate_from
        return ConversionResult(
            from_value=val,
            from_unit=curr_from,
            to_value=res,
            to_unit=curr_to,
            formatted_from=f"{format_number(val)} {curr_from}",
            formatted_to=f"{format_number(res)} {curr_to}",
            category="currency",
            formula=f"1 {curr_from} ≈ {format_number(single_rate)} {curr_to}",
            rate_date=time.strftime("%Y-%m-%d"),
            source="Bancos Centrales & Open Exchange Rates (ECB / Frankfurter)",
            license="Datos Públicos Oficiales (Open Data)",
        )

    return None
