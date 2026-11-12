# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Verifiable Grounded Extractive Synthesis Engine for Senda Search.

Strictly adheres to non-negotiable ethical guidelines:
1. Grounding: All assertions must explicitly cite retrieved source items [1], [2].
2. Zero Hallucination: Purely deterministic extractive quotes from retrieved documents.
   Senda never uses generative AI models for synthesis and never invents claims.
3. No Veracity Certifications: Senda never issues binary true/false judgments or certifies truth.
   Every claim is attributed strictly to the retrieved source.
4. Methodological Precision: Sources retrieved from the web are secondary/tertiary documents,
   never falsely labeled as "fuentes primarias" unless formally verified as such.
5. Privacy & Free Software: 100% server-side HTML rendering compatible with GNU LibreJS
   and Tor Browser 'Safest' mode.
"""

import re
import urllib.parse
from typing import List, Optional
from pydantic import BaseModel, Field

from senda.config import settings
from senda.providers.base import SearchResultItem


class GroundedCitation(BaseModel):
    """Citation metadata referencing a retrieved SearchResultItem."""

    index: int = Field(description="1-based citation index e.g. [1]")
    title: str
    url: str
    author: str = "No declarada"
    published_date: Optional[str] = None
    source: str = "Fuente desconocida"
    domain: str = ""


# Backward-compatible alias
CitationItem = GroundedCitation


class GroundedSynthesisResult(BaseModel):
    """Structured synthesis result with bracketed citations and ethical disclaimer."""

    summary: str
    citations: List[GroundedCitation] = Field(default_factory=list)
    disclaimer: str
    is_refusal: bool = False


def _clean_and_truncate_snippet(text: str, max_chars: int = 180) -> str:
    """Extract a complete, coherent sentence or clause from snippet text without mid-word cuts."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""

    # Try to find a sentence ending with punctuation (. ! ?)
    sentence_match = re.search(r"^(.*?[.!?])(?:\s+|$)", cleaned)
    if sentence_match:
        sentence = sentence_match.group(1).strip()
        if len(sentence) >= 30 and len(sentence) <= max_chars:
            return sentence

    # If too long or no punctuation, truncate at word boundary
    if len(cleaned) > max_chars:
        truncated = cleaned[:max_chars].rsplit(" ", 1)[0].rstrip(".,;:¡!¿?")
        return truncated + "…"

    return cleaned.rstrip(".,;:¡!¿?")


class GroundedSynthesizer:
    """Produces verified, grounded extractive syntheses from retrieved search items."""

    ETHICAL_DISCLAIMER = (
        "Aviso de procedencia: Síntesis extractiva determinista atribuida a documentos fuente. "
        "Senda no certifica verdad ni emite veredictos propios; no se utilizan modelos generativos "
        "de IA en esta función. Consulte siempre los documentos originales."
    )

    def __init__(self, enabled: Optional[bool] = None):
        # Allow explicit override for tests or admin configuration
        # Supports both new ENABLE_EXTRACTIVE_SYNTHESIS and legacy ENABLE_AI_SYNTHESIS
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = getattr(settings, "ENABLE_EXTRACTIVE_SYNTHESIS", settings.ENABLE_AI_SYNTHESIS)

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

        # Refusal condition: insufficient evidence in retrieved documents
        if not valid_items:
            return GroundedSynthesisResult(
                summary="No se encontraron documentos fuente suficientes en los resultados para formular una síntesis con procedencia verificable.",
                citations=[],
                disclaimer="Senda exige documentos fuente y atribución verificable antes de emitir cualquier síntesis.",
                is_refusal=True,
            )

        # Extract top relevant items (up to 4) as cited sources
        selected = valid_items[:4]
        citations: List[GroundedCitation] = []

        for idx, it in enumerate(selected, start=1):
            domain = ""
            try:
                domain = urllib.parse.urlparse(it.url).netloc
            except Exception:
                domain = ""

            author_str = ", ".join(it.authors) if it.authors else "No declarada"
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
            src_item = selected[c.index - 1]
            raw_text = (src_item.snippet or src_item.title or "").strip()
            clean_snip = _clean_and_truncate_snippet(raw_text, max_chars=180)

            # Distinct quotation typography: complete sentence vs truncated extract
            if clean_snip.endswith("…"):
                quote_text = f"«{clean_snip.rstrip('…')} [...]»"
            else:
                quote_text = f"«{clean_snip}»"

            # Clean attribution without awkward placeholders
            if c.author and c.author not in ("No declarada", "Dato no disponible"):
                summary_lines.append(f"Según {c.author} en {c.source}: {quote_text} [{c.index}].")
            else:
                summary_lines.append(f"Según {c.source}: {quote_text} [{c.index}].")

        body_text = " ".join(summary_lines)

        return GroundedSynthesisResult(
            summary=body_text,
            citations=citations,
            disclaimer=self.ETHICAL_DISCLAIMER,
            is_refusal=False,
        )
