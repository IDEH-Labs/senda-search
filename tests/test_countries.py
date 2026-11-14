# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Tests for Worldwide Country Catalog and Regional Localization."""

from senda.countries import (
    COUNTRY_CATALOG,
    COUNTRY_BY_CODE,
    SOVEREIGN_REGISTRY,
    get_country_name,
    get_countries_grouped,
    get_sovereign_country,
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
    assert len(grouped["África"]) >= 50


def test_sovereign_country_universal_registry():
    """Verify that SOVEREIGN_REGISTRY covers 100% of sovereign nations with verified HTTPS portals."""
    assert len(SOVEREIGN_REGISTRY) >= 195

    for code, country in SOVEREIGN_REGISTRY.items():
        assert len(country.code) == 2
        assert country.official_portal.startswith("https://"), f"{code} portal must be HTTPS: {country.official_portal}"
        assert country.wikidata_qid.startswith("Q"), f"{code} missing valid Wikidata QID"
        assert country.name_es, f"{code} missing Spanish name"
        assert country.name_en, f"{code} missing English name"
        assert country.portal_name, f"{code} missing portal name"


def test_get_sovereign_country_lookups():
    """Verify resolution across various continents, queries, Q-IDs, and institutional prefixes."""
    # Africa: Burundi
    bi = get_sovereign_country(query="burundi")
    assert bi is not None
    assert bi.official_portal == "https://presidence.gov.bi/"
    assert bi.wikidata_qid == "Q967"
    assert get_sovereign_country(qid="Q967") == bi

    # Africa: Tanzania (Ikulu State House)
    tz = get_sovereign_country(query="gobierno de tanzania")
    assert tz is not None
    assert tz.official_portal == "https://www.ikulu.go.tz/"
    assert tz.wikidata_qid == "Q924"

    # Africa: DR Congo (Primature)
    cd = get_sovereign_country(query="republica democratica del congo")
    assert cd is not None
    assert cd.official_portal == "https://www.primature.gouv.cd/"

    # Asia: Vietnam
    vn = get_sovereign_country(query="vietnam")
    assert vn is not None
    assert vn.official_portal == "https://chinhphu.vn/"

    # Latin America: El Salvador
    sv = get_sovereign_country(query="gobierno de el salvador")
    assert sv is not None
    assert sv.official_portal == "https://www.transparencia.gob.sv/"

    # Caribbean: Trinidad & Tobago
    tt = get_sovereign_country(query="trinidad y tobago")
    assert tt is not None
    assert tt.official_portal == "https://www.ttconnect.gov.tt/"

    # Africa: South Africa
    za = get_sovereign_country(query="sudáfrica")
    assert za is not None
    assert za.official_portal == "https://www.gov.za/"

    # Europe/Asia: Turkey
    tr = get_sovereign_country(query="turquía")
    assert tr is not None
    assert tr.official_portal == "https://www.turkiye.gov.tr/"


def test_sovereign_country_typo_tolerance():
    """Verify typo tolerance matches sovereign countries on 1-2 edit distance."""
    # 1-letter typo on Burundi -> Burundi official presidency portal
    bi = get_sovereign_country(query="burundo")
    assert bi is not None
    assert bi.name_es == "Burundi"
    assert bi.official_portal == "https://presidence.gov.bi/"

    # Typo on Tanzania
    tz = get_sovereign_country(query="tanzanya")
    assert tz is not None
    assert tz.name_es == "Tanzania"
    assert tz.official_portal == "https://www.ikulu.go.tz/"

    # Typo on Vietnam
    vn = get_sovereign_country(query="vietna")
    assert vn is not None
    assert vn.name_es == "Vietnam"

    # Typo on El Salvador
    sv = get_sovereign_country(query="el salvado")
    assert sv is not None
    assert sv.name_es == "El Salvador"

    # Typo on South Africa
    za = get_sovereign_country(query="sudafrika")
    assert za is not None
    assert za.name_es == "Sudáfrica"


