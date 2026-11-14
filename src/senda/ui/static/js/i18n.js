// @license magnet:?xt=urn:btih:1f739d935de45e38526949e2bee45099c10f745f&dn=gpl-3.0.txt GPL-v3.0-or-later
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

/**
 * Senda Sovereign Client Core
 * Multi-Language, Theme Manager, Density Toggle, Why-Seen Dialog.
 * Zero telemetry, zero tracking, zero third-party cookies. Free Software under GNU GPL-3.0-or-later.
 */

const SENDA_TRANSLATIONS = {
  es: {
    nav_about: "Acerca de",
    nav_privacy: "Privacidad",
    nav_javascript: "JavaScript y licencias",
    search_placeholder: "Buscar en la web libre...",
    tab_web: "Web",
    tab_images: "Imágenes",
    tab_news: "Noticias",
    tab_videos: "Videos",
    tab_library: "Biblioteca",
    results_found: "resultados (",
    no_results_title: "No se encontraron resultados",
    no_results_desc: "Comprueba la ortografía o intenta con términos más generales.",
    footer_add_browser: "Añadir a mi navegador",
    footer_libre_code: "Código Libre (GPLv3+)",
  },
  en: {
    nav_about: "About",
    nav_privacy: "Privacy",
    nav_javascript: "JavaScript & Licenses",
    search_placeholder: "Search the libre web...",
    tab_web: "Web",
    tab_images: "Images",
    tab_news: "News",
    tab_videos: "Videos",
    tab_library: "Library",
    results_found: "results (",
    no_results_title: "No results found",
    no_results_desc: "Check your spelling or try more general keywords.",
    footer_add_browser: "Add to my browser",
    footer_libre_code: "Free Software (GPLv3+)",
  },
  fr: {
    nav_about: "À propos",
    nav_privacy: "Confidentialité",
    nav_javascript: "JavaScript et licences",
    search_placeholder: "Rechercher sur le web libre...",
    tab_web: "Web",
    tab_images: "Images",
    tab_news: "Actualités",
    tab_videos: "Vidéos",
    tab_library: "Bibliothèque",
    results_found: "résultats (",
    no_results_title: "Aucun résultat trouvé",
    no_results_desc: "Vérifiez l'orthographe ou essayez des mots-clés plus généraux.",
    footer_add_browser: "Ajouter à mon navigateur",
    footer_libre_code: "Logiciel Libre (GPLv3+)",
  },
  de: {
    nav_about: "Über uns",
    nav_privacy: "Datenschutz",
    nav_javascript: "JavaScript & Lizenzen",
    search_placeholder: "Im freien Web suchen...",
    tab_web: "Web",
    tab_images: "Bilder",
    tab_news: "Nachrichten",
    tab_videos: "Videos",
    tab_library: "Bibliothek",
    results_found: "Ergebnisse (",
    no_results_title: "Keine Ergebnisse gefunden",
    no_results_desc: "Prüfen Sie die Schreibweise oder versuchen Sie allgemeinere Suchbegriffe.",
    footer_add_browser: "Zu meinem Browser hinzufügen",
    footer_libre_code: "Freie Software (GPLv3+)",
  },
  pt: {
    nav_about: "Sobre",
    nav_privacy: "Privacidade",
    nav_javascript: "JavaScript e licenças",
    search_placeholder: "Pesquisar na web livre...",
    tab_web: "Web",
    tab_images: "Imagens",
    tab_news: "Notícias",
    tab_videos: "Vídeos",
    tab_library: "Biblioteca",
    results_found: "resultados (",
    no_results_title: "Nenhum resultado encontrado",
    no_results_desc: "Verifique a ortografia ou tente palavras-chave mais gerais.",
    footer_add_browser: "Adicionar ao meu navegador",
    footer_libre_code: "Código Livre (GPLv3+)",
  },
  it: {
    nav_about: "Info",
    nav_privacy: "Privacy",
    nav_javascript: "JavaScript e licenze",
    search_placeholder: "Cerca nel web libero...",
    tab_web: "Web",
    tab_images: "Immagini",
    tab_news: "Notizie",
    tab_videos: "Video",
    tab_library: "Biblioteca",
    results_found: "risultati (",
    no_results_title: "Nessun risultato trovato",
    no_results_desc: "Controlla l'ortografia o prova parole chiave più generali.",
    footer_add_browser: "Aggiungi al mio browser",
    footer_libre_code: "Software Libero (GPLv3+)",
  },
  ja: {
    nav_about: "概要",
    nav_privacy: "プライバシー",
    nav_javascript: "JavaScript とライセンス",
    search_placeholder: "自由なウェブを検索...",
    tab_web: "ウェブ",
    tab_images: "画像",
    tab_news: "ニュース",
    tab_videos: "動画",
    tab_library: "ライブラリ",
    results_found: "件の検索結果 (",
    no_results_title: "一致する結果が見つかりませんでした",
    no_results_desc: "スペルを確認するか、より一般的なキーワードをお試しください。",
    footer_add_browser: "ブラウザに追加",
    footer_libre_code: "自由ソフトウェア (GPLv3+)",
  },
  zh: {
    nav_about: "关于",
    nav_privacy: "隐私政策",
    nav_javascript: "JavaScript 与许可证",
    search_placeholder: "在自由网络中搜索...",
    tab_web: "网页",
    tab_images: "图片",
    tab_news: "资讯",
    tab_videos: "视频",
    tab_library: "文献库",
    results_found: "条结果 (",
    no_results_title: "未找到符合条件的结果",
    no_results_desc: "请检查拼写或尝试使用更通用的关键词。",
    footer_add_browser: "添加至浏览器",
    footer_libre_code: "自由软件源码 (GPLv3+)",
  },
  ru: {
    nav_about: "О проекте",
    nav_privacy: "Конфиденциальность",
    nav_javascript: "JavaScript и лицензии",
    search_placeholder: "Поиск в свободной сети...",
    tab_web: "Веб",
    tab_images: "Изображения",
    tab_news: "Новости",
    tab_videos: "Видео",
    tab_library: "Библиотека",
    results_found: "результатов (",
    no_results_title: "Ничего не найдено",
    no_results_desc: "Проверьте правописание или используйте более общие ключевые слова.",
    footer_add_browser: "Добавить в браузер",
    footer_libre_code: "Свободный код (GPLv3+)",
  },
  ar: {
    nav_about: "حول",
    nav_privacy: "الخصوصية",
    nav_javascript: "جافاسكريبت والتراخيص",
    search_placeholder: "ابحث في الويب الحر...",
    tab_web: "ويب",
    tab_images: "صور",
    tab_news: "أخبار",
    tab_videos: "فيديوهات",
    tab_library: "المكتبة",
    results_found: "نتائج (",
    no_results_title: "لم يتم العثور على نتائج",
    no_results_desc: "تحقق من الإملاء أو جرب كلمات مفتاحية أكثر عمومية.",
    footer_add_browser: "إضافة إلى متصفحي",
    footer_libre_code: "برمجيات حرة (GPLv3+)",
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
 * Tor & Privacy Sandbox Storage Guards
 */
function safeGetStorage(key) {
  try {
    return localStorage.getItem(key);
  } catch (e) {
    return null;
  }
}

function safeSetStorage(key, val) {
  try {
    localStorage.setItem(key, val);
  } catch (e) {}
}

/**
 * Theme Manager: Toggle light/dark themes with dual-layer fallback.
 * Works with or without JavaScript enabled.
 */
function initThemeManager() {
  var toggleBtn = document.getElementById('themeToggle');
  if (!toggleBtn) return;

  function updateToggleState(theme) {
    var next = theme === 'dark' ? 'light' : 'dark';
    try {
      var currentUrl = new URL(window.location.href);
      currentUrl.searchParams.set('theme', next);
      toggleBtn.setAttribute('href', currentUrl.pathname + currentUrl.search);
    } catch(e) {
      toggleBtn.setAttribute('href', '?theme=' + next);
    }
    toggleBtn.setAttribute('title', next === 'dark' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro');
    toggleBtn.setAttribute('aria-label', next === 'dark' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro');

    // Update hidden inputs in search forms
    document.querySelectorAll('input[name="theme"]').forEach(function(inp) {
      inp.value = theme;
    });

    // Update all internal links that carry theme parameter (tabs, filters, pagination)
    document.querySelectorAll('a[href*="theme="]').forEach(function(link) {
      if (link === toggleBtn) return;
      try {
        var href = link.getAttribute('href');
        if (href && (href.startsWith('/') || href.startsWith('?'))) {
          var targetUrl = new URL(href, window.location.origin);
          targetUrl.searchParams.set('theme', theme);
          link.setAttribute('href', targetUrl.pathname + targetUrl.search);
        }
      } catch (err) {}
    });

    // Synchronize browser address bar so F5 / reload preserves the chosen theme
    try {
      if (window.history && window.history.replaceState) {
        var u = new URL(window.location.href);
        if (u.searchParams.get('theme') !== theme) {
          u.searchParams.set('theme', theme);
          window.history.replaceState(null, '', u.pathname + u.search);
        }
      }
    } catch(err) {}
  }

  toggleBtn.addEventListener('click', function(e) {
    e.preventDefault();
    var current = document.documentElement.getAttribute('data-theme') || 'dark';
    var next = current === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', next);
    if (next === 'light') {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
      document.documentElement.classList.add('dark');
    }

    safeSetStorage('senda_theme', next);

    // Set functional cookie for zero-JS fallback continuity
    try {
      document.cookie = "senda_theme=" + next + ";path=/;max-age=31536000;SameSite=Lax";
    } catch (err) {}

    updateToggleState(next);
  });

  // Initial sync with current DOM theme
  var initial = document.documentElement.getAttribute('data-theme') || 'dark';
  updateToggleState(initial);
}

/**
 * Sovereign Dropdown & Accessible Filter Manager
 * - Closes dropdowns on Escape key press (with focus restore to summary)
 * - Closes dropdowns on Outside Click
 * - Automatically closes other open dropdowns when one opens (mutual exclusion)
 * - Autofocuses country filter input when Region dropdown opens
 * - Client-side instant filter for countries and ISO codes
 * - Zero JS fallback: standard HTML <details> native behavior is preserved
 * - Free Software under GNU GPL-3.0-or-later.
 */
window.selectCategory = function(cat, btn) {
  var input = document.getElementById('search-category');
  if (input) input.value = cat;
  document.querySelectorAll('.cat-chip').forEach(function(el) {
    el.classList.remove('active');
  });
  if (btn) btn.classList.add('active');
};

function initDropdownsAndFilters() {
  var dropdowns = document.querySelectorAll('.filter-dropdown, .why-seen-disclosure');

  var backdrop = document.getElementById('filterBackdrop');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.id = 'filterBackdrop';
    backdrop.className = 'filter-backdrop';
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.appendChild(backdrop);
  }

  function updateBackdrop() {
    var anyOpen = document.querySelector('.filter-dropdown[open], .why-seen-disclosure[open], details.lang-picker[open], details.opensearch-details[open]');
    if (anyOpen) {
      document.body.classList.add('dropdown-open');
    } else {
      document.body.classList.remove('dropdown-open');
    }
  }

  function resetMenuPosition(d) {
    var menu = d.querySelector('.filter-dropdown-menu, .why-seen-dropdown');
    if (menu) {
      menu.style.left = '';
      menu.style.right = '';
      menu.style.top = '';
      menu.style.bottom = '';
      menu.style.transform = '';
    }
  }

  function closeAllDropdowns(except) {
    var allOpen = document.querySelectorAll('.filter-dropdown[open], .why-seen-disclosure[open], details.lang-picker[open], details.opensearch-details[open]');
    allOpen.forEach(function(d) {
      if (d !== except) {
        d.removeAttribute('open');
        d.open = false;
        if (d.classList.contains('why-seen-disclosure')) {
          var c = d.closest('.result-card');
          if (c) c.classList.remove('has-open-why-seen');
        }
        resetMenuPosition(d);
      }
    });
    updateBackdrop();
  }

  function adjustMenuBoundary(d) {
    var menu = d.querySelector('.filter-dropdown-menu, .why-seen-dropdown');
    if (!menu) return;

    var viewportWidth = window.innerWidth || document.documentElement.clientWidth;
    var viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    // On mobile screens (<= 640px), dropdowns are anchored full-width / in-flow via CSS
    if (viewportWidth <= 640) {
      menu.style.left = '';
      menu.style.right = '';
      menu.style.top = '';
      menu.style.bottom = '';
      menu.style.transform = '';
      return;
    }

    menu.style.left = '';
    menu.style.right = '';
    menu.style.top = '';
    menu.style.bottom = '';
    menu.style.transform = '';

    var rect = menu.getBoundingClientRect();

    // If menu extends beyond right edge, align right edge to button
    if (rect.right > viewportWidth - 16) {
      menu.style.left = 'auto';
      menu.style.right = '0';
    }

    // If after alignment it extends beyond left edge (left < 16), shift it right
    var updatedRect = menu.getBoundingClientRect();
    if (updatedRect.left < 16) {
      var shift = 16 - updatedRect.left;
      menu.style.transform = 'translateX(' + shift + 'px)';
    }

    // If panel extends below viewport, check if flipping upwards provides better visibility
    if (updatedRect.bottom > viewportHeight - 16) {
      var btnRect = d.getBoundingClientRect();
      if (btnRect.top > (viewportHeight - btnRect.bottom)) {
        menu.style.top = 'auto';
        menu.style.bottom = 'calc(100% + 6px)';
      }
    }
  }

  // Handle dropdown open toggle for mutual exclusion, boundary adjustment, and autofocus
  dropdowns.forEach(function(d) {
    d.addEventListener('toggle', function() {
      if (d.open) {
        closeAllDropdowns(d);
        adjustMenuBoundary(d);
        updateBackdrop();

        if (d.classList.contains('why-seen-disclosure')) {
          var card = d.closest('.result-card');
          if (card) card.classList.add('has-open-why-seen');
        }

        var searchInput = d.querySelector('.country-search-input');
        if (searchInput) {
          setTimeout(function() {
            searchInput.focus();
          }, 50);
        }
      } else {
        if (d.classList.contains('why-seen-disclosure')) {
          var c = d.closest('.result-card');
          if (c) c.classList.remove('has-open-why-seen');
        }
        resetMenuPosition(d);
        updateBackdrop();
      }
    });
  });

  // Also coordinate lang-picker and opensearch details
  document.querySelectorAll('details.lang-picker, details.opensearch-details').forEach(function(d) {
    d.addEventListener('toggle', function() {
      if (d.open) {
        closeAllDropdowns(d);
        updateBackdrop();
      } else {
        updateBackdrop();
      }
    });
  });

  // Keep open dropdown inside viewport on screen orientation / resize
  window.addEventListener('resize', function() {
    dropdowns.forEach(function(d) {
      if (d.open) {
        adjustMenuBoundary(d);
      }
    });
  });

  // Dismiss open dropdowns immediately upon outside touch or click
  function handleOutside(e) {
    var target = e.target;
    var el = target && target.nodeType === 1 ? target : (target ? target.parentElement : null);
    if (!el) return;

    // If click or touch is on backdrop, dismiss all
    if (el === backdrop || el.id === 'filterBackdrop' || el.classList.contains('filter-backdrop')) {
      e.preventDefault();
      closeAllDropdowns(null);
      return;
    }

    var inside = el.closest('.filter-dropdown, .why-seen-disclosure, details.lang-picker, details.opensearch-details');

    var openDropdowns = document.querySelectorAll('.filter-dropdown[open], .why-seen-disclosure[open], details.lang-picker[open], details.opensearch-details[open]');
    if (!openDropdowns || openDropdowns.length === 0) return;

    var anyClosed = false;
    openDropdowns.forEach(function(d) {
      if (d !== inside) {
        d.removeAttribute('open');
        d.open = false;
        resetMenuPosition(d);
        anyClosed = true;
      }
    });

    if (anyClosed) {
      updateBackdrop();
      // If user touched an outside element while closing, unfocus any active inputs
      if (document.activeElement && typeof document.activeElement.blur === 'function') {
        document.activeElement.blur();
      }
    }
  }

  // Dismiss listeners:
  // 1. pointerdown (fires instantaneously on finger touch or mouse press)
  // 2. touchstart (fallback for mobile environments)
  // 3. click (desktop & accessibility fallback)
  if (window.PointerEvent) {
    document.addEventListener('pointerdown', handleOutside, true);
  }
  document.addEventListener('touchstart', handleOutside, { capture: true, passive: true });
  document.addEventListener('click', handleOutside, true);

  if (backdrop) {
    backdrop.addEventListener('pointerdown', function(e) {
      e.preventDefault();
      closeAllDropdowns(null);
    });
    backdrop.addEventListener('touchstart', function(e) {
      e.preventDefault();
      closeAllDropdowns(null);
    });
    backdrop.addEventListener('click', function(e) {
      e.preventDefault();
      closeAllDropdowns(null);
    });
  }

  // Close dropdowns on Escape key press and restore focus to summary
  window.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' || e.key === 'Esc' || e.keyCode === 27) {
      var anyClosed = false;
      var openDropdowns = document.querySelectorAll('.filter-dropdown[open], .why-seen-disclosure[open], details.lang-picker[open], details.opensearch-details[open]');
      openDropdowns.forEach(function(d) {
        d.removeAttribute('open');
        d.open = false;
        resetMenuPosition(d);
        anyClosed = true;
        var summary = d.querySelector('summary');
        if (summary) summary.focus();
      });
      if (anyClosed) {
        updateBackdrop();
        e.preventDefault();
      }
    }
  });

  // Instant client-side filter for all countries and ISO codes
  var countryFilter = document.getElementById('countryQuickFilter');
  if (countryFilter) {
    countryFilter.addEventListener('input', function() {
      var term = this.value.toLowerCase().trim();
      var items = document.querySelectorAll('.country-item');
      var headers = document.querySelectorAll('.country-continent-header');
      items.forEach(function(el) {
        var text = (el.getAttribute('data-country') || el.textContent).toLowerCase();
        el.style.display = text.indexOf(term) !== -1 ? 'flex' : 'none';
      });
      headers.forEach(function(h) {
        h.style.display = term ? 'none' : 'block';
      });
    });

    countryFilter.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && this.value) {
        e.stopPropagation();
        this.value = '';
        this.dispatchEvent(new Event('input'));
      }
    });
  }

  // Category chip switcher buttons on home page
  document.querySelectorAll('.cat-chip').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var cat = this.getAttribute('data-cat') || 'all';
      window.selectCategory(cat, this);
    });
  });

  // Sovereign Calculator copy button
  var calcCopy = document.getElementById('calcCopyBtn');
  if (calcCopy) {
    calcCopy.addEventListener('click', function() {
      var res = this.getAttribute('data-result');
      if (res && navigator.clipboard) {
        var btn = this;
        navigator.clipboard.writeText(res).then(function() {
          var label = btn.querySelector('.copy-label');
          if (label) label.textContent = '¡Copiado!';
          btn.classList.add('copied');
          setTimeout(function() {
            if (label) label.textContent = 'Copiar';
            btn.classList.remove('copied');
          }, 2000);
        });
      }
    });
  }
}

