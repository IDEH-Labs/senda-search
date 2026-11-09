// @license magnet:?xt=urn:btih:1f739d935de45e38526949e2bee45099c10f745f&dn=gpl-3.0.txt GPL-v3.0-or-later
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

/**
 * Senda Client Core (Minimalist i18n, Theme Manager, Keyboard Navigation)
 * Zero tracking, zero telemetry, zero cookies. 100% Client-Side.
 * GNU LibreJS Compliant: Declared Free Software under GNU GPL-3.0-or-later.
 */

const SENDA_TRANSLATIONS = {
  es: {
    nav_home: "Buscar",
    nav_about: "Acerca de",
    nav_privacy: "Privacidad",
    hero_title: "Senda",
    hero_subtitle: "Buscador libre, ético y sin rastreo para la web abierta.",
    search_placeholder: "Escribe para buscar...",
    search_btn: "Buscar",
    tab_web: "Web",
    tab_news: "Noticias",
    tab_images: "Imágenes",
    tab_library: "Biblioteca",
    pill_no_logs: "Cero Registros",
    pill_no_tracking: "Cero Rastreo",
    pill_no_cookies: "Cero Cookies",
    pill_fsf: "Software Libre",
    results_found: "resultados (",
    results_page: "Página",
    results_of: "de",
    no_results_title: "No se encontraron resultados",
    no_results_desc: "Revisa la ortografía o intenta con términos más generales.",
    footer_text: "Senda es software libre bajo la licencia GNU GPL-3.0-o-posterior.",
    skip_to_content: "Saltar al contenido principal",
    copied: "¡Copiado!",
  },
  en: {
    nav_home: "Search",
    nav_about: "About",
    nav_privacy: "Privacy",
    hero_title: "Senda",
    hero_subtitle: "Libre, ethical, and tracker-free search for the open web.",
    search_placeholder: "Type to search...",
    search_btn: "Search",
    tab_web: "Web",
    tab_news: "News",
    tab_images: "Images",
    tab_library: "Library",
    pill_no_logs: "Zero Logs",
    pill_no_tracking: "Zero Tracking",
    pill_no_cookies: "Zero Cookies",
    pill_fsf: "Free Software",
    results_found: "results (",
    results_page: "Page",
    results_of: "of",
    no_results_title: "No results matched your query",
    no_results_desc: "Check your spelling or try more general terms.",
    footer_text: "Senda is free software governed by the GNU GPL-3.0-or-later license.",
    skip_to_content: "Skip to content",
    copied: "Copied!",
  },
  fr: {
    nav_home: "Rechercher",
    nav_about: "À propos",
    nav_privacy: "Confidentialité",
    hero_title: "Senda",
    hero_subtitle: "Moteur de recherche libre, éthique et sans pistage pour le web ouvert.",
    search_placeholder: "Tapez pour rechercher...",
    search_btn: "Rechercher",
    tab_web: "Web",
    tab_news: "Actualités",
    tab_images: "Images",
    tab_library: "Bibliothèque",
    pill_no_logs: "Zéro Journal",
    pill_no_tracking: "Zéro Pistage",
    pill_no_cookies: "Zéro Cookies",
    pill_fsf: "Logiciel Libre",
    results_found: "résultats (",
    results_page: "Page",
    results_of: "sur",
    no_results_title: "Aucun résultat trouvé",
    no_results_desc: "Vérifiez l'orthographe ou essayez des termes plus généraux.",
    footer_text: "Senda est un logiciel libre protégé par la licence GNU GPL-3.0-or-later.",
    skip_to_content: "Aller au contenu",
    copied: "Copié !",
  },
  de: {
    nav_home: "Suche",
    nav_about: "Über uns",
    nav_privacy: "Datenschutz",
    hero_title: "Senda",
    hero_subtitle: "Freie, ethische und trackerfreie Suchmaschine für das offene Web.",
    search_placeholder: "Suchbegriff eingeben...",
    search_btn: "Suchen",
    tab_web: "Web",
    tab_news: "Nachrichten",
    tab_images: "Bilder",
    tab_library: "Bibliothek",
    pill_no_logs: "Keine Logs",
    pill_no_tracking: "Kein Tracking",
    pill_no_cookies: "Keine Cookies",
    pill_fsf: "Freie Software",
    results_found: "Ergebnisse (",
    results_page: "Seite",
    results_of: "von",
    no_results_title: "Keine Ergebnisse gefunden",
    no_results_desc: "Prüfen Sie die Schreibweise oder verwenden Sie allgemeinere Begriffe.",
    footer_text: "Senda ist freie Software unter der GNU GPL-3.0-or-later Lizenz.",
    skip_to_content: "Zum Inhalt springen",
    copied: "Kopiert!",
  },
  pt: {
    nav_home: "Pesquisar",
    nav_about: "Sobre",
    nav_privacy: "Privacidade",
    hero_title: "Senda",
    hero_subtitle: "Buscador livre, ético e sem rastreamento para a web aberta.",
    search_placeholder: "Digite para pesquisar...",
    search_btn: "Pesquisar",
    tab_web: "Web",
    tab_news: "Notícias",
    tab_images: "Imagens",
    tab_library: "Biblioteca",
    pill_no_logs: "Sem Logs",
    pill_no_tracking: "Sem Rastreamento",
    pill_no_cookies: "Zero Cookies",
    pill_fsf: "Software Livre",
    results_found: "resultados (",
    results_page: "Página",
    results_of: "de",
    no_results_title: "Nenhum resultado encontrado",
    no_results_desc: "Verifique a ortografia ou use termos mais gerais.",
    footer_text: "O Senda é um software livre sob a licença GNU GPL-3.0-or-later.",
    skip_to_content: "Pular para o conteúdo",
    copied: "Copiado!",
  },
  it: {
    nav_home: "Cerca",
    nav_about: "Info",
    nav_privacy: "Privacy",
    hero_title: "Senda",
    hero_subtitle: "Motore di ricerca libero, etico e senza tracciamento per il web aperto.",
    search_placeholder: "Scrivi per cercare...",
    search_btn: "Cerca",
    tab_web: "Web",
    tab_news: "Notizie",
    tab_images: "Immagini",
    tab_library: "Biblioteca",
    pill_no_logs: "Nessun Log",
    pill_no_tracking: "Nessun Tracciamento",
    pill_no_cookies: "Zero Cookie",
    pill_fsf: "Software Libero",
    results_found: "risultati (",
    results_page: "Pagina",
    results_of: "di",
    no_results_title: "Nessun risultato trovato",
    no_results_desc: "Controlla l'ortografia o prova termini più generali.",
    footer_text: "Senda è software libero regolato dalla licenza GNU GPL-3.0-or-later.",
    skip_to_content: "Salta al contenuto",
    copied: "Copiato!",
  },
  ja: {
    nav_home: "検索",
    nav_about: "概要",
    nav_privacy: "プライバシー",
    hero_title: "Senda",
    hero_subtitle: "オープンウェブのための自由で倫理的な検索エンジン。",
    search_placeholder: "検索キーワードを入力...",
    search_btn: "検索",
    tab_web: "ウェブ",
    tab_news: "ニュース",
    tab_images: "画像",
    tab_library: "ライブラリ",
    pill_no_logs: "ログなし",
    pill_no_tracking: "追跡なし",
    pill_no_cookies: "クッキーなし",
    pill_fsf: "自由ソフトウェア",
    results_found: "件の検索結果 (",
    results_page: "ページ",
    results_of: "/",
    no_results_title: "一致する結果が見つかりませんでした",
    no_results_desc: "スペルを確認するか、より一般的なキーワードをお試しください。",
    footer_text: "SendaはGNU GPL-3.0以降に基づく自由ソフトウェアです。",
    skip_to_content: "コンテンツへスキップ",
    copied: "コピーしました！",
  },
  zh: {
    nav_home: "搜索",
    nav_about: "关于",
    nav_privacy: "隐私政策",
    hero_title: "Senda",
    hero_subtitle: "面向开放网络的自由、合乎道德且无追踪的搜索引擎。",
    search_placeholder: "输入关键词搜索...",
    search_btn: "搜索",
    tab_web: "网页",
    tab_news: "资讯",
    tab_images: "图片",
    tab_library: "文献库",
    pill_no_logs: "零日志",
    pill_no_tracking: "零追踪",
    pill_no_cookies: "零 Cookies",
    pill_fsf: "自由软件",
    results_found: "条结果 (",
    results_page: "第",
    results_of: "页，共",
    no_results_title: "未找到符合条件的搜索结果",
    no_results_desc: "请检查拼写或尝试使用更通用的搜索词。",
    footer_text: "Senda 是受 GNU GPL-3.0 或更高版本许可证管辖的自由软件。",
    skip_to_content: "跳转至主要内容",
    copied: "已复制！",
  }
};

