# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import pytest
from senda.converters import convert_query


@pytest.mark.asyncio
async def test_convert_length():
    res = await convert_query("10 km a metros")
    assert res is not None
    assert res.category == "length"
    assert res.to_value == 10000.0
    assert "10,000" in res.formatted_to or "10000" in res.formatted_to or "10.000" in res.formatted_to

    res2 = await convert_query("5 millas a km")
    assert res2 is not None
    assert round(res2.to_value, 2) == 8.05


@pytest.mark.asyncio
async def test_convert_weight():
    res = await convert_query("2.5 kg a libras")
    assert res is not None
    assert res.category == "weight"
    assert round(res.to_value, 2) == 5.51

    res2 = await convert_query("100 gramos en oz")
    assert res2 is not None
    assert round(res2.to_value, 2) == 3.53


@pytest.mark.asyncio
async def test_convert_temperature():
    res = await convert_query("100 c a fahrenheit")
    assert res is not None
    assert res.category == "temperature"
    assert res.to_value == 212.0

    res2 = await convert_query("32 f a c")
    assert res2 is not None
    assert res2.to_value == 0.0

    res3 = await convert_query("0 c a kelvin")
    assert res3 is not None
    assert res3.to_value == 273.15


@pytest.mark.asyncio
async def test_convert_speed_and_data():
    res = await convert_query("120 km/h a mph")
    assert res is not None
    assert res.category == "speed"
    assert round(res.to_value, 2) == 74.56

    res2 = await convert_query("1024 mb a gb")
    assert res2 is not None
    assert res2.category == "data"
    assert res2.to_value == 1.0


@pytest.mark.asyncio
async def test_convert_currency():
    res = await convert_query("100 usd a eur")
    assert res is not None
    assert res.category == "currency"
    assert res.to_value > 0

    res2 = await convert_query("cuanto es 50 eur en cop")
    assert res2 is not None
    assert res2.category == "currency"
    assert res2.to_value > 100000


@pytest.mark.asyncio
async def test_convert_invalid_queries():
    assert await convert_query("not a conversion") is None
    assert await convert_query("") is None
    assert await convert_query("10 patatas a zanahorias") is None