/**
 * Command Bar & Shortcuts
 */
function initCommandBar() {
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

  // Keyboard shortcut '/' or Ctrl+K / Cmd+K to focus search input
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
    }

    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.blur();
    }
  });
}

/**
 * Preferences Manager: Persist all sovereign user preferences in browser localStorage
 * (Theme, Language, Density, Preferred Region/Country, and SafeSearch).
 * Zero tracking, zero telemetry, zero invasive cookies.
 */
function initPreferencesManager() {
  try {
    var savedRegion = localStorage.getItem("senda_region");
    if (savedRegion) {
      document.querySelectorAll('input[name="region"]').forEach(function(inp) {
        if (!inp.value || inp.value === "all") inp.value = savedRegion;
      });
    }

    var savedSafeSearch = localStorage.getItem("senda_safesearch");
    if (savedSafeSearch) {
      document.querySelectorAll('input[name="safe_search"]').forEach(function(inp) {
        if (!inp.value || inp.value === "off") inp.value = savedSafeSearch;
      });
    }
  } catch (e) {}

  // Remember region/country preference when clicked in dropdown
  document.querySelectorAll('.filter-dropdown-item[href*="region="]').forEach(function(item) {
    item.addEventListener('click', function() {
      try {
        var match = this.getAttribute('href').match(/[?&]region=([^&]+)/);
        if (match && match[1]) {
          localStorage.setItem('senda_region', decodeURIComponent(match[1]));
        }
      } catch (err) {}
    });
  });

  // Remember SafeSearch preference when clicked in dropdown
  document.querySelectorAll('.filter-dropdown-item[href*="safe_search="]').forEach(function(item) {
    item.addEventListener('click', function() {
      try {
        var match = this.getAttribute('href').match(/[?&]safe_search=([^&]+)/);
        if (match && match[1]) {
          localStorage.setItem('senda_safesearch', decodeURIComponent(match[1]));
        }
      } catch (err) {}
    });
  });
}

