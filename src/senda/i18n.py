# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Sovereign Internationalization (i18n) Engine for Senda Search.

Provides 100% offline, privacy-first, zero-telemetry multilingual translation catalogs,
HTTP Accept-Language resolution, and heuristic query-language routing.
Declared Free Software under GNU GPL-3.0-or-later.
"""

import re
from typing import Dict, Any, Optional
from starlette.requests import Request

# Supported interface languages with their native display names
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "es": "Español",
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "it": "Italiano",
    "zh": "中文",
    "ja": "日本語",
    "ru": "Русский",
    "ar": "العربية",
}

TRANSLATION_CATALOGS: Dict[str, Dict[str, str]] = {
    "es": {
        "nav_about": "Acerca de",
        "nav_privacy": "Privacidad",
        "nav_how_it_works": "Cómo funciona",
        "nav_reader": "Lector",
        "tag_organic": "100% Orgánico",
        "tag_no_tracking": "Sin Rastreo",
        "lang_switch": "Idioma",
        "search_placeholder": "Buscar en la web libre...",
        "tab_web": "Web",
        "tab_images": "Imágenes",
        "tab_news": "Noticias",
        "tab_videos": "Videos",
        "tab_library": "Biblioteca",
        "tab_community": "Comunidad & Foros",
        "tab_maps": "Mapas ↗",
        "filter_date": "Fecha",
        "date_all": "Todas",
        "date_1h": "1 hora",
        "date_1d": "24 horas",
        "date_1w": "1 semana",
        "date_1m": "1 mes",
        "date_2m": "2 meses",
        "date_6m": "6 meses",
        "date_1y": "1 año+",
        "opt_any_date": "Cualquier fecha",
        "opt_last_hour": "Última hora",
        "opt_last_24h": "Últimas 24 horas",
        "opt_last_week": "Última semana",
        "opt_last_month": "Último mes",
        "opt_last_2m": "Hace 2 meses",
        "opt_last_6m": "Hace 6 meses",
        "opt_last_year": "Hace 1 año o más",
        "filter_sort": "Ordenar",
        "sort_relevance": "Relevancia",
        "sort_recent": "Recientes",
        "opt_relevance": "Relevancia",
        "opt_most_recent": "Más recientes",
        "filter_region": "Región",
        "region_global": "Global",
        "region_all_world": "🌐 Global (Todo el mundo)",
        "search_country": "Buscar país o código...",
        "filter_safesearch": "SafeSearch",
        "safesearch_moderate": "Moderado",
        "safesearch_off": "Off",
        "opt_disabled": "Desactivado",
        "opt_moderate": "Moderado",
        "filter_lens": "Lente",
        "filter_lenses": "Lentes",
        "lens_custom_dsl": "DSL Personalizada",
        "lens_tech_libre": "Software Libre",
        "lens_no_farms": "Sin Granjas",
        "lens_science": "Ciencia",
        "lens_community": "Comunidad & Foros",
        "lens_standard": "Estándar",
        "opt_standard_no_lens": "Estándar (Sin lente)",
        "opt_tech_libre_desc": "Software Libre & Documentación",
        "opt_no_farms_desc": "Sin Granjas ni Muros",
        "opt_science_desc": "Ciencia & Fuentes Primarias",
        "opt_community_desc": "Comunidad & Foros",
        "opt_dsl_rule": "Regla DSL ($discard, $boost, $down):",
        "opt_apply_dsl": "Aplicar DSL",
        "density_comfortable": "Densidad: Cómoda",
        "density_compact": "Densidad: Compacta",
        "density_tooltip": "Alternar densidad visual (Cómoda / Compacta)",
        "results_found": "resultados",
        "in_seconds": "segundos",
        "no_results_title": "No se encontraron resultados",
        "no_results_desc": "Comprueba la ortografía o intenta con términos más generales.",
    },
    "en": {
        "nav_about": "About",
        "nav_privacy": "Privacy",
        "nav_how_it_works": "How it works",
        "nav_reader": "Reader",
        "tag_organic": "100% Organic",
        "tag_no_tracking": "No Tracking",
        "lang_switch": "Language",
        "search_placeholder": "Search the libre web...",
        "tab_web": "Web",
        "tab_images": "Images",
        "tab_news": "News",
        "tab_videos": "Videos",
        "tab_library": "Library",
        "tab_community": "Community & Forums",
        "tab_maps": "Maps ↗",
        "filter_date": "Date",
        "date_all": "All",
        "date_1h": "1 hour",
        "date_1d": "24 hours",
        "date_1w": "1 week",
        "date_1m": "1 month",
        "date_2m": "2 months",
        "date_6m": "6 months",
        "date_1y": "1 year+",
        "opt_any_date": "Any time",
        "opt_last_hour": "Past hour",
        "opt_last_24h": "Past 24 hours",
        "opt_last_week": "Past week",
        "opt_last_month": "Past month",
        "opt_last_2m": "Past 2 months",
        "opt_last_6m": "Past 6 months",
        "opt_last_year": "1 year or more",
        "filter_sort": "Sort",
        "sort_relevance": "Relevance",
        "sort_recent": "Recent",
        "opt_relevance": "Relevance",
        "opt_most_recent": "Most recent",
        "filter_region": "Region",
        "region_global": "Global",
        "region_all_world": "🌐 Global (All World)",
        "search_country": "Search country or code...",
        "filter_safesearch": "SafeSearch",
        "safesearch_moderate": "Moderate",
        "safesearch_off": "Off",
        "opt_disabled": "Off",
        "opt_moderate": "Moderate",
        "filter_lens": "Lens",
        "filter_lenses": "Lenses",
        "lens_custom_dsl": "Custom DSL",
        "lens_tech_libre": "Free Software",
        "lens_no_farms": "No SEO Farms",
        "lens_science": "Science",
        "lens_community": "Community & Forums",
        "lens_standard": "Standard",
        "opt_standard_no_lens": "Standard (No lens)",
        "opt_tech_libre_desc": "Free Software & Documentation",
        "opt_no_farms_desc": "No Content Farms or Paywalls",
        "opt_science_desc": "Science & Primary Sources",
        "opt_community_desc": "Community & Forums",
        "opt_dsl_rule": "DSL Rule ($discard, $boost, $down):",
        "opt_apply_dsl": "Apply DSL",
        "density_comfortable": "Density: Comfortable",
        "density_compact": "Density: Compact",
        "density_tooltip": "Toggle visual density (Comfortable / Compact)",
        "results_found": "results",
        "in_seconds": "seconds",
        "no_results_title": "No results found",
        "no_results_desc": "Check your spelling or try more general keywords.",
    },
    "fr": {
        "nav_about": "À propos",
        "nav_privacy": "Confidentialité",
        "nav_how_it_works": "Comment ça marche",
        "nav_reader": "Lecteur",
        "tag_organic": "100% Organique",
        "tag_no_tracking": "Sans Pistage",
        "lang_switch": "Langue",
        "search_placeholder": "Rechercher sur le web libre...",
        "tab_web": "Web",
        "tab_images": "Images",
        "tab_news": "Actualités",
        "tab_videos": "Vidéos",
        "tab_library": "Bibliothèque",
        "tab_community": "Communauté & Forums",
        "tab_maps": "Cartes ↗",
        "filter_date": "Date",
        "date_all": "Toutes",
        "date_1h": "1 heure",
        "date_1d": "24 heures",
        "date_1w": "1 semaine",
        "date_1m": "1 mois",
        "date_2m": "2 mois",
        "date_6m": "6 mois",
        "date_1y": "1 an+",
        "opt_any_date": "N'importe quand",
        "opt_last_hour": "Dernière heure",
        "opt_last_24h": "Dernières 24 heures",
        "opt_last_week": "Dernière semaine",
        "opt_last_month": "Dernier mois",
        "opt_last_2m": "Il y a 2 mois",
        "opt_last_6m": "Il y a 6 mois",
        "opt_last_year": "Il y a 1 an ou plus",
        "filter_sort": "Trier",
        "sort_relevance": "Pertinence",
        "sort_recent": "Récents",
        "opt_relevance": "Pertinence",
        "opt_most_recent": "Plus récents",
        "filter_region": "Région",
        "region_global": "Mondial",
        "region_all_world": "🌐 Mondial (Monde entier)",
        "search_country": "Rechercher pays ou code...",
        "filter_safesearch": "SafeSearch",
        "safesearch_moderate": "Modéré",
        "safesearch_off": "Off",
        "opt_disabled": "Désactivé",
        "opt_moderate": "Modéré",
        "filter_lens": "Lentille",
        "filter_lenses": "Lentilles",
        "lens_custom_dsl": "DSL Personnalisée",
        "lens_tech_libre": "Logiciel Libre",
        "lens_no_farms": "Sans Fermes",
        "lens_science": "Science",
        "lens_community": "Communauté & Forums",
        "lens_standard": "Standard",
        "opt_standard_no_lens": "Standard (Sans lentille)",
        "opt_tech_libre_desc": "Logiciel Libre & Documentation",
        "opt_no_farms_desc": "Sans Fermes SEO ni Paywalls",
        "opt_science_desc": "Science & Sources Primaires",
        "opt_community_desc": "Communauté & Forums",
        "opt_dsl_rule": "Règle DSL ($discard, $boost, $down) :",
        "opt_apply_dsl": "Appliquer DSL",
        "density_comfortable": "Densité : Confortable",
        "density_compact": "Densité : Compacte",
        "density_tooltip": "Changer la densité (Confortable / Compacte)",
        "results_found": "résultats",
        "in_seconds": "secondes",
        "no_results_title": "Aucun résultat trouvé",
        "no_results_desc": "Vérifiez l'orthographe ou essayez des mots-clés plus généraux.",
    },
    "de": {
        "nav_about": "Über uns",
        "nav_privacy": "Datenschutz",
        "nav_how_it_works": "Wie es funktioniert",
        "nav_reader": "Leser",
        "tag_organic": "100% Organisch",
        "tag_no_tracking": "Kein Tracking",
        "lang_switch": "Sprache",
        "search_placeholder": "Im freien Web suchen...",
        "tab_web": "Web",
        "tab_images": "Bilder",
        "tab_news": "Nachrichten",
        "tab_videos": "Videos",
        "tab_library": "Bibliothek",
        "tab_community": "Community & Foren",
        "tab_maps": "Karten ↗",
        "filter_date": "Datum",
        "date_all": "Alle",
        "date_1h": "1 Stunde",
        "date_1d": "24 Stunden",
        "date_1w": "1 Woche",
        "date_1m": "1 Monat",
        "date_2m": "2 Monate",
        "date_6m": "6 Monate",
        "date_1y": "1 Jahr+",
        "opt_any_date": "Beliebige Zeit",
        "opt_last_hour": "Letzte Stunde",
        "opt_last_24h": "Letzte 24 Stunden",
        "opt_last_week": "Letzte Woche",
        "opt_last_month": "Letzter Monat",
        "opt_last_2m": "Letzte 2 Monate",
        "opt_last_6m": "Letzte 6 Monate",
        "opt_last_year": "1 Jahr oder mehr",
        "filter_sort": "Sortieren",
        "sort_relevance": "Relevanz",
        "sort_recent": "Neueste",
        "opt_relevance": "Relevanz",
        "opt_most_recent": "Neueste zuerst",
        "filter_region": "Region",
        "region_global": "Global",
        "region_all_world": "🌐 Global (Weltweit)",
        "search_country": "Land oder Code suchen...",
        "filter_safesearch": "SafeSearch",
        "safesearch_moderate": "Moderat",
        "safesearch_off": "Aus",
        "opt_disabled": "Aus",
        "opt_moderate": "Moderat",
        "filter_lens": "Filterlinse",
        "filter_lenses": "Filterlinsen",
        "lens_custom_dsl": "Eigene DSL",
        "lens_tech_libre": "Freie Software",
        "lens_no_farms": "Ohne Farmen",
        "lens_science": "Wissenschaft",
        "lens_community": "Community & Foren",
        "lens_standard": "Standard",
        "opt_standard_no_lens": "Standard (Keine Linse)",
        "opt_tech_libre_desc": "Freie Software & Dokumentation",
        "opt_no_farms_desc": "Ohne Content-Farmen oder Paywalls",
        "opt_science_desc": "Wissenschaft & Primärquellen",
        "opt_community_desc": "Community & Foren",
        "opt_dsl_rule": "DSL-Regel ($discard, $boost, $down):",
        "opt_apply_dsl": "DSL anwenden",
        "density_comfortable": "Dichte: Komfortabel",
        "density_compact": "Dichte: Kompakt",
        "density_tooltip": "Visuelle Dichte umschalten (Komfortabel / Kompakt)",
        "results_found": "Ergebnisse",
        "in_seconds": "Sekunden",
        "no_results_title": "Keine Ergebnisse gefunden",
        "no_results_desc": "Überprüfen Sie die Rechtschreibung oder verwenden Sie allgemeinere Begriffe.",
    },
    "pt": {
        "nav_about": "Sobre",
        "nav_privacy": "Privacidade",
        "nav_how_it_works": "Como funciona",
        "nav_reader": "Leitor",
        "tag_organic": "100% Orgânico",
        "tag_no_tracking": "Sem Rastreamento",
        "lang_switch": "Idioma",
        "search_placeholder": "Pesquisar na web livre...",
        "tab_web": "Web",
        "tab_images": "Imagens",
        "tab_news": "Notícias",
        "tab_videos": "Vídeos",
        "tab_library": "Biblioteca",
        "tab_community": "Comunidade & Fóruns",
        "tab_maps": "Mapas ↗",
        "filter_date": "Data",
        "date_all": "Todas",
        "date_1h": "1 hora",
        "date_1d": "24 horas",
        "date_1w": "1 semana",
        "date_1m": "1 mês",
        "date_2m": "2 meses",
        "date_6m": "6 meses",
        "date_1y": "1 ano+",
        "opt_any_date": "Qualquer data",
        "opt_last_hour": "Última hora",
        "opt_last_24h": "Últimas 24 horas",
        "opt_last_week": "Última semana",
        "opt_last_month": "Último mês",
        "opt_last_2m": "Últimos 2 meses",
        "opt_last_6m": "Últimos 6 meses",
        "opt_last_year": "1 ano ou mais",
        "filter_sort": "Ordenar",
        "sort_relevance": "Relevância",
        "sort_recent": "Recentes",
        "opt_relevance": "Relevância",
        "opt_most_recent": "Mais recentes",
        "filter_region": "Região",
        "region_global": "Global",
        "region_all_world": "🌐 Global (Mundo todo)",
        "search_country": "Buscar país ou código...",
        "filter_safesearch": "SafeSearch",
        "safesearch_moderate": "Moderado",
        "safesearch_off": "Off",
        "opt_disabled": "Desativado",
        "opt_moderate": "Moderado",
        "filter_lens": "Lente",
        "filter_lenses": "Lentes",
        "lens_custom_dsl": "DSL Personalizada",
        "lens_tech_libre": "Software Livre",
        "lens_no_farms": "Sem Fazendas",
        "lens_science": "Ciência",
        "lens_community": "Comunidade & Fóruns",
        "lens_standard": "Padrão",
        "opt_standard_no_lens": "Padrão (Sem lente)",
        "opt_tech_libre_desc": "Software Livre & Documentação",
        "opt_no_farms_desc": "Sem Fazendas de Conteúdo ou Paywalls",
        "opt_science_desc": "Ciência & Fontes Primárias",
        "opt_community_desc": "Comunidade & Fóruns",
        "opt_dsl_rule": "Regra DSL ($discard, $boost, $down):",
        "opt_apply_dsl": "Aplicar DSL",
        "density_comfortable": "Densidade: Confortável",
        "density_compact": "Densidade: Compacta",
        "density_tooltip": "Alternar densidade visual (Confortável / Compacta)",
        "results_found": "resultados",
        "in_seconds": "segundos",
        "no_results_title": "Nenhum resultado encontrado",
        "no_results_desc": "Verifique a ortografia ou tente palavras-chave mais gerais.",
    },
    "it": {
        "nav_about": "Informazioni",
        "nav_privacy": "Privacy",
        "nav_how_it_works": "Come funziona",
        "nav_reader": "Lettore",
        "tag_organic": "100% Organico",
        "tag_no_tracking": "Nessun Tracciamento",
        "lang_switch": "Lingua",
        "search_placeholder": "Cerca nel web libero...",
        "tab_web": "Web",
        "tab_images": "Immagini",
        "tab_news": "Notizie",
        "tab_videos": "Video",
        "tab_library": "Biblioteca",
        "tab_community": "Comunità & Forum",
        "tab_maps": "Mappe ↗",
        "filter_date": "Data",
        "date_all": "Tutte",
        "date_1h": "1 ora",
        "date_1d": "24 ore",
        "date_1w": "1 settimana",
        "date_1m": "1 mese",
        "date_2m": "2 mesi",
        "date_6m": "6 mesi",
        "date_1y": "1 anno+",
        "opt_any_date": "Qualsiasi data",
        "opt_last_hour": "Ultima ora",
        "opt_last_24h": "Ultime 24 ore",
        "opt_last_week": "Ultima settimana",
        "opt_last_month": "Ultimo mese",
        "opt_last_2m": "Ultimi 2 mesi",
        "opt_last_6m": "Ultimi 6 mesi",
        "opt_last_year": "1 anno o più",
        "filter_sort": "Ordina",
        "sort_relevance": "Rilevanza",
        "sort_recent": "Recenti",
        "opt_relevance": "Rilevanza",
        "opt_most_recent": "Più recenti",
        "filter_region": "Regione",
        "region_global": "Globale",
        "region_all_world": "🌐 Globale (Tutto il mondo)",
        "search_country": "Cerca paese o codice...",
        "filter_safesearch": "SafeSearch",
        "safesearch_moderate": "Moderato",
        "safesearch_off": "Off",
        "opt_disabled": "Disattivato",
        "opt_moderate": "Moderato",
        "filter_lens": "Lente",
        "filter_lenses": "Lenti",
        "lens_custom_dsl": "DSL Personalizzata",
        "lens_tech_libre": "Software Libero",
        "lens_no_farms": "Senza Content Farm",
        "lens_science": "Scienza",
        "lens_community": "Comunità & Forum",
        "lens_standard": "Standard",
        "opt_standard_no_lens": "Standard (Nessuna lente)",
        "opt_tech_libre_desc": "Software Libero & Documentazione",
        "opt_no_farms_desc": "Senza Content Farm o Paywall",
        "opt_science_desc": "Scienza & Fonti Primarie",
        "opt_community_desc": "Comunità & Forum",
        "opt_dsl_rule": "Regola DSL ($discard, $boost, $down):",
        "opt_apply_dsl": "Applica DSL",
        "density_comfortable": "Densità: Comoda",
        "density_compact": "Densità: Compatta",
        "density_tooltip": "Cambia densità visiva (Comoda / Compatta)",
        "results_found": "risultati",
        "in_seconds": "secondi",
        "no_results_title": "Nessun risultato trovato",
        "no_results_desc": "Controlla l'ortografia o prova termini più generali.",
    },
}


def get_translation_catalog(lang: str) -> Dict[str, str]:
    """Retrieve full catalog for a language with fallback to Spanish."""
    code = lang.lower().strip()[:2] if lang else "es"
    base = TRANSLATION_CATALOGS.get("es", {})
    if code in TRANSLATION_CATALOGS and code != "es":
        merged = dict(base)
        merged.update(TRANSLATION_CATALOGS[code])
        return merged
    return base


def translate(key: str, lang: str = "es", default: Optional[str] = None) -> str:
    """Translate a single key for the given language."""
    catalog = get_translation_catalog(lang)
    return catalog.get(key, default if default is not None else key)


def resolve_language(request: Request, query_lang: Optional[str] = None) -> str:
    """Resolve user interface language with strict privacy and Zero-JS compatibility.

    Priority:
    1. Explicit query parameter (?lang=en)
    2. Functional preference cookie (senda_lang=en)
    3. HTTP Accept-Language request header
    4. Default configured language ('es')
    """
    if query_lang:
        code = query_lang.lower().strip()[:2]
        if code in SUPPORTED_LANGUAGES:
            return code

    cookie_lang = request.cookies.get("senda_lang", "").lower().strip()[:2]
    if cookie_lang in SUPPORTED_LANGUAGES:
        return cookie_lang

    accept_lang = request.headers.get("accept-language", "")
    if accept_lang:
        for part in accept_lang.split(","):
            token = part.split(";")[0].strip().lower()
            code = token.split("-")[0]
            if code in SUPPORTED_LANGUAGES:
                return code

    return "es"


def detect_query_language(query: str, fallback_lang: str = "es") -> str:
    """Detect search query natural language with zero latency, offline, and zero tracking.

    Uses Unicode scripts, distinctive alphabetic diacritics, and high-frequency functional stopwords.
    """
    if not query or not query.strip():
        return fallback_lang

    q = query.lower().strip()

    # 1. Non-Latin scripts check
    for ch in q:
        code = ord(ch)
        if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            return "zh"
        if 0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF:
            return "ja"
        if 0x0400 <= code <= 0x04FF:
            return "ru"
        if 0x0600 <= code <= 0x06FF:
            return "ar"

    # 2. Distinctive diacritics
    if any(c in q for c in ("ä", "ö", "ü", "ß")):
        return "de"
    if any(c in q for c in ("¿", "¡", "ñ")):
        return "es"
    if any(c in q for c in ("ã", "õ")):
        return "pt"
    if any(c in q for c in ("œ", "ù", "ê", "à")):
        return "fr"

    # 3. High-frequency stop word matching
    words = set(re.findall(r"\b\w+\b", q))
    scores = {
        "en": len(words & {"the", "how", "what", "why", "where", "who", "which", "best", "near", "for", "with", "and", "from", "free", "review", "guide", "download"}),
        "es": len(words & {"el", "la", "de", "que", "en", "los", "del", "las", "por", "un", "para", "con", "una", "como", "donde", "quien", "cual", "noticias", "descargar"}),
        "fr": len(words & {"le", "la", "les", "de", "du", "des", "pour", "dans", "qui", "quoi", "comment", "avec", "sur", "recette", "telecharger"}),
        "de": len(words & {"der", "die", "das", "und", "in", "zu", "den", "nicht", "von", "wie", "was", "warum", "kaufen", "herunterladen"}),
        "pt": len(words & {"o", "os", "do", "da", "dos", "das", "em", "para", "com", "nao", "onde", "como", "porque", "baixar", "noticias"}),
        "it": len(words & {"il", "lo", "la", "gli", "le", "di", "da", "con", "su", "per", "tra", "fra", "cosa", "come", "dove", "scaricare"}),
    }
    best_lang, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score > 0:
        return best_lang

    return fallback_lang
