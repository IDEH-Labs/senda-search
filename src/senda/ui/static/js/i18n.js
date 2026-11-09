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
  },
  pt: {
    brand_sub: "Busca Soberana",
    nav_home: "Pesquisar",
    nav_about: "Sobre",
    nav_privacy: "Privacidade",
    hero_title: "Senda",
    hero_subtitle: "Motor de busca web independente, ético e verificável. Software livre sob GPL-3.0.",
    search_placeholder: "Explore a web soberana...",
    search_btn: "Pesquisar",
    tab_web: "Web",
    tab_news: "Notícias",
    tab_images: "Imagens",
    tab_library: "Biblioteca",
    pill_no_logs: "Zero Registros",
    pill_no_tracking: "Zero Rastreamento",
    pill_no_cookies: "Zero Cookies",
    pill_fsf: "100% Software Livre",
    results_found: "resultados encontrados em",
    results_page: "Página",
    results_of: "de",
    no_results_title: "Nenhum resultado corresponde à sua pesquisa",
    no_results_desc: "Verifique a ortografia, use termos mais gerais ou adicione novos sites ao índice.",
    footer_text: "Senda é software soberano regido pela licença GNU GPLv3.",
  },
  it: {
    brand_sub: "Ricerca Sovrana",
    nav_home: "Cerca",
    nav_about: "Informazioni",
    nav_privacy: "Privacy",
    hero_title: "Senda",
    hero_subtitle: "Motore di ricerca web indipendente, etico e verificabile. Software libero sotto licenza GPL-3.0.",
    search_placeholder: "Esplora il web sovrano...",
    search_btn: "Cerca",
    tab_web: "Web",
    tab_news: "Notizie",
    tab_images: "Immagini",
    tab_library: "Biblioteca",
    pill_no_logs: "Zero Registri",
    pill_no_tracking: "Zero Tracciamento",
    pill_no_cookies: "Zero Cookie",
    pill_fsf: "100% Software Libero",
    results_found: "risultati trovati in",
    results_page: "Pagina",
    results_of: "di",
    no_results_title: "Nessun risultato trovato per la ricerca",
    no_results_desc: "Controlla l'ortografia, usa termini più generici o aggiungi nuovi siti all'indice.",
    footer_text: "Senda è software sovrano rilasciato sotto licenza GNU GPLv3.",
  },
  ja: {
    brand_sub: "主権的検索",
    nav_home: "検索",
    nav_about: "概要",
    nav_privacy: "プライバシー",
    hero_title: "Senda",
    hero_subtitle: "独立した倫理的で検証可能なウェブ検索エンジン。GPL-3.0準拠の自由ソフトウェア。",
    search_placeholder: "主権あるウェブを探索...",
    search_btn: "検索",
    tab_web: "ウェブ",
    tab_news: "ニュース",
    tab_images: "画像",
    tab_library: "図書館",
    pill_no_logs: "検索ログゼロ",
    pill_no_tracking: "追跡ゼロ",
    pill_no_cookies: "クッキーゼロ",
    pill_fsf: "100% 自由ソフトウェア",
    results_found: "件の検索結果（",
    results_page: "ページ",
    results_of: "/",
    no_results_title: "検索条件に一致する結果は見つかりませんでした",
    no_results_desc: "スペルを確認するか、より一般的な語句を試してください。",
    footer_text: "SendaはGNU GPLv3ライセンスに基づく主権的ソフトウェアです。",
  },
  zh: {
    brand_sub: "主权搜索引擎",
    nav_home: "搜索",
    nav_about: "关于",
    nav_privacy: "隐私",
    hero_title: "Senda",
    hero_subtitle: "独立、道德且可验证的网络搜索引擎。基于 GPL-3.0 协议的自由软件。",
    search_placeholder: "探索主权互联网...",
    search_btn: "搜索",
    tab_web: "网页",
    tab_news: "新闻",
    tab_images: "图片",
    tab_library: "文库",
    pill_no_logs: "零查询日志",
    pill_no_tracking: "零用户画像",
    pill_no_cookies: "零 Cookies",
    pill_fsf: "100% 自由软件",
    results_found: "条结果，耗时",
    results_page: "第",
    results_of: "页，共",
    no_results_title: "未找到与您的搜索匹配的结果",
    no_results_desc: "请检查拼写，尝试更通用的词语，或将新站点编入索引。",
    footer_text: "Senda 是遵循 GNU GPLv3 许可证的主权自由软件。",
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
