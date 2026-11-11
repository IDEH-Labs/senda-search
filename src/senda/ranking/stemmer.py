# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Lightweight, sovereign morphological stemmer for multilingual query expansion.

Handles common inflectional and derivational suffixes in Spanish and English
without external heavyweight C/NLP dependencies.
"""

import unicodedata


class MorphologicalStemmer:
    """Provides heuristic root-prefix extraction for query expansion."""

    # Spanish inflectional and derivational suffixes (ordered by length descending)
    SPANISH_SUFFIXES = (
        "izaciones", "icamente", "amiento", "imiento", "aciones", "iciones",
        "idades", "amente", "adoras", "adores", "mente", "yendo", "iendo",
        "ando", "cion", "sión", "ador", "ante", "idad", "aron", "eron",
        "ados", "idos", "ales", "ores", "ado", "ido", "les", "des",
        "es", "as", "os", "ar", "er", "ir", "a", "o", "e", "s"
    )

    # English inflectional and derivational suffixes (ordered by length descending)
    ENGLISH_SUFFIXES = (
        "izations", "ization", "ational", "fulness", "ments", "ment",
        "ings", "ing", "ness", "tion", "tions", "ies", "ied", "ers",
        "er", "ed", "ly", "es", "s"
    )

    # French suffixes
    FRENCH_SUFFIXES = (
        "isations", "isation", "ements", "ement", "atrices", "atrice",
        "ateurs", "ateur", "ations", "ation", "abilites", "abilite",
        "euses", "euse", "ment", "ique", "iste", "able", "ible",
        "ance", "ence", "esse", "isse", "eaux", "ette", "eur", "eux",
        "ees", "ent", "ait", "ais", "ons", "iez", "ier", "ee", "es", "e", "s"
    )

    # Portuguese suffixes
    PORTUGUESE_SUFFIXES = (
        "izacoes", "izacao", "amentos", "amento", "imentos", "imento",
        "acoes", "acao", "idades", "idade", "amente", "mente",
        "adores", "adoras", "ador", "adora", "ando", "endo", "indo",
        "ados", "idos", "ado", "ido", "aram", "eram", "iram",
        "oes", "ao", "ais", "eis", "as", "os", "ar", "er", "ir", "a", "o", "e", "s"
    )

    # Italian suffixes
    ITALIAN_SUFFIXES = (
        "izzazioni", "izzazione", "amenti", "amento", "imenti", "imento",
        "azioni", "azione", "atrici", "atrice", "atori", "atore",
        "mente", "ismo", "isti", "ista", "ando", "endo", "anti", "ante",
        "abili", "abile", "ibili", "ibile", "anze", "anza", "enze", "enza",
        "ette", "etto", "etti", "etta", "ezza", "ezze", "eranno", "iranno",
        "arono", "erono", "irono", "iosa", "ioso", "ura", "ure",
        "ato", "ito", "ata", "ita", "ati", "iti", "are", "ere", "ire", "a", "o", "e", "i"
    )

    # German suffixes
    GERMAN_SUFFIXES = (
        "ungen", "ung", "heiten", "heit", "keiten", "keit", "schaften", "schaft",
        "ischen", "ischer", "isches", "ische", "isch", "lichen", "licher", "liches",
        "liche", "lich", "baren", "barer", "bares", "bare", "bar",
        "enden", "ender", "endes", "ende", "end", "eren", "erer", "eres", "ere",
        "ern", "ers", "eln", "ens", "est", "ten", "ter", "tes", "te",
        "en", "em", "es", "er", "st", "e", "s"
    )

    # Unified multilingual suffixes ordered strictly by length descending
    # to guarantee greedy maximal suffix stripping across all supported language families.
    ALL_SUFFIXES = tuple(
        sorted(
            set(
                SPANISH_SUFFIXES
                + ENGLISH_SUFFIXES
                + FRENCH_SUFFIXES
                + PORTUGUESE_SUFFIXES
                + ITALIAN_SUFFIXES
                + GERMAN_SUFFIXES
            ),
            key=len,
            reverse=True,
        )
    )

    @staticmethod
    def strip_accents(text: str) -> str:
        """Strip combining diacritical marks."""
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    @classmethod
    def get_root_prefix(cls, word: str, min_root_length: int = 3) -> str:
        """Extract a canonical root-prefix from a single word token.

        Guarantees that the resulting root has at least min_root_length characters.
        """
        w = word.strip().lower()
        if len(w) <= min_root_length:
            return w

        # Try stripped accents version
        clean_w = cls.strip_accents(w)

        # Check suffixes across unified multilingual catalogue (greedy longest-match first)
        for suffix in cls.ALL_SUFFIXES:
            clean_suffix = cls.strip_accents(suffix)
            if clean_w.endswith(clean_suffix):
                potential_root = clean_w[:-len(clean_suffix)]
                if len(potential_root) >= min_root_length:
                    return potential_root

        return clean_w