/**
 * Set active vertical category in homepage search form.
 */
function setCategory(cat, btn) {
  var catInput = document.getElementById('search-category');
  if (catInput) {
    catInput.value = cat;
  }
  document.querySelectorAll('.category-tabs .category-tab').forEach(function(el) {
    el.classList.remove('active');
    el.setAttribute('aria-selected', 'false');
  });
  if (btn) {
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
  }
}

/**
 * Apply localized translations to all elements with data-i18n.
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
 * Theme Manager: Toggle and store light/dark/auto themes.
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
 * Keyboard Navigation for Power Users (j, k, /, Enter, Escape)
 */
function initKeyboardNavigation() {
  var searchInput = document.getElementById('search-input');
  var clearBtn = document.getElementById('clearSearchBtn');
  var resultCards = Array.from(document.querySelectorAll('.result-card'));
  var activeCardIndex = -1;

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

  window.addEventListener('keydown', function(e) {
    var isInputActive = document.activeElement === searchInput || 
                        document.activeElement.tagName === 'INPUT' || 
                        document.activeElement.tagName === 'TEXTAREA' || 
                        document.activeElement.tagName === 'SELECT';

    if (!isInputActive && (e.key === '/' || ((e.ctrlKey || e.metaKey) && e.key === 'k'))) {
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
      return;
    }

    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.blur();
      return;
    }

    if (!isInputActive && resultCards.length > 0) {
      if (e.key === 'j' || e.key === 'ArrowDown') {
        e.preventDefault();
        if (activeCardIndex < resultCards.length - 1) {
          activeCardIndex++;
          updateActiveCard();
        }
      } else if (e.key === 'k' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (activeCardIndex > 0) {
          activeCardIndex--;
          updateActiveCard();
        }
      } else if (e.key === 'Enter' && activeCardIndex >= 0) {
        var card = resultCards[activeCardIndex];
        var link = card ? card.querySelector('.result-title') : null;
        if (link) {
          window.open(link.href, '_blank', 'noopener,noreferrer');
        }
      }
    }
  });

  function updateActiveCard() {
    resultCards.forEach(function(card, idx) {
      if (idx === activeCardIndex) {
        card.classList.add('keyboard-active');
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        card.classList.remove('keyboard-active');
      }
    });
  }
}

/**
 * Copy URL Buttons on Search Results
 */
function initCopyButtons() {
  document.querySelectorAll('.copy-url-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      var url = btn.getAttribute('data-copy-url');
      if (url && navigator.clipboard) {
        navigator.clipboard.writeText(url).then(function() {
          var originalHtml = btn.innerHTML;
          btn.innerHTML = '<span style="font-size:0.75rem; font-weight:700; color:var(--text-accent)">✓</span>';
          setTimeout(function() {
            btn.innerHTML = originalHtml;
          }, 1500);
        });
      }
    });
  });
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
  initKeyboardNavigation();
  initCopyButtons();
});

// @license-end
