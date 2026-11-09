// @license magnet:?xt=urn:btih:1f739d935de45e38526949e2bee45099c10f745f&dn=gpl-3.0.txt GPL-v3.0-or-later
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

/**
 * Senda Sovereign Client Core (i18n, Theme Manager, Keyboard Navigation)
 * Zero tracking, zero telemetry, zero cookies. 100% Client-Side.
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
    footer_text: "Senda is sovereign, libre software governed by the GNU GPL-3.0-or-later license.",
    skip_to_content: "Skip to content",
    copied: "Copied!",
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
    pill_no_tracking: "Cero Perfiles",
    pill_no_cookies: "Cero Cookies",
    pill_fsf: "100% Software Libre",
    results_found: "resultados encontrados en",
    results_page: "Página",
    results_of: "de",
    no_results_title: "No se encontraron resultados para tu consulta",
    no_results_desc: "Revisa la ortografía, usa términos más generales o incorpora nuevos sitios al índice del rastreador.",
    footer_text: "Senda es software soberano y libre amparado por la licencia GNU GPL-3.0-o-posterior.",
    skip_to_content: "Saltar al contenido principal",
    copied: "¡Copiado!",
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
    pill_no_tracking: "Zéro Profilage",
    pill_no_cookies: "Zéro Cookies",
    pill_fsf: "100% Logiciel Libre",
    results_found: "résultats trouvés en",
    results_page: "Page",
    results_of: "sur",
    no_results_title: "Aucun résultat trouvé pour votre requête",
    no_results_desc: "Vérifiez l'orthographe, utilisez des termes plus généraux ou indexez de nouveaux sites.",
    footer_text: "Senda est un logiciel souverain et libre protégé par la licence GNU GPL-3.0-or-later.",
    skip_to_content: "Aller au contenu",
    copied: "Copié !",
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
    pill_no_tracking: "Kein Profiling",
    pill_no_cookies: "Keine Cookies",
    pill_fsf: "100% Freie Software",
    results_found: "Ergebnisse gefunden in",
    results_page: "Seite",
    results_of: "von",
    no_results_title: "Keine Ergebnisse für Ihre Suchanfrage",
    no_results_desc: "Prüfen Sie die Schreibweise oder verwenden Sie allgemeinere Begriffe.",
    footer_text: "Senda ist souveräne freie Software unter der GNU GPL-3.0-or-later Lizenz.",
    skip_to_content: "Zum Inhalt springen",
    copied: "Kopiert!",
  },
  pt: {
    brand_sub: "Busca Soberana",
    nav_home: "Pesquisar",
    nav_about: "Sobre",
    nav_privacy: "Privacidade",
    hero_title: "Senda",
    hero_subtitle: "Motor de busca independente, ético e verificável. Software livre sob GPL-3.0.",
    search_placeholder: "Explore a web soberana...",
    search_btn: "Pesquisar",
    tab_web: "Web",
    tab_news: "Notícias",
    tab_images: "Imagens",
    tab_library: "Biblioteca",
    pill_no_logs: "Sem Registros",
    pill_no_tracking: "Sem Rastreamento",
    pill_no_cookies: "Zero Cookies",
    pill_fsf: "100% Software Livre",
    results_found: "resultados encontrados em",
    results_page: "Página",
    results_of: "de",
    no_results_title: "Nenhum resultado encontrado",
    no_results_desc: "Verifique a ortografia ou use termos mais gerais.",
    footer_text: "O Senda é um software livre e soberano sob a licença GNU GPL-3.0-or-later.",
    skip_to_content: "Pular para o conteúdo",
    copied: "Copiado!",
  },
  it: {
    brand_sub: "Ricerca Sovrana",
    nav_home: "Cerca",
    nav_about: "Info",
    nav_privacy: "Privacy",
    hero_title: "Senda",
    hero_subtitle: "Motore di ricerca indipendente, etico e verificabile. Software libero sotto licenza GPL-3.0.",
    search_placeholder: "Esplora il web sovrano...",
    search_btn: "Cerca",
    tab_web: "Web",
    tab_news: "Notizie",
    tab_images: "Immagini",
    tab_library: "Biblioteca",
    pill_no_logs: "Nessun Registro",
    pill_no_tracking: "Nessuna Profilazione",
    pill_no_cookies: "Zero Cookie",
    pill_fsf: "100% Software Libero",
    results_found: "risultati trovati in",
    results_page: "Pagina",
    results_of: "di",
    no_results_title: "Nessun risultato trovato",
    no_results_desc: "Controlla l'ortografia o prova termini più generali.",
    footer_text: "Senda è software sovrano e libero regolato dalla licenza GNU GPL-3.0-or-later.",
    skip_to_content: "Salta al contenuto",
    copied: "Copiato!",
  },
  ja: {
    brand_sub: "主権型検索エンジン",
    nav_home: "検索",
    nav_about: "概要",
    nav_privacy: "プライバシー",
    hero_title: "Senda",
    hero_subtitle: "独立・倫理的・検証可能なウェブ検索エンジン。GPL-3.0に基づく自由ソフトウェア。",
    search_placeholder: "主権型ウェブを探索...",
    search_btn: "検索",
    tab_web: "ウェブ",
    tab_news: "ニュース",
    tab_images: "画像",
    tab_library: "ライブラリ",
    pill_no_logs: "クエリログなし",
    pill_no_tracking: "トラッキングなし",
    pill_no_cookies: "クッキーなし",
    pill_fsf: "100% 自由ソフトウェア",
    results_found: "件の検索結果（所要時間：",
    results_page: "ページ",
    results_of: "/",
    no_results_title: "一致する結果が見つかりませんでした",
    no_results_desc: "スペルを確認するか、より一般的なキーワードをお試しください。",
    footer_text: "SendaはGNU GPL-3.0以降のライセンスに基づく主権型自由ソフトウェアです。",
    skip_to_content: "コンテンツへスキップ",
    copied: "コピーしました！",
  },
  zh: {
    brand_sub: "主权搜索引擎",
    nav_home: "搜索",
    nav_about: "关于",
    nav_privacy: "隐私政策",
    hero_title: "Senda",
    hero_subtitle: "独立、合乎道德且可验证的网络搜索引擎。基于 GPL-3.0 的自由软件。",
    search_placeholder: "探索主权网络...",
    search_btn: "搜索",
    tab_web: "网页",
    tab_news: "资讯",
    tab_images: "图片",
    tab_library: "文献库",
    pill_no_logs: "零查询日志",
    pill_no_tracking: "零数据画像",
    pill_no_cookies: "零 Cookies",
    pill_fsf: "100% 自由软件",
    results_found: "条结果，耗时",
    results_page: "第",
    results_of: "页，共",
    no_results_title: "未找到符合条件的搜索结果",
    no_results_desc: "请检查拼写或尝试使用更通用的搜索词。",
    footer_text: "Senda 是受 GNU GPL-3.0 或更高版本许可证管辖的主权自由软件。",
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
  var dict = SENDA_TRANSLATIONS[lang] || SENDA_TRANSLATIONS.en;
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

  // Clear button logic
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

  // Global Keydown Listeners
  window.addEventListener('keydown', function(e) {
    var isInputActive = document.activeElement === searchInput || 
                        document.activeElement.tagName === 'INPUT' || 
                        document.activeElement.tagName === 'TEXTAREA' || 
                        document.activeElement.tagName === 'SELECT';

    // Focus search on '/' or Ctrl+K / Cmd+K
    if (!isInputActive && (e.key === '/' || ((e.ctrlKey || e.metaKey) && e.key === 'k'))) {
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
      return;
    }

    // Escape unfocuses search
    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.blur();
      return;
    }

    // Results navigation: j (down), k (up)
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
          btn.innerHTML = '<span style="font-size:0.75rem; font-weight:700; color:var(--brand-primary)">✓</span>';
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
  // 1. Language selector setup
  var selector = document.getElementById("langSelector");
  var userLang = (navigator.language || navigator.userLanguage || "en").slice(0, 2);
  var initialLang = SENDA_TRANSLATIONS[userLang] ? userLang : "en";

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

  // 2. Initialize Theme, Keyboard navigation, and Copy actions
  initThemeManager();
  initKeyboardNavigation();
  initCopyButtons();
});

// @license-end
