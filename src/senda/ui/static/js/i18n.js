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
 * Theme Manager: Toggle light/dark themes with localStorage.
 */
function initThemeManager() {
  var toggleBtn = document.getElementById('themeToggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', function() {
    var current = document.documentElement.getAttribute('data-theme') || 'dark';
    var next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try {
      localStorage.setItem('senda_theme', next);
    } catch(e) {}
  });
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
 * Why Seen Dialog Handler
 */
function initWhySeenDialog() {
  var dialog = document.getElementById('whyDialog');
  var dialogText = document.getElementById('whyDialogText');
  var closeBtn = document.getElementById('closeWhyBtn');

  if (!dialog || !dialogText) return;

  document.querySelectorAll('.why-seen-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var explanation = btn.getAttribute('data-why') || "Resultado orgánico obtenido según relevancia léxica BM25.";
      dialogText.textContent = explanation;
      dialog.showModal();
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', function() {
      dialog.close();
    });
  }

  dialog.addEventListener('click', function(e) {
    if (e.target === dialog) {
      dialog.close();
    }
  });
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
  initDensityManager();
  initWhySeenDialog();
  initCommandBar();
});

// @license-end