function initOpenSearchInstallation() {
  var btn = document.getElementById("btnInstallOpenSearch");
  if (!btn) return;
  btn.addEventListener("click", function() {
    if (window.external && "AddSearchProvider" in window.external) {
      try {
        window.external.AddSearchProvider("/opensearch.xml");
      } catch (e) {
        alert("En tu navegador, añade Senda haciendo clic derecho en la barra de direcciones y seleccionando 'Añadir motor de búsqueda'.");
      }
    } else {
      alert("En tu navegador, añade Senda haciendo clic derecho en la barra de direcciones y seleccionando 'Añadir motor de búsqueda'.");
    }
  });
}

// Lifecycle Initialization
document.addEventListener("DOMContentLoaded", function() {
  // 1. Resolve active language following standard sovereign priority:
  //    a) Explicit URL query param (?lang=en)
  //    b) Server-rendered document lang (<html lang="en">)
  //    c) Client-side stored preference (localStorage 'senda_lang')
  //    d) Client-side functional cookie ('senda_lang')
  //    e) Browser / device system language (navigator.language)
  //    f) Fallback default ('es')
  var urlParams = new URLSearchParams(window.location.search);
  var urlLang = (urlParams.get("lang") || "").toLowerCase().slice(0, 2);
  var htmlLang = (document.documentElement.getAttribute("lang") || "").toLowerCase().slice(0, 2);
  var storedLang = (safeGetStorage("senda_lang") || "").toLowerCase().slice(0, 2);
  var cookieMatch = document.cookie.match(/(?:^|;\s*)senda_lang=([^;]+)/);
  var cookieLang = cookieMatch ? decodeURIComponent(cookieMatch[1]).toLowerCase().slice(0, 2) : "";
  var navLang = (navigator.language || navigator.userLanguage || "es").toLowerCase().slice(0, 2);

  var activeLang = "es";
  if (urlLang && SENDA_TRANSLATIONS[urlLang]) {
    activeLang = urlLang;
  } else if (htmlLang && SENDA_TRANSLATIONS[htmlLang]) {
    activeLang = htmlLang;
  } else if (storedLang && SENDA_TRANSLATIONS[storedLang]) {
    activeLang = storedLang;
  } else if (cookieLang && SENDA_TRANSLATIONS[cookieLang]) {
    activeLang = cookieLang;
  } else if (navLang && SENDA_TRANSLATIONS[navLang]) {
    activeLang = navLang;
  }

  // Persist resolved language in storage and functional cookie
  safeSetStorage("senda_lang", activeLang);
  document.cookie = "senda_lang=" + activeLang + "; path=/; max-age=31536000; SameSite=Lax";

  // When clicking any language item in the language picker, remember preference immediately
  document.querySelectorAll('.lang-menu-item').forEach(function(item) {
    item.addEventListener('click', function() {
      try {
        var href = this.getAttribute('href');
        var match = href ? href.match(/[?&]lang=([a-zA-Z]{2})/) : null;
        if (match && match[1]) {
          var chosen = match[1].toLowerCase();
          safeSetStorage("senda_lang", chosen);
          document.cookie = "senda_lang=" + chosen + "; path=/; max-age=31536000; SameSite=Lax";
        }
      } catch (err) {}
    });
  });

  applyTranslations(activeLang);
  initThemeManager();
  initPreferencesManager();
  initDropdownsAndFilters();
  initCommandBar();
  initOpenSearchInstallation();
  initWorldTimeLiveClock();
});

