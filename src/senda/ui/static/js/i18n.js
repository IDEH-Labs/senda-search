// @license magnet:?xt=urn:btih:1f739d935de45e38526949e2bee45099c10f745f&dn=gpl-3.0.txt GPL-v3.0-or-later
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

/**
 * Sovereign i18n client translator for Senda Search.
 * Respects user privacy: no cookies, no remote telemetry, purely client-side.
 * GNU LibreJS Compliant: Declared Free Software under GNU GPL-3.0-or-later.
 */

const SENDA_TRANSLATIONS = {
  en: {
    brand_sub: "Sovereign Search",
    nav_home: "Search",
    nav_about: "About",
    nav_privacy: "Privacy",
    hero_title: "Senda",
    hero_subtitle: "Independent, ethical, and verifiable web search engine. Free software under GPL-3.0.",
    search_placeholder: "Explore the sovereign web...",
    search_btn: "Search",
    tab_web: "Web",
    tab_news: "News",
    tab_images: "Images",
    tab_library: "Library",
    pill_no_logs: "Zero Query Logs",
    pill_no_tracking: "Zero Profiling",
    pill_no_cookies: "Zero Cookies",
    pill_fsf: "100% Free Software",
    results_found: "results found in",
    results_page: "Page",
    results_of: "of",
    no_results_title: "No results matched your query",
    no_results_desc: "Try checking your spelling, using more general terms, or adding new sites to the crawler index.",
    footer_text: "Senda is sovereign software governed by the GNU GPLv3 license.",
  },
  es: {
    brand_sub: "Buscador Soberano",
    nav_home: "Buscar",
    nav_about: "Acerca de",
    nav_privacy: "Privacidad",
    hero_title: "Senda",
    hero_subtitle: "Motor de búsqueda web independiente, ético y verificable. Software libre bajo GPL-3.0.",
    search_placeholder: "Explora la web soberana...",
    search_btn: "Buscar",
    tab_web: "Web",
    tab_news: "Noticias",
    tab_images: "Imágenes",
    tab_library: "Biblioteca",
    pill_no_logs: "Cero Registros",
    pill_no_tracking: "Cero Rastreo",
    pill_no_cookies: "Cero Cookies",
    pill_fsf: "100% Software Libre",
    results_found: "resultados encontrados en",
    results_page: "Página",
    results_of: "de",
    no_results_title: "No se encontraron resultados para tu consulta",
    no_results_desc: "Revisa la ortografía, usa términos más generales o incorpora nuevos sitios al índice del rastreador.",
    footer_text: "Senda es software soberano amparado por la licencia GNU GPLv3.",
  },
  fr: {
    brand_sub: "Recherche Souveraine",
    nav_home: "Rechercher",
    nav_about: "À propos",
    nav_privacy: "Confidentialité",
    hero_title: "Senda",
    hero_subtitle: "Moteur de recherche web indépendant, éthique et vérifiable. Logiciel libre sous GPL-3.0.",
    search_placeholder: "Explorez le web souverain...",
    search_btn: "Rechercher",
    tab_web: "Web",
    tab_news: "Actualités",
    tab_images: "Images",
    tab_library: "Bibliothèque",
    pill_no_logs: "Zéro Journal",
    pill_no_tracking: "Zéro Pistage",
    pill_no_cookies: "Zéro Cookies",
    pill_fsf: "100% Logiciel Libre",
    results_found: "résultats trouvés en",
    results_page: "Page",
    results_of: "sur",
    no_results_title: "Aucun résultat trouvé pour votre requête",
    no_results_desc: "Vérifiez l'orthographe, utilisez des termes plus généraux ou indexez de nouveaux sites.",
    footer_text: "Senda est un logiciel souverain protégé par la licence GNU GPLv3.",
  },
  de: {
    brand_sub: "Souveräne Suche",
    nav_home: "Suche",
    nav_about: "Über uns",
    nav_privacy: "Datenschutz",
    hero_title: "Senda",
    hero_subtitle: "Unabhängige, ethische und überprüfbare Websuchmaschine. Freie Software unter GPL-3.0.",
    search_placeholder: "Erkunden Sie das souveräne Web...",
    search_btn: "Suchen",
    tab_web: "Web",
    tab_news: "Nachrichten",
    tab_images: "Bilder",
    tab_library: "Bibliothek",
    pill_no_logs: "Keine Protokolle",
    pill_no_tracking: "Kein Tracking",
    pill_no_cookies: "Keine Cookies",
    pill_fsf: "100% Freie Software",
    results_found: "Ergebnisse gefunden in",
    results_page: "Seite",
    results_of: "von",
    no_results_title: "Keine Ergebnisse für Ihre Suchanfrage gefunden",
    no_results_desc: "Überprüfen Sie die Schreibweise oder verwenden Sie allgemeinere Suchbegriffe.",
    footer_text: "Senda ist freie Software unter der GNU GPLv3-Lizenz.",
  }
};

function getActiveLanguage() {
  try {
    const saved = localStorage.getItem("senda_lang");
    if (saved && SENDA_TRANSLATIONS[saved]) return saved;
  } catch (e) {}

  const navLang = (navigator.language || "en").substring(0, 2).toLowerCase();
  return SENDA_TRANSLATIONS[navLang] ? navLang : "en";
}

function applyLanguage(lang) {
  const dict = SENDA_TRANSLATIONS[lang] || SENDA_TRANSLATIONS.en;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      if (el.tagName === "INPUT" && el.hasAttribute("placeholder")) {
        el.placeholder = dict[key];
      } else {
        el.textContent = dict[key];
      }
    }
  });

  const selector = document.getElementById("langSelector");
  if (selector) selector.value = lang;

  try {
    localStorage.setItem("senda_lang", lang);
  } catch (e) {}
}

document.addEventListener("DOMContentLoaded", () => {
  const initialLang = getActiveLanguage();
  applyLanguage(initialLang);

  const selector = document.getElementById("langSelector");
  if (selector) {
    selector.addEventListener("change", (e) => {
      applyLanguage(e.target.value);
    });
  }
});
// @license-end
