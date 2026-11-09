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

        # Check Spanish suffixes
        for suffix in cls.SPANISH_SUFFIXES:
            clean_suffix = cls.strip_accents(suffix)
            if clean_w.endswith(clean_suffix):
                potential_root = clean_w[:-len(clean_suffix)]
                if len(potential_root) >= min_root_length:
                    return potential_root

        # Check English suffixes
        for suffix in cls.ENGLISH_SUFFIXES:
            if clean_w.endswith(suffix):
                potential_root = clean_w[:-len(suffix)]
                if len(potential_root) >= min_root_length:
                    return potential_root

        return clean_w
