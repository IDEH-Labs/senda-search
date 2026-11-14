# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Dictionary & Lexicographical Definition Provider.

Retrieves grammatical categories, etymologies, definitions, examples, and synonyms
directly from Wikimedia Wiktionary / Wikcionario APIs.
Enforces zero telemetry, privacy-preserving client headers, in-memory caching,
and strictly non-evaluating deterministic text parsing.
Data licensed under Creative Commons Atribución-CompartirIgual 4.0 (CC BY-SA 4.0).
"""

from __future__ import annotations

import html
import logging
import re
import time
import urllib.parse
from typing import Dict, List, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DictionarySense(BaseModel):
    """Numbered lexical sense/definition of a term."""
    number: int
    field: Optional[str] = None  # e.g., "Psicología", "Física", "Ecología"
    definition: str
    example: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)


class DictionaryCard(BaseModel):
    """Structured, verifiable dictionary card for search results."""
    word: str
    part_of_speech: str = "Palabra"  # e.g., "Sustantivo femenino", "Adjetivo"
    etymology: Optional[str] = None
    senses: List[DictionarySense] = Field(default_factory=list)
    all_synonyms: List[str] = Field(default_factory=list)
    all_antonyms: List[str] = Field(default_factory=list)
    source_url: str
    source_name: str = "Wikcionario"
    license: str = "Creative Commons Atribución-CompartirIgual 4.0 (CC BY-SA 4.0)"
    lang: str = "es"
    query_intent: str = "definition"  # "definition", "synonym", "antonym"


def extract_dictionary_term(query: str) -> Optional[Tuple[str, str, str]]:
    """
    Detect if search query expresses dictionary, definition, synonym or antonym intent.
    Returns (cleaned_term, lang, intent) or None.
    """
    if not query:
        return None
    raw = query.strip()
    if len(raw) > 100:
        return None

    # Strip trailing punctuation
    clean = re.sub(r"[?¿!¡\.\s]+$", "", raw).strip()

    # Spanish patterns
    # 1. Definición / significado
    m_def = re.match(
        r"^(?:qu[eé]\s+significa\s+|significado\s+(?:de\s+|del\s+)?|definici[oó]n\s+(?:de\s+|del\s+)?|definir\s+)[\"'\s]*(.+?)[\"'\s]*$",
        clean,
        flags=re.IGNORECASE,
    )
    if m_def:
        term = _clean_term(m_def.group(1))
        if term:
            return term, "es", "definition"

    # 2. Sinónimos
    m_syn = re.match(
        r"^(?:sin[oó]nimos?\s+(?:de\s+|del\s+|para\s+)?)[\"'\s]*(.+?)[\"'\s]*$",
        clean,
        flags=re.IGNORECASE,
    )
    if m_syn:
        term = _clean_term(m_syn.group(1))
        if term:
            return term, "es", "synonym"

    # 3. Antónimos
    m_ant = re.match(
        r"^(?:ant[oó]nimos?\s+(?:de\s+|del\s+|para\s+)?)[\"'\s]*(.+?)[\"'\s]*$",
        clean,
        flags=re.IGNORECASE,
    )
    if m_ant:
        term = _clean_term(m_ant.group(1))
        if term:
            return term, "es", "antonym"

    # 4. Prefijo explícito dict: / diccionario:
    m_pref = re.match(r"^(?:dict|diccionario):\s*[\"']?(.+?)[\"']?$", clean, flags=re.IGNORECASE)
    if m_pref:
        term = _clean_term(m_pref.group(1))
        if term:
            return term, "es", "definition"

    # English patterns
    m_en_def = re.match(
        r"^(?:what\s+does\s+(.+?)\s+mean|(?:definition|meaning)\s+(?:of\s+)?(.+?)|define\s+(.+?))$",
        clean,
        flags=re.IGNORECASE,
    )
    if m_en_def:
        raw_word = m_en_def.group(1) or m_en_def.group(2) or m_en_def.group(3)
        term = _clean_term(raw_word)
        if term:
            return term, "en", "definition"

    m_en_syn = re.match(
        r"^synonyms?\s+(?:of\s+|for\s+)?[\"']?(.+?)[\"']?$",
        clean,
        flags=re.IGNORECASE,
    )
    if m_en_syn:
        term = _clean_term(m_en_syn.group(1))
        if term:
            return term, "en", "synonym"

    return None


def _clean_term(term: str) -> Optional[str]:
    """Strip leading articles and surrounding whitespace/quotes."""
    if not term:
        return None
    t = term.strip("\"' \t\r\n")
    # Strip optional leading articles
    t = re.sub(r"^(?:el|la|los|las|un|una|unos|unas|the|a|an)\s+", "", t, flags=re.IGNORECASE).strip()
    if 1 < len(t) <= 45 and not re.search(r"[<>{}\[\]|\\]", t):
        return t.lower()
    return None


def parse_wiktionary_extract(word: str, text: str, lang: str = "es", intent: str = "definition") -> Optional[DictionaryCard]:
    """Parse plain text extract returned by Wiktionary Action API."""
    if not text or not text.strip():
        return None

    etymology: Optional[str] = None
    pos = "Palabra" if lang == "es" else "Word"
    senses: List[DictionarySense] = []
    all_synonyms: List[str] = []
    all_antonyms: List[str] = []

    # 1. Etimología
    etym_m = re.search(
        r"===\s*Etimolog[ií]a(?:\s+\d+)?\s*===\s*\n(.*?)(?=\n===|\n==|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if etym_m:
        raw_etym = etym_m.group(1).strip()
        # Clean internal markers
        raw_etym = re.sub(r"\[cita requerida\]", "", raw_etym)
        etymology = " ".join(raw_etym.split())

    # 2. Part of Speech (Categoría gramatical)
    pos_m = re.search(
        r"={3,4}\s*(Sustantivo[^\n=]*|Adjetivo[^\n=]*|Verbo[^\n=]*|Adverbio[^\n=]*|Interjecci[oó]n[^\n=]*|Preposici[oó]n[^\n=]*|Noun[^\n=]*|Verb[^\n=]*|Adjective[^\n=]*|Adverb[^\n=]*)\s*={3,4}",
        text,
        re.IGNORECASE,
    )
    if pos_m:
        raw_pos = pos_m.group(1).strip()
        # Clean extra qualifiers like " 1"
        pos = re.sub(r"\s+\d+$", "", raw_pos)

    # 3. Parse numbered senses / definitions
    raw_senses = re.findall(
        r"(?:^|\n)(\d+)(?:[ \t]+([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[a-záéíóú]+)?))?\s*\n([^\n]+(?:\n(?!\d+(?:[ \t]+[A-Z]|\s*\n)|[=])[^\n]+)*)",
        text,
    )

    for num_str, field_tag, sense_body in raw_senses[:6]:
        lines = [l.strip() for l in sense_body.strip().splitlines() if l.strip()]
        if not lines:
            continue
        field = field_tag if field_tag else None
        raw_def = lines[0]
        # Clean citation marks
        clean_def = re.sub(r"\[cita requerida\]", "", raw_def).strip()

        rest_lines = lines[1:]
        example = None
        sense_syns: List[str] = []

        for rl in rest_lines:
            if rl.lower().startswith("ejemplo:"):
                example = rl[8:].strip()
            elif rl.lower().startswith("sinónimo:") or rl.lower().startswith("sinónimos:") or rl.lower().startswith("synonym:") or rl.lower().startswith("synonyms:"):
                raw_syns = re.sub(r"^(?:sin[oó]nimos?|synonyms?):\s*", "", rl, flags=re.IGNORECASE)
                syns = [s.strip(" .,;()") for s in raw_syns.split(",") if s.strip(" .,;()")]
                sense_syns.extend(syns)
                all_synonyms.extend(syns)
            elif rl.lower().startswith("antónimo:") or rl.lower().startswith("antónimos:") or rl.lower().startswith("antonym:") or rl.lower().startswith("antonyms:"):
                raw_ants = re.sub(r"^(?:ant[oó]nimos?|antonyms?):\s*", "", rl, flags=re.IGNORECASE)
                ants = [s.strip(" .,;()") for s in raw_ants.split(",") if s.strip(" .,;()")]
                all_antonyms.extend(ants)

        if clean_def:
            senses.append(
                DictionarySense(
                    number=int(num_str),
                    field=field,
                    definition=clean_def,
                    example=example,
                    synonyms=sense_syns,
                )
            )

    # If no numbered senses matched, check if there's a simple bulleted list
    if not senses:
        bullets = re.findall(r"(?:^|\n)[*#]\s*([^\n]+)", text)
        for i, b in enumerate(bullets[:4], start=1):
            clean_b = re.sub(r"\[cita requerida\]", "", b).strip()
            if len(clean_b) > 5:
                senses.append(DictionarySense(number=i, definition=clean_b))

    if not senses and not all_synonyms:
        return None

    # Source branding and URLs
    encoded_word = urllib.parse.quote(word)
    if lang == "es":
        source_url = f"https://es.wiktionary.org/wiki/{encoded_word}"
        source_name = "Wikcionario"
    else:
        source_url = f"https://en.wiktionary.org/wiki/{encoded_word}"
        source_name = "Wiktionary"

    # Deduplicate synonyms & antonyms
    unique_syns = list(dict.fromkeys([s for s in all_synonyms if s.lower() != word.lower()]))
    unique_ants = list(dict.fromkeys([a for a in all_antonyms if a.lower() != word.lower()]))

    return DictionaryCard(
        word=word,
        part_of_speech=pos,
        etymology=etymology,
        senses=senses,
        all_synonyms=unique_syns,
        all_antonyms=unique_ants,
        source_url=source_url,
        source_name=source_name,
        lang=lang,
        query_intent=intent,
    )


class DictionaryProvider:
    """Zero-telemetry provider querying open Wiktionary instances."""

    def __init__(self, timeout: float = 3.0, cache_ttl_seconds: int = 7200):
        self.timeout = timeout
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Tuple[float, Optional[DictionaryCard]]] = {}
        self.user_agent = "SendaSearch/1.0 (https://senda.ideh.top; contact@ideh.top)"

    def _get_cached(self, key: str) -> Optional[DictionaryCard]:
        cached = self._cache.get(key)
        if not cached:
            return None
        ts, item = cached
        if time.time() - ts > self.cache_ttl_seconds:
            self._cache.pop(key, None)
            return None
        return item

    def _set_cached(self, key: str, card: Optional[DictionaryCard]):
        self._cache[key] = (time.time(), card)

    async def get_definition(self, query: str, default_lang: str = "es") -> Optional[DictionaryCard]:
        """Detect intent and fetch dictionary card asynchronously."""
        parsed = extract_dictionary_term(query)
        if not parsed:
            return None

        word, lang, intent = parsed
        cache_key = f"{lang}:{word}:{intent}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        encoded_word = urllib.parse.quote(word)
        url = (
            f"https://{lang}.wiktionary.org/w/api.php"
            f"?action=query&prop=extracts&explaintext=1&titles={encoded_word}&format=json&redirects=1"
        )
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    self._set_cached(cache_key, None)
                    return None

                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for pid, page_data in pages.items():
                    if pid != "-1" and "extract" in page_data:
                        card = parse_wiktionary_extract(
                            word=page_data.get("title", word),
                            text=page_data["extract"],
                            lang=lang,
                            intent=intent,
                        )
                        self._set_cached(cache_key, card)
                        return card

                # If not found in primary language and was Spanish, attempt English fallback
                if lang == "es":
                    en_url = (
                        f"https://en.wiktionary.org/w/api.php"
                        f"?action=query&prop=extracts&explaintext=1&titles={encoded_word}&format=json&redirects=1"
                    )
                    resp_en = await client.get(en_url, headers=headers)
                    if resp_en.status_code == 200:
                        en_data = resp_en.json()
                        en_pages = en_data.get("query", {}).get("pages", {})
                        for pid, page_data in en_pages.items():
                            if pid != "-1" and "extract" in page_data:
                                card = parse_wiktionary_extract(
                                    word=page_data.get("title", word),
                                    text=page_data["extract"],
                                    lang="en",
                                    intent=intent,
                                )
                                self._set_cached(cache_key, card)
                                return card

                self._set_cached(cache_key, None)
                return None
        except Exception as e:
            logger.debug(f"DictionaryProvider fetch error for '{word}': {e}")
            return None