/**
 * Live Sovereign World Time Clock
 * Accurately ticks seconds client-side using standard W3C Intl API.
 * 100% offline, zero network telemetry.
 */
function initWorldTimeLiveClock() {
  var clockEl = document.querySelector('.worldtime-clock[data-timezone]');
  if (!clockEl) return;

  var tz = clockEl.getAttribute('data-timezone');
  if (!tz) return;

  var hoursMinsEl = clockEl.querySelector('.worldtime-hours-mins');
  var secondsEl = clockEl.querySelector('.worldtime-seconds');
  var clock12El = clockEl.querySelector('.worldtime-clock-12');

  function tick() {
    try {
      var now = new Date();
      var t24 = now.toLocaleTimeString('en-GB', {
        timeZone: tz,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
      var parts = t24.split(':');
      if (parts.length === 3) {
        if (hoursMinsEl) hoursMinsEl.textContent = parts[0] + ':' + parts[1];
        if (secondsEl) secondsEl.textContent = ':' + parts[2];
      }

      if (clock12El) {
        var t12 = now.toLocaleTimeString('en-US', {
          timeZone: tz,
          hour: 'numeric',
          minute: '2-digit',
          second: '2-digit',
          hour12: true
        });
        clock12El.textContent = t12;
      }
    } catch (e) {
      // Graceful fallback: maintain initial server-rendered time
    }
  }

  tick();
  var delay = 1000 - (new Date().getTime() % 1000);
  setTimeout(function() {
    tick();
    setInterval(tick, 1000);
  }, delay);
}

// @license-end
