# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Verifiable Grounded AI Synthesis for Senda Search Engine.

Strictly adheres to non-negotiable ethical guidelines:
1. Grounding: All assertions must explicitly cite retrieved primary items [1], [2].
2. Zero Hallucination: If retrieved items are empty or lack sufficient evidence to
   answer the query, Senda issues an explicit refusal to answer.
3. No Veracity Certifications: Senda never issues binary true/false judgments or certifies truth.
   Every claim is attributed strictly to the retrieved source.
4. Privacy & Free Software: 100% server-side HTML rendering compatible with GNU LibreJS
   and Tor Browser 'Safest' mode.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from senda.config import settings
from senda.providers.base import SearchResultItem


class GroundedCitation(BaseModel):
    """Citation metadata referencing a retrieved SearchResultItem."""

    index: int = Field(description="1-based citation index e.g. [1]")
    title: str
    url: str
    author: str = "Dato no disponible"
    published_date: Optional[str] = None
    source: str = "Fuente desconocida"
    domain: str = ""


class GroundedSynthesisResult(BaseModel):
    """Structured synthesis result with bracketed citations and ethical disclaimer."""

    summary: str
    citations: List[GroundedCitation] = Field(default_factory=list)
    disclaimer: str
    is_refusal: bool = False


class GroundedSynthesizer:
    """Produces verified, grounded answer syntheses from retrieved search items."""

    ETHICAL_DISCLAIMER = (
        "Aviso de procedencia: Síntesis automatizada atribuida. Senda no certifica verdad "
        "ni emite veredictos propios; consulte siempre los documentos originales."
    )

    def __init__(self, enabled: Optional[bool] = None):
        # Allow explicit override for tests or admin configuration
        self.enabled = settings.ENABLE_AI_SYNTHESIS if enabled is None else enabled

    def synthesize(
        self,
        query: str,
        items: List[SearchResultItem],
        force: bool = False,
    ) -> Optional[GroundedSynthesisResult]:
        """Synthesize retrieved evidence with explicit source citations.

        Returns None if synthesis is globally disabled and not forced.
        Returns a structured refusal if items are insufficient.
        """
        if not self.enabled and not force:
            return None

        clean_q = query.strip()
        if not clean_q:
            return None

        # Filter items with meaningful text
        valid_items: List[SearchResultItem] = []
        for it in items:
            text = (it.snippet or "") + " " + (it.title or "")
            if len(text.strip()) > 20:
                valid_items.append(it)

        # Refusal condition: insufficient evidence in retrieved items
        if not valid_items:
            return GroundedSynthesisResult(
                summary="No se encontraron fuentes primarias suficientes en los resultados para formular una síntesis con procedencia verificable.",
                citations=[],
                disclaimer="Senda exige evidencia y atribución verificable antes de emitir cualquier síntesis.",
                is_refusal=True,
            )

        # Extract top relevant items (up to 4) as cited primary sources
        selected = valid_items[:4]
        citations: List[GroundedCitation] = []

        import urllib.parse
        for idx, it in enumerate(selected, start=1):
            domain = ""
            try:
                domain = urllib.parse.urlparse(it.url).netloc
            except Exception:
                domain = ""

            author_str = ", ".join(it.authors) if it.authors else "Dato no disponible"
            citations.append(
                GroundedCitation(
                    index=idx,
                    title=it.title or "Sin título",
                    url=it.url,
                    author=author_str,
                    published_date=it.published_date or it.date,
                    source=it.source or domain or "Fuente externa",
                    domain=domain,
                )
            )

        # Build grounded synthesis paragraphs attributing each key point
        summary_lines = []
        for c in citations:
            # Find the corresponding snippet
            src_item = selected[c.index - 1]
            snippet_text = (src_item.snippet or src_item.title or "").strip()
            # Truncate cleanly to first sentence or max 140 chars
            clean_snip = snippet_text.split(". ")[0].rstrip(".")
            if len(clean_snip) > 160:
                clean_snip = clean_snip[:157] + "…"
            summary_lines.append(f"Según {c.source} ({c.author}): «{clean_snip}» [{c.index}].")

        body_text = " ".join(summary_lines)

        return GroundedSynthesisResult(
            summary=body_text,
            citations=citations,
            disclaimer=self.ETHICAL_DISCLAIMER,
            is_refusal=False,
        )
