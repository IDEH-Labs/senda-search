// @license magnet:?xt=urn:btih:1f739d935de45e38526949e2bee45099c10f745f&dn=gpl-3.0.txt GPL-v3.0-or-later
// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

/**
 * Senda Sovereign Client Core
 * Multi-Language (es-CO, en), Theme Manager, Density Toggle, Why-Seen Dialog.
 * Zero telemetry, zero tracking, zero cookies. 100% Client-Side.
 * GNU LibreJS Compliant: Declared Free Software under GNU GPL-3.0-or-later.
 */

const SENDA_TRANSLATIONS = {
  es: {
    nav_about: "Acerca de",
    nav_privacy: "Privacidad",
    search_placeholder: "Buscar en la web libre...",
    tab_web: "Web",
    tab_images: "Imágenes",
    tab_news: "Noticias",
    tab_videos: "Videos",
    tab_library: "Biblioteca",
    results_found: "resultados (",
    no_results_title: "No se encontraron resultados",
    no_results_desc: "Comprueba la ortografía o intenta con términos más generales.",
  },
  en: {
    nav_about: "About",
    nav_privacy: "Privacy",
    search_placeholder: "Search the libre web...",
    tab_web: "Web",
    tab_images: "Images",
    tab_news: "News",
    tab_videos: "Videos",
    tab_library: "Library",
    results_found: "results (",
    no_results_title: "No results found",
    no_results_desc: "Check your spelling or try more general keywords.",
  },
  fr: {
    nav_about: "À propos",
    nav_privacy: "Confidentialité",
    search_placeholder: "Rechercher sur le web libre...",
    tab_web: "Web",
    tab_images: "Images",
    tab_news: "Actualités",
    tab_videos: "Vidéos",
    tab_library: "Bibliothèque",
    results_found: "résultats (",
    no_results_title: "Aucun résultat trouvé",
    no_results_desc: "Vérifiez l'orthographe ou essayez des mots-clés plus généraux.",
  },
  de: {
    nav_about: "Über uns",
    nav_privacy: "Datenschutz",
    search_placeholder: "Im freien Web suchen...",
    tab_web: "Web",
    tab_images: "Bilder",
    tab_news: "Nachrichten",
    tab_videos: "Videos",
    tab_library: "Bibliothek",
    results_found: "Ergebnisse (",
    no_results_title: "Keine Ergebnisse gefunden",
    no_results_desc: "Prüfen Sie die Schreibweise oder versuchen Sie allgemeinere Suchbegriffe.",
  },
  pt: {
    nav_about: "Sobre",
    nav_privacy: "Privacidade",
    search_placeholder: "Pesquisar na web livre...",
    tab_web: "Web",
    tab_images: "Imagens",
    tab_news: "Notícias",
    tab_videos: "Vídeos",
    tab_library: "Biblioteca",
    results_found: "resultados (",
    no_results_title: "Nenhum resultado encontrado",
    no_results_desc: "Verifique a ortografia ou tente palavras-chave mais gerais.",
  },
  it: {
    nav_about: "Info",
    nav_privacy: "Privacy",
    search_placeholder: "Cerca nel web libero...",
    tab_web: "Web",
    tab_images: "Immagini",
    tab_news: "Notizie",
    tab_videos: "Video",
    tab_library: "Biblioteca",
    results_found: "risultati (",
    no_results_title: "Nessun risultato trovato",
    no_results_desc: "Controlla l'ortografia o prova parole chiave più generali.",
  },
  ja: {
    nav_about: "概要",
    nav_privacy: "プライバシー",
    search_placeholder: "自由なウェブを検索...",
    tab_web: "ウェブ",
    tab_images: "画像",
    tab_news: "ニュース",
    tab_videos: "動画",
    tab_library: "ライブラリ",
    results_found: "件の検索結果 (",
    no_results_title: "一致する結果が見つかりませんでした",
    no_results_desc: "スペルを確認するか、より一般的なキーワードをお試しください。",
  },
  zh: {
    nav_about: "关于",
    nav_privacy: "隐私政策",
    search_placeholder: "在自由网络中搜索...",
    tab_web: "网页",
    tab_images: "图片",
    tab_news: "资讯",
    tab_videos: "视频",
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
 * Tor & Privacy Sandbox Storage Guards (GNU LibreJS Compliant)
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
 * Works seamlessly in Tor Browser (Standard, Safer, Safest) and with LibreJS.
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
 * Density Manager: Toggle comfortable / compact view modes.
 */
function initDensityManager() {
  var densityBtn = document.getElementById('densityBtn');
  var densityLabel = document.getElementById('densityLabel');
  
  try {
    var saved = localStorage.getItem('senda_density');
    if (saved === 'compact') {
      document.body.classList.add('compact-density');
      if (densityLabel) densityLabel.textContent = "Densidad: Compacta";
    }
  } catch(e) {}

  if (densityBtn) {
    densityBtn.addEventListener('click', function() {
      var isCompact = document.body.classList.toggle('compact-density');
      var mode = isCompact ? 'compact' : 'comfortable';
      if (densityLabel) {
        densityLabel.textContent = isCompact ? "Densidad: Compacta" : "Densidad: Cómoda";
      }
      try {
        localStorage.setItem('senda_density', mode);
      } catch(e) {}
    });
  }
}

/**
 * Sovereign Dropdown & Accessible Filter Manager (GNU LibreJS Compliant)
 * - Closes dropdowns on Escape key press (with focus restore to summary)
 * - Closes dropdowns on Outside Click
 * - Automatically closes other open dropdowns when one opens (mutual exclusion)
 * - Autofocuses country filter input when Region dropdown opens
 * - Client-side instant filter for countries and ISO codes
 * - Zero JS fallback: standard HTML <details> native behavior is preserved
 * - GNU LibreJS Compliant: 100% Free Software under GNU GPL-3.0-or-later.
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

  function resetMenuPosition(d) {
    var menu = d.querySelector('.filter-dropdown-menu');
    if (menu) {
      menu.style.left = '';
      menu.style.right = '';
      menu.style.transform = '';
    }
  }

  function closeAllDropdowns(except) {
    dropdowns.forEach(function(d) {
      if (d !== except && d.hasAttribute('open')) {
        d.removeAttribute('open');
        resetMenuPosition(d);
      }
    });
  }

  function adjustMenuBoundary(d) {
    var menu = d.querySelector('.filter-dropdown-menu');
    if (!menu) return;
    menu.style.left = '';
    menu.style.right = '';
    menu.style.transform = '';

    var rect = menu.getBoundingClientRect();
    var viewportWidth = window.innerWidth || document.documentElement.clientWidth;

    // If menu extends beyond right edge, align right edge to button
    if (rect.right > viewportWidth - 8) {
      menu.style.left = 'auto';
      menu.style.right = '0';
    }

    // If after alignment it extends beyond left edge, shift it right
    var updatedRect = menu.getBoundingClientRect();
    if (updatedRect.left < 8) {
      var shift = 8 - updatedRect.left;
      menu.style.transform = 'translateX(' + shift + 'px)';
    }
  }

  // Handle dropdown open toggle for mutual exclusion, boundary adjustment, and autofocus
  dropdowns.forEach(function(d) {
    d.addEventListener('toggle', function() {
      if (d.open) {
        closeAllDropdowns(d);
        adjustMenuBoundary(d);

        var searchInput = d.querySelector('.country-search-input');
        if (searchInput) {
          setTimeout(function() {
            searchInput.focus();
          }, 50);
        }
      } else {
        resetMenuPosition(d);
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

  // Close dropdowns on outside click
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.filter-dropdown, .why-seen-disclosure')) {
      closeAllDropdowns(null);
    }
  });

  // Close dropdowns on Escape key press and restore focus to summary
  window.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' || e.key === 'Esc' || e.keyCode === 27) {
      var anyClosed = false;
      dropdowns.forEach(function(d) {
        if (d.open) {
          d.removeAttribute('open');
          resetMenuPosition(d);
          anyClosed = true;
          var summary = d.querySelector('summary');
          if (summary) summary.focus();
        }
      });
      if (anyClosed) {
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
    selector.addEventListener("change", function(e) {
      var selected = e.target.value;
      try {
        localStorage.setItem("senda_lang", selected);
      } catch (err) {}
      document.cookie = "senda_lang=" + selected + "; path=/; max-age=31536000; SameSite=Lax";
      var params = new URLSearchParams(window.location.search);
      params.set("lang", selected);
      window.location.search = params.toString();
    });
  }

  // Close sovereign language picker dropdown when clicking outside
  document.addEventListener("click", function(e) {
    var picker = document.querySelector("details.lang-picker[open]");
    if (picker && !picker.contains(e.target)) {
      picker.removeAttribute("open");
    }
  });

  applyTranslations(initialLang);
  initThemeManager();
  initDensityManager();
  initPreferencesManager();
  initDropdownsAndFilters();
  initCommandBar();
  initOpenSearchInstallation();
});

// @license-end
