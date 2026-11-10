# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

from senda.worldtime import get_world_time


def test_world_time_cities():
    tokyo = get_world_time("hora en Tokio")
    assert tokyo is not None
    assert "Tokio" in tokyo.display_name
    assert tokyo.timezone_name == "Asia/Tokyo"
    assert tokyo.time_24
    assert tokyo.day_icon in ("☀️", "🌙")

    bogota = get_world_time("que hora es en Bogota")
    assert bogota is not None
    assert "Bogotá" in bogota.display_name
    assert bogota.timezone_name == "America/Bogota"

    madrid = get_world_time("hora actual en Madrid")
    assert madrid is not None
    assert "Madrid" in madrid.display_name
    assert madrid.timezone_name == "Europe/Madrid"

    ny = get_world_time("time in New York")
    assert ny is not None
    assert "Nueva York" in ny.display_name
    assert ny.timezone_name == "America/New_York"


def test_world_time_utc():
    utc = get_world_time("hora utc")
    assert utc is not None
    assert "UTC" in utc.utc_offset


def test_world_time_invalid():
    assert get_world_time("receta de empanadas") is None
    assert get_world_time("") is None
    assert get_world_time("hora en Narnia12345") is None
