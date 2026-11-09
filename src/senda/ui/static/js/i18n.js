// @license magnet:?xt=urn:btih:1f739d935de45e38526949e2bee45099c10f745f&dn=gpl-3.0.txt GPL-v3.0-or-later
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

/**
 * Senda Minimalist Core (i18n, Theme Manager)
 * Zero tracking, zero telemetry, zero cookies. 100% Client-Side.
 * GNU LibreJS Compliant: Declared Free Software under GNU GPL-3.0-or-later.
 */

const SENDA_TRANSLATIONS = {
  es: {
    nav_about: "Acerca de",
    nav_privacy: "Privacidad",
    search_placeholder: "Buscar en la web libre...",
    search_btn: "Buscar con Senda",
    lucky_btn: "Explorar la red libre",
    tab_web: "Todo",
    tab_images: "Imágenes",
    tab_news: "Noticias",
    tab_library: "Biblioteca",
    results_found: "resultados (",
    no_results_title: "No se encontraron resultados",
    no_results_desc: "Comprueba que las palabras estén bien escritas o prueba con términos más generales.",
  },
  en: {
    nav_about: "About",
    nav_privacy: "Privacy",
    search_placeholder: "Search the libre web...",
    search_btn: "Senda Search",
    lucky_btn: "Explore the libre web",
    tab_web: "All",
    tab_images: "Images",
    tab_news: "News",
    tab_library: "Library",
    results_found: "results (",
    no_results_title: "No results found",
    no_results_desc: "Check your spelling or try more general keywords.",
  },
  fr: {
    nav_about: "À propos",
    nav_privacy: "Confidentialité",
    search_placeholder: "Rechercher sur le web libre...",
    search_btn: "Recherche Senda",
    lucky_btn: "Explorer le web libre",
    tab_web: "Tout",
    tab_images: "Images",
    tab_news: "Actualités",
    tab_library: "Bibliothèque",
    results_found: "résultats (",
    no_results_title: "Aucun résultat trouvé",
    no_results_desc: "Vérifiez l'orthographe ou essayez des mots-clés plus généraux.",
  },
  de: {
    nav_about: "Über uns",
    nav_privacy: "Datenschutz",
    search_placeholder: "Im freien Web suchen...",
    search_btn: "Senda Suche",
    lucky_btn: "Freies Web erkunden",
    tab_web: "Alle",
    tab_images: "Bilder",
    tab_news: "Nachrichten",
    tab_library: "Bibliothek",
    results_found: "Ergebnisse (",
    no_results_title: "Keine Ergebnisse gefunden",
    no_results_desc: "Prüfen Sie die Schreibweise oder versuchen Sie allgemeinere Suchbegriffe.",
  },
  pt: {
    nav_about: "Sobre",
    nav_privacy: "Privacidade",
    search_placeholder: "Pesquisar na web livre...",
    search_btn: "Pesquisar com Senda",
    lucky_btn: "Explorar a web livre",
    tab_web: "Tudo",
    tab_images: "Imagens",
    tab_news: "Notícias",
    tab_library: "Biblioteca",
    results_found: "resultados (",
    no_results_title: "Nenhum resultado encontrado",
    no_results_desc: "Verifique a ortografia ou tente palavras-chave mais gerais.",
  },
  it: {
    nav_about: "Info",
    nav_privacy: "Privacy",
    search_placeholder: "Cerca nel web libero...",
    search_btn: "Cerca con Senda",
    lucky_btn: "Esplora il web libero",
    tab_web: "Tutti",
    tab_images: "Immagini",
    tab_news: "Notizie",
    tab_library: "Biblioteca",
    results_found: "risultati (",
    no_results_title: "Nessun risultato trovato",
    no_results_desc: "Controlla l'ortografia o prova parole chiave più generali.",
  },
  ja: {
    nav_about: "概要",
    nav_privacy: "プライバシー",
    search_placeholder: "自由なウェブを検索...",
    search_btn: "Senda 検索",
    lucky_btn: "自由なウェブを探索",
    tab_web: "すべて",
    tab_images: "画像",
    tab_news: "ニュース",
    tab_library: "ライブラリ",
    results_found: "件の検索結果 (",
    no_results_title: "一致する結果が見つかりませんでした",
    no_results_desc: "スペルを確認するか、より一般的なキーワードをお試しください。",
  },
  zh: {
    nav_about: "关于",
    nav_privacy: "隐私政策",
    search_placeholder: "在自由网络中搜索...",
    search_btn: "Senda 搜索",
    lucky_btn: "探索自由网络",
    tab_web: "全部",
    tab_images: "图片",
    tab_news: "资讯",
    tab_library: "文献库",
    results_found: "条结果 (",
    no_results_title: "未找到符合条件的结果",
    no_results_desc: "请检查拼写或尝试使用更通用的关键词。",
  }
};

/**
 * Apply localized translations to elements with data-i18n.
 */
function applyTranslations(lang) {
  var dict = SENDA_TRANSLATIONS[lang] || SENDA_TRANSLATIONS.es;
  document.querySelectorAll("[data-i18n]").forEach(function(el) {
    var key = el.getAttribute("data-i18n");
    if (dict[key]) {
      if (el.tagName === "INPUT" && el.hasAttribute("placeholder")) {
        el.setAttribute("placeholder", dict[key]);
      } else {
        el.textContent = dict[key];
      }
    }
  });
  document.documentElement.setAttribute("lang", lang);
}

/**
 * Theme Manager: Toggle light/dark/auto themes with localStorage.
 */
function initThemeManager() {
  var toggleBtn = document.getElementById('themeToggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', function() {
    var current = document.documentElement.getAttribute('data-theme') || 'auto';
    var next = 'dark';
    if (current === 'dark') {
      next = 'light';
    } else if (current === 'light') {
      next = 'auto';
    }
    document.documentElement.setAttribute('data-theme', next);
    try {
      localStorage.setItem('senda_theme', next);
    } catch(e) {}
  });
}

/**
 * Search Input Clear Button
 */
function initSearchBox() {
  var searchInput = document.getElementById('search-input');
  var clearBtn = document.getElementById('clearSearchBtn');

  if (searchInput && clearBtn) {
    function toggleClear() {
      clearBtn.style.display = searchInput.value.trim().length > 0 ? 'inline-flex' : 'none';
    }
    searchInput.addEventListener('input', toggleClear);
    toggleClear();

    clearBtn.addEventListener('click', function() {
      searchInput.value = '';
      toggleClear();
      searchInput.focus();
    });
  }
}

// Lifecycle Initialization
document.addEventListener("DOMContentLoaded", function() {
  var selector = document.getElementById("langSelector");
  var userLang = (navigator.language || navigator.userLanguage || "es").slice(0, 2);
  var initialLang = SENDA_TRANSLATIONS[userLang] ? userLang : "es";

  try {
    var storedLang = localStorage.getItem("senda_lang");
    if (storedLang && SENDA_TRANSLATIONS[storedLang]) {
      initialLang = storedLang;
    }
  } catch (e) {}

  if (selector) {
    selector.value = initialLang;
    selector.addEventListener("change", function(e) {
      var selected = e.target.value;
      try {
        localStorage.setItem("senda_lang", selected);
      } catch (err) {}
      applyTranslations(selected);
    });
  }

  applyTranslations(initialLang);
  initThemeManager();
  initSearchBox();
});

// @license-end
