# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Sovereign Typo-Tolerance and Spell Suggestion Engine for Senda Search.

Provides 100% offline-resilient, privacy-first, zero-telemetry spelling corrections,
Damerau-Levenshtein edit-distance calculation, and Wikimedia OpenSearch entity suggestions.
Declared Free Software under GNU GPL-3.0-or-later.
"""

import html
import re
import time
import urllib.parse
from typing import Dict, List, Optional, Tuple
import httpx


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Damerau-Levenshtein edit distance between two strings.

    Accounts for insertions, deletions, substitutions, and transpositions of adjacent characters.
    """
    d = {}
    len1, len2 = len(s1), len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,          # deletion
                d[(i, j - 1)] + 1,          # insertion
                d[(i - 1, j - 1)] + cost,   # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + 1)  # transposition

    return d[(len1 - 1, len2 - 1)]


class SuggestionEngine:
    """Provides privacy-preserving spelling suggestions and typo-tolerance."""

    _VOCAB_CACHE: Optional[Dict[str, str]] = None

    # Offline common vocabulary of high-frequency tech, scientific, and cultural entities
    OFFLINE_DICTIONARY = {
        "notre dame", "albert einstein", "stephen hawking", "marie curie",
        "computadora", "ordenador", "wikipedia", "inteligencia artificial",
        "software libre", "codigo abierto", "open source", "sistema operativo",
        "redes neuronales", "mecanica cuantica", "fisica cuantica",
        "richard stallman", "linus torvalds", "alan turing", "ada lovelace",
        "python", "javascript", "linux", "debian", "ubuntu", "arch linux",
        "freedom", "privacy", "knowledge", "science", "library",
    }

    @classmethod
    def get_offline_vocabulary(cls) -> Dict[str, str]:
        """Lazy-loaded authoritative in-memory vocabulary for zero-latency correction (<0.1ms)."""
        if cls._VOCAB_CACHE is not None:
            return cls._VOCAB_CACHE

        vocab: Dict[str, str] = {
            "notre dame": "Notre Dame",
            "albert einstein": "Albert Einstein",
            "stephen hawking": "Stephen Hawking",
            "marie curie": "Marie Curie",
            "computadora": "Computadora",
            "ordenador": "Ordenador",
            "wikipedia": "Wikipedia",
            "inteligencia artificial": "Inteligencia Artificial",
            "machine learning": "Machine Learning",
            "deep learning": "Deep Learning",
            "software libre": "Software Libre",
            "codigo abierto": "Código Abierto",
            "open source": "Open Source",
            "sistema operativo": "Sistema Operativo",
            "redes neuronales": "Redes Neuronales",
            "mecanica cuantica": "Mecánica Cuántica",
            "fisica cuantica": "Física Cuántica",
            "richard stallman": "Richard Stallman",
            "linus torvalds": "Linus Torvalds",
            "alan turing": "Alan Turing",
            "ada lovelace": "Ada Lovelace",
            "python": "Python",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "rust": "Rust",
            "linux": "Linux",
            "debian": "Debian",
            "ubuntu": "Ubuntu",
            "arch linux": "Arch Linux",
            "github": "GitHub",
            "gitlab": "GitLab",
            "codeberg": "Codeberg",
            "gutenberg": "Project Gutenberg",
            "open library": "Open Library",
            "europeana": "Europeana",
            "gallica": "Gallica",
            "biblioteca nacional": "Biblioteca Nacional",
            "nasa": "NASA",
            "esa": "ESA",
            "eso": "ESO",
            "james webb": "James Webb",
            "hubble": "Hubble",
            "astronomia": "Astronomía",
            "astrofisica": "Astrofísica",
            "pubmed": "PubMed",
            "medlineplus": "MedlinePlus",
            "cochrane": "Cochrane",
            "salud publica": "Salud Pública",
            "openstax": "OpenStax",
            "unesco": "UNESCO",
            "who": "WHO",
            "paho": "PAHO",
            "arxiv": "arXiv",
            "hugging face": "Hugging Face",
            "freedom": "Freedom",
            "privacy": "Privacy",
            "knowledge": "Knowledge",
            "science": "Science",
            "library": "Library",
        }

        # Populate with 100% of sovereign nations and their official aliases
        try:
            from senda.countries import SOVEREIGN_REGISTRY, normalize_country_text
            for c in SOVEREIGN_REGISTRY.values():
                vocab[normalize_country_text(c.name_es)] = c.name_es
                vocab[normalize_country_text(c.name_en)] = c.name_es
                for a in c.aliases:
                    vocab[normalize_country_text(a)] = c.name_es
        except Exception:
            pass

        cls._VOCAB_CACHE = vocab
        return cls._VOCAB_CACHE

    def __init__(self, timeout: float = 2.5, cache_ttl_seconds: int = 3600):
        self.timeout = timeout
        self.cache_ttl_seconds = cache_ttl_seconds
        # In-memory volatile cache: (q, lang) -> (timestamp, suggestion)
        self._cache: Dict[Tuple[str, str], Tuple[float, Optional[str]]] = {}

    def _cache_get(self, key: Tuple[str, str]) -> Optional[str]:
        cached = self._cache.get(key)
        if not cached:
            return None
        ts, item = cached
        if (time.time() - ts) > self.cache_ttl_seconds:
            self._cache.pop(key, None)
            return None
        return item

    def _cache_set(self, key: Tuple[str, str], item: Optional[str]) -> None:
        if len(self._cache) > 2000:
            self._cache.clear()
        self._cache[key] = (time.time(), item)

    async def suggest(self, query: str, lang: str = "es") -> Optional[str]:
        """Suggest an authoritative spelling correction for query, if one exists."""
        if not query or len(query.strip()) < 3:
            return None

        clean_q = query.strip()
        q_norm = clean_q.lower()

        # Do not suggest for exact quoted queries
        if clean_q.startswith('"') and clean_q.endswith('"'):
            return None

        cache_key = (q_norm, lang)
        cached_result = self._cache_get(cache_key)
        if cached_result is not None:
            return cached_result if cached_result != "" else None

        # 1. Check authoritative offline dictionary first (zero network latency)
        vocab = self.get_offline_vocabulary()
        best_offline_term: Optional[str] = None
        best_offline_dist = 999
        max_d = 1 if len(q_norm) < 7 else 2

        for term, display_title in vocab.items():
            if abs(len(term) - len(q_norm)) > max_d:
                continue
            dist = damerau_levenshtein_distance(q_norm, term)
            if 0 < dist <= max_d and dist < best_offline_dist:
                best_offline_dist = dist
                best_offline_term = display_title
                if dist == 1:
                    # An exact 1-letter typo distance match is overwhelmingly likely
                    break

        if best_offline_term:
            self._cache_set(cache_key, best_offline_term)
            return best_offline_term

        # 2. Query Wikimedia OpenSearch API (non-profit, privacy-first, verified entities)
        target_lang = lang if lang in ("es", "en", "fr", "de", "pt", "it") else "es"
        encoded_q = urllib.parse.quote_plus(q_norm)
        url = (
            f"https://{target_lang}.wikipedia.org/w/api.php?"
            f"action=opensearch&search={encoded_q}&limit=5&namespace=0&format=json"
        )
        headers = {
            "User-Agent": "SendaSearch/2.0 (https://senda.ideh.top; privacy-first sovereign search)",
            "Accept": "application/json",
        }

        candidates: List[str] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if len(data) > 1 and isinstance(data[1], list):
                        candidates = [str(c) for c in data[1]]
        except Exception:
            candidates = []

        num_query_words = len(q_norm.split())
        best_candidate: Optional[str] = None
        best_dist = 999

        for c in candidates:
            # Strip parenthetical disambiguations: "Notre-Dame de Paris (comédie musicale)" -> "Notre-Dame de Paris"
            clean_c = re.sub(r"\(.*?\)", "", c).strip()
            # Normalize dashes to spaces for comparison: "Notre-Dame" -> "Notre Dame"
            clean_c_spaced = clean_c.replace("-", " ")
            c_words = clean_c_spaced.split()

            # A. Check prefix of matching word count:
            if len(c_words) >= num_query_words:
                cand_slice = " ".join(c_words[:num_query_words])
                dist = damerau_levenshtein_distance(q_norm, cand_slice.lower())
                if 0 < dist <= 2 and dist < best_dist:
                    best_dist = dist
                    best_candidate = cand_slice

            # B. Check full title:
            full_dist = damerau_levenshtein_distance(q_norm, clean_c_spaced.lower())
            if 0 < full_dist <= 2 and full_dist < best_dist:
                best_dist = full_dist
                best_candidate = clean_c_spaced

        if best_candidate and best_candidate.lower() != q_norm:
            self._cache_set(cache_key, best_candidate)
            return best_candidate

        self._cache_set(cache_key, "")
        return None
