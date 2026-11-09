# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Worldwide ISO 3166-1 Sovereign Countries and Regional Catalog for Senda Search."""

from typing import Dict, List, Optional


COUNTRY_CATALOG: List[Dict[str, str]] = [
    # Global
    {"code": "all", "name": "Global (Todo el mundo)", "continent": "Global"},

    # América del Sur
    {"code": "ar", "name": "Argentina", "continent": "América del Sur"},
    {"code": "bo", "name": "Bolivia", "continent": "América del Sur"},
    {"code": "br", "name": "Brasil", "continent": "América del Sur"},
    {"code": "cl", "name": "Chile", "continent": "América del Sur"},
    {"code": "co", "name": "Colombia", "continent": "América del Sur"},
    {"code": "ec", "name": "Ecuador", "continent": "América del Sur"},
    {"code": "gy", "name": "Guyana", "continent": "América del Sur"},
    {"code": "py", "name": "Paraguay", "continent": "América del Sur"},
    {"code": "pe", "name": "Perú", "continent": "América del Sur"},
    {"code": "sr", "name": "Surinam", "continent": "América del Sur"},
    {"code": "uy", "name": "Uruguay", "continent": "América del Sur"},
    {"code": "ve", "name": "Venezuela", "continent": "América del Sur"},

    # América del Norte y Central
    {"code": "ca", "name": "Canadá", "continent": "América del Norte y Central"},
    {"code": "us", "name": "Estados Unidos", "continent": "América del Norte y Central"},
    {"code": "mx", "name": "México", "continent": "América del Norte y Central"},
    {"code": "bz", "name": "Belice", "continent": "América del Norte y Central"},
    {"code": "cr", "name": "Costa Rica", "continent": "América del Norte y Central"},
    {"code": "sv", "name": "El Salvador", "continent": "América del Norte y Central"},
    {"code": "gt", "name": "Guatemala", "continent": "América del Norte y Central"},
    {"code": "hn", "name": "Honduras", "continent": "América del Norte y Central"},
    {"code": "ni", "name": "Nicaragua", "continent": "América del Norte y Central"},
    {"code": "pa", "name": "Panamá", "continent": "América del Norte y Central"},

    # Caribe
    {"code": "cu", "name": "Cuba", "continent": "Caribe"},
    {"code": "do", "name": "República Dominicana", "continent": "Caribe"},
    {"code": "pr", "name": "Puerto Rico", "continent": "Caribe"},
    {"code": "ht", "name": "Haití", "continent": "Caribe"},
    {"code": "jm", "name": "Jamaica", "continent": "Caribe"},
    {"code": "bs", "name": "Bahamas", "continent": "Caribe"},
    {"code": "bb", "name": "Barbados", "continent": "Caribe"},
    {"code": "tt", "name": "Trinidad y Tobago", "continent": "Caribe"},

    # Europa
    {"code": "al", "name": "Albania", "continent": "Europa"},
    {"code": "de", "name": "Alemania", "continent": "Europa"},
    {"code": "ad", "name": "Andorra", "continent": "Europa"},
    {"code": "at", "name": "Austria", "continent": "Europa"},
    {"code": "be", "name": "Bélgica", "continent": "Europa"},
    {"code": "by", "name": "Bielorrusia", "continent": "Europa"},
    {"code": "ba", "name": "Bosnia y Herzegovina", "continent": "Europa"},
    {"code": "bg", "name": "Bulgaria", "continent": "Europa"},
    {"code": "cy", "name": "Chipre", "continent": "Europa"},
    {"code": "hr", "name": "Croacia", "continent": "Europa"},
    {"code": "dk", "name": "Dinamarca", "continent": "Europa"},
    {"code": "sk", "name": "Eslovaquia", "continent": "Europa"},
    {"code": "si", "name": "Eslovenia", "continent": "Europa"},
    {"code": "es", "name": "España", "continent": "Europa"},
    {"code": "ee", "name": "Estonia", "continent": "Europa"},
    {"code": "fi", "name": "Finlandia", "continent": "Europa"},
    {"code": "fr", "name": "Francia", "continent": "Europa"},
    {"code": "gr", "name": "Grecia", "continent": "Europa"},
    {"code": "hu", "name": "Hungría", "continent": "Europa"},
    {"code": "ie", "name": "Irlanda", "continent": "Europa"},
    {"code": "is", "name": "Islandia", "continent": "Europa"},
    {"code": "it", "name": "Italia", "continent": "Europa"},
    {"code": "lv", "name": "Letonia", "continent": "Europa"},
    {"code": "li", "name": "Liechtenstein", "continent": "Europa"},
    {"code": "lt", "name": "Lituania", "continent": "Europa"},
    {"code": "lu", "name": "Luxemburgo", "continent": "Europa"},
    {"code": "mk", "name": "Macedonia del Norte", "continent": "Europa"},
    {"code": "mt", "name": "Malta", "continent": "Europa"},
    {"code": "md", "name": "Moldavia", "continent": "Europa"},
    {"code": "mc", "name": "Mónaco", "continent": "Europa"},
    {"code": "me", "name": "Montenegro", "continent": "Europa"},
    {"code": "no", "name": "Noruega", "continent": "Europa"},
    {"code": "nl", "name": "Países Bajos", "continent": "Europa"},
    {"code": "pl", "name": "Polonia", "continent": "Europa"},
    {"code": "pt", "name": "Portugal", "continent": "Europa"},
    {"code": "gb", "name": "Reino Unido", "continent": "Europa"},
    {"code": "cz", "name": "República Checa", "continent": "Europa"},
    {"code": "ro", "name": "Rumanía", "continent": "Europa"},
    {"code": "ru", "name": "Rusia", "continent": "Europa"},
    {"code": "sm", "name": "San Marino", "continent": "Europa"},
    {"code": "rs", "name": "Serbia", "continent": "Europa"},
    {"code": "se", "name": "Suecia", "continent": "Europa"},
    {"code": "ch", "name": "Suiza", "continent": "Europa"},
    {"code": "ua", "name": "Ucrania", "continent": "Europa"},
    {"code": "va", "name": "Ciudad del Vaticano", "continent": "Europa"},

    # Asia y Medio Oriente
    {"code": "af", "name": "Afganistán", "continent": "Asia"},
    {"code": "sa", "name": "Arabia Saudita", "continent": "Asia"},
    {"code": "am", "name": "Armenia", "continent": "Asia"},
    {"code": "az", "name": "Azerbaiyán", "continent": "Asia"},
    {"code": "bd", "name": "Bangladés", "continent": "Asia"},
    {"code": "bh", "name": "Baréin", "continent": "Asia"},
    {"code": "bn", "name": "Brunéi", "continent": "Asia"},
    {"code": "bt", "name": "Bután", "continent": "Asia"},
    {"code": "kh", "name": "Camboya", "continent": "Asia"},
    {"code": "qa", "name": "Catar", "continent": "Asia"},
    {"code": "cn", "name": "China", "continent": "Asia"},
    {"code": "kr", "name": "Corea del Sur", "continent": "Asia"},
    {"code": "ae", "name": "Emiratos Árabes Unidos", "continent": "Asia"},
    {"code": "ph", "name": "Filipinas", "continent": "Asia"},
    {"code": "ge", "name": "Georgia", "continent": "Asia"},
    {"code": "in", "name": "India", "continent": "Asia"},
    {"code": "id", "name": "Indonesia", "continent": "Asia"},
    {"code": "iq", "name": "Irak", "continent": "Asia"},
    {"code": "ir", "name": "Irán", "continent": "Asia"},
    {"code": "il", "name": "Israel", "continent": "Asia"},
    {"code": "jp", "name": "Japón", "continent": "Asia"},
    {"code": "jo", "name": "Jordania", "continent": "Asia"},
    {"code": "kz", "name": "Kazajistán", "continent": "Asia"},
    {"code": "kg", "name": "Kirguistán", "continent": "Asia"},
    {"code": "kw", "name": "Kuwait", "continent": "Asia"},
    {"code": "lb", "name": "Líbano", "continent": "Asia"},
    {"code": "my", "name": "Malasia", "continent": "Asia"},
    {"code": "mv", "name": "Maldivas", "continent": "Asia"},
    {"code": "mn", "name": "Mongolia", "continent": "Asia"},
    {"code": "np", "name": "Nepal", "continent": "Asia"},
    {"code": "om", "name": "Omán", "continent": "Asia"},
    {"code": "pk", "name": "Pakistán", "continent": "Asia"},
    {"code": "ps", "name": "Palestina", "continent": "Asia"},
    {"code": "sg", "name": "Singapur", "continent": "Asia"},
    {"code": "sy", "name": "Siria", "continent": "Asia"},
    {"code": "lk", "name": "Sri Lanka", "continent": "Asia"},
    {"code": "th", "name": "Tailandia", "continent": "Asia"},
    {"code": "tw", "name": "Taiwán", "continent": "Asia"},
    {"code": "tr", "name": "Turquía", "continent": "Asia"},
    {"code": "uz", "name": "Uzbekistán", "continent": "Asia"},
    {"code": "vn", "name": "Vietnam", "continent": "Asia"},

    # África
    {"code": "ao", "name": "Angola", "continent": "África"},
    {"code": "dz", "name": "Argelia", "continent": "África"},
    {"code": "cm", "name": "Camerún", "continent": "África"},
    {"code": "ci", "name": "Costa de Marfil", "continent": "África"},
    {"code": "eg", "name": "Egipto", "continent": "África"},
    {"code": "et", "name": "Etiopía", "continent": "África"},
    {"code": "gh", "name": "Ghana", "continent": "África"},
    {"code": "ke", "name": "Kenia", "continent": "África"},
    {"code": "ma", "name": "Marruecos", "continent": "África"},
    {"code": "mz", "name": "Mozambique", "continent": "África"},
    {"code": "ng", "name": "Nigeria", "continent": "África"},
    {"code": "sn", "name": "Senegal", "continent": "África"},
    {"code": "za", "name": "Sudáfrica", "continent": "África"},
    {"code": "tn", "name": "Túnez", "continent": "África"},
    {"code": "ug", "name": "Uganda", "continent": "África"},

    # Oceanía
    {"code": "au", "name": "Australia", "continent": "Oceanía"},
    {"code": "nz", "name": "Nueva Zelanda", "continent": "Oceanía"},
    {"code": "fj", "name": "Fiyi", "continent": "Oceanía"},
    {"code": "pg", "name": "Papúa Nueva Guinea", "continent": "Oceanía"},
]

COUNTRY_BY_CODE: Dict[str, str] = {
    c["code"]: c["name"] for c in COUNTRY_CATALOG
}


def get_country_name(code: Optional[str]) -> str:
    """Return Spanish country display name for an ISO country code."""
    if not code or code.lower() in ("all", "global", "none"):
        return "Global"
    code_lower = code.lower().strip()
    if code_lower in COUNTRY_BY_CODE:
        return f"{COUNTRY_BY_CODE[code_lower]} ({code.upper()})"
    return f"Región: {code.upper()}"


def get_countries_grouped() -> Dict[str, List[Dict[str, str]]]:
    """Return countries grouped by geographic continent/region."""
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for item in COUNTRY_CATALOG:
        cont = item["continent"]
        if cont not in grouped:
            grouped[cont] = []
        grouped[cont].append(item)
    return grouped
