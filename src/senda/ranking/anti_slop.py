# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Anti-Slop & Synthetic Farm Detection Engine
Inspired by Kagi SlopStop and anti-SEO scraping defenses.
Detects, flags, and demotes repetitive AI-generated spam and content-farm filler.
Works 100% server-side with zero JavaScript required.
"""

from __future__ import annotations

import re
from typing import List, Tuple
from senda.providers.base import SearchResultItem


# Known synthetic filler cliches common in automated LLM content-farms
SYNTHETIC_CLICHES = [
    # Spanish
    r"\ben\s+conclusi[oó]n\b",
    r"\ben\s+resumen\b",
    r"\bes\s+(?:fundamental|importante|crucial)\s+(?:tener\s+en\s+cuenta|destacar|mencionar)\b",
    r"\ben\s+el\s+(?:vertiginoso|mundo\s+actual|panorama\s+digital)\b",
    r"\ba\s+continuaci[oó]n\s+te\s+(?:explicamos|presentamos|mostramos)\b",
    r"\ben\s+este\s+art[ií]culo\s+(?:exploraremos|analizaremos|descubriremos)\b",
    r"\bcomo\s+modelo\s+de\s+lenguaje\b",
    r"\bsin\s+lugar\s+a\s+dudas\b",
    r"\bcabe\s+destacar\s+que\b",
    r"\btodo\s+lo\s+que\s+necesitas\s+saber\s+sobre\b",

    # English
    r"\bin\s+conclusion\b",
    r"\bin\s+summary\b",
    r"\bit\s+is\s+(?:important|crucial|essential)\s+to\s+(?:note|remember|consider)\b",
    r"\bin\s+today's\s+(?:fast-paced|digital|modern)\s+world\b",
    r"\bin\s+this\s+article\s+we\s+will\s+(?:explore|delve|examine)\b",
    r"\bas\s+an\s+ai\s+language\s+model\b",
    r"\beverything\s+you\s+need\s+to\s+know\s+about\b",
]

COMPILED_CLICHES = [re.compile(p, re.IGNORECASE) for p in SYNTHETIC_CLICHES]


def compute_slop_score(
    title: str,
    snippet: str,
    domain: str,
    has_author: bool = False,
    has_date: bool = False,
) -> Tuple[float, List[str]]:
    """
    Compute heuristic slop probability score from 0.0 (high human craft) to 1.0 (pure AI slop).
    Returns (score, detected_reasons).
    """
    text = f"{title} {snippet}".strip().lower()
    score = 0.0
    reasons: List[str] = []

    if not text:
        return 0.0, []

    # 1. Check for synthetic filler clichés
    matches = [m.pattern for m in COMPILED_CLICHES if m.search(text)]
    if len(matches) >= 2:
        score += 0.45
        reasons.append("Múltiples clichés genéricos de redacción sintética")
    elif len(matches) == 1:
        score += 0.20
        reasons.append("Frases típicas de granjas de contenido")

    # 2. Check for keyword stuffing in title
    title_words = [w for w in re.findall(r"\w+", title.lower()) if len(w) > 3]
    if len(title_words) >= 6:
        unique_ratio = len(set(title_words)) / len(title_words)
        if unique_ratio < 0.65:
            score += 0.30
            reasons.append("Títulos con repetición forzada para SEO (keyword stuffing)")

    # 3. Complete absence of author and date on long generic text
    if not has_author and not has_date and len(snippet) > 120:
        score += 0.15
        reasons.append("Sin autoría identificada ni fecha de publicación")

    # 4. Repetitive clickbait patterns
    if re.search(r"\b(los\s+\d+\s+mejores|top\s+\d+|gu[ií]a\s+definitiva\s+de)\b", title, re.I):
        score += 0.10

    return min(1.0, score), reasons


def apply_anti_slop_filter(
    items: List[SearchResultItem],
    threshold: float = 0.55,
    demote_penalty: float = 45.0,
) -> List[SearchResultItem]:
    """
    Inspect retrieved items, flag synthetic content mills, and demote them in ranking.
    """
    if not items:
        return items

    for item in items:
        has_author = bool(item.authors and len(item.authors) > 0)
        has_date = bool(item.published_date or item.date)
        score, reasons = compute_slop_score(
            title=item.title,
            snippet=item.snippet,
            domain=item.domain,
            has_author=has_author,
            has_date=has_date,
        )

        if score >= threshold:
            item.score -= demote_penalty
            reason_str = "; ".join(reasons)
            item.why_seen = f"[Anti-Slop: Sospecha de granja SEO ({reason_str})] {item.why_seen}".strip()
            if not item.ai_provenance:
                from senda.providers.base import AIProvenance
                item.ai_provenance = AIProvenance(
                    declared_signal="Heurística Anti-Slop: Alta probabilidad de generación sintética / granja SEO",
                    status="degradado",
                )

    # Re-sort descending
    items.sort(key=lambda x: x.score, reverse=True)
    return items
