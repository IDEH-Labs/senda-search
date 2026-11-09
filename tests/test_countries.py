# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Tests for Worldwide Country Catalog and Regional Localization."""

from senda.countries import (
    COUNTRY_CATALOG,
    COUNTRY_BY_CODE,
    get_country_name,
    get_countries_grouped,
)


def test_country_catalog_integrity():
    """Verify that COUNTRY_CATALOG covers worldwide countries across all continents."""
    assert len(COUNTRY_CATALOG) >= 120
    assert "all" in COUNTRY_BY_CODE
    assert "es" in COUNTRY_BY_CODE
    assert "co" in COUNTRY_BY_CODE
    assert "mx" in COUNTRY_BY_CODE
    assert "jp" in COUNTRY_BY_CODE
    assert "de" in COUNTRY_BY_CODE
    assert "za" in COUNTRY_BY_CODE
    assert "au" in COUNTRY_BY_CODE


def test_get_country_name():
    """Verify friendly Spanish display names for country codes."""
    assert get_country_name("all") == "Global"
    assert get_country_name(None) == "Global"
    assert "Japón (JP)" in get_country_name("jp")
    assert "Alemania (DE)" in get_country_name("de")
    assert "Colombia (CO)" in get_country_name("co")
    assert "España (ES)" in get_country_name("es")
    # Fallback for unknown code
    assert "ZZ" in get_country_name("zz")


def test_get_countries_grouped():
    """Verify countries are grouped into geographic continents."""
    grouped = get_countries_grouped()
    assert "Global" in grouped
    assert "América del Sur" in grouped
    assert "Europa" in grouped
    assert "Asia" in grouped
    assert "África" in grouped
    assert "Oceanía" in grouped
    assert len(grouped["Europa"]) >= 30
