# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Astronomical Engine.
Deterministic, 100% offline, zero-telemetry astronomical calculations.
Calculates real lunar synodic cycles and phases based on standard astronomical algorithms (Jean Meeus / Conway).
No external APIs, no tracking, pure server-side mathematics.
"""

from __future__ import annotations

import datetime
import math
from typing import Optional
from pydantic import BaseModel


# Reference New Moon epoch: 2000-01-06 18:14:00 UTC (Astronomical Julian Day 2451549.26)
_EPOCH_NEW_MOON = datetime.datetime(2000, 1, 6, 18, 14, 0, tzinfo=datetime.timezone.utc)

# Mean Synodic Month (period between successive new moons in standard solar days)
_SYNODIC_MONTH = 29.53058770576


class MoonPhaseInfo(BaseModel):
    """Structured verifiable lunar phase information."""
    code: str
    name: str
    age_days: float
    fraction: float
    illumination_pct: int
    svg_icon: str


PHASE_DEFINITIONS = (
    ("new_moon", "Luna nueva", "moon_new"),
    ("waxing_crescent", "Luna creciente", "moon_waxing_crescent"),
    ("first_quarter", "Cuarto creciente", "moon_first_quarter"),
    ("waxing_gibbous", "Luna gibosa creciente", "moon_waxing_gibbous"),
    ("full_moon", "Luna llena", "moon_full"),
    ("waning_gibbous", "Luna gibosa menguante", "moon_waning_gibbous"),
    ("last_quarter", "Cuarto menguante", "moon_last_quarter"),
    ("waning_crescent", "Luna menguante", "moon_waning_crescent"),
)


def calculate_moon_phase(dt: Optional[datetime.datetime] = None) -> MoonPhaseInfo:
    """
    Calculate the real astronomical lunar phase for a given datetime.
    Deterministic, offline, zero-telemetry.
    """
    if dt is None:
        dt = datetime.datetime.now(datetime.timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    utc_dt = dt.astimezone(datetime.timezone.utc)
    diff_days = (utc_dt - _EPOCH_NEW_MOON).total_seconds() / 86400.0
    age = diff_days % _SYNODIC_MONTH
    fraction = age / _SYNODIC_MONTH  # 0.0 to 1.0

    # 8 bins of width 0.125, centered on 0.0 (new moon), 0.125, 0.25, etc.
    phase_idx = int((fraction + 0.0625) % 1.0 / 0.125)
    code, name, svg_icon = PHASE_DEFINITIONS[phase_idx]

    # Illumination fraction (0.0 to 1.0) via spherical geometry approximation
    illumination = 0.5 * (1.0 - math.cos(fraction * 2.0 * math.pi))
    illumination_pct = int(round(illumination * 100))

    return MoonPhaseInfo(
        code=code,
        name=name,
        age_days=round(age, 1),
        fraction=round(fraction, 4),
        illumination_pct=illumination_pct,
        svg_icon=svg_icon,
    )
