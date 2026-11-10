# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Base schemas and interface for interchangeable SearchProviders and Verifiable Provenance."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RetractionInfo(BaseModel):
    """Auditable metadata for scientific or editorial retractions."""
    status: str = Field(default="desconocido", description="ninguna | retractada | expresión_de_preocupación | desconocido")
    source: Optional[str] = Field(default=None, description="Fuente o base de datos que formalizó la retractación (ej. Crossref, Retraction Watch)")
    date: Optional[str] = Field(default=None, description="Fecha ISO de la retractación formal")
    notice_url: Optional[str] = Field(default=None, description="Enlace persistente al aviso editorial de retractación")


class VerificationItem(BaseModel):
    """ClaimReview attributed fact-check evidence."""
    verifier: str = Field(..., description="Nombre de la organización independiente signataria de la IFCN")
    attributed_verdict: str = Field(..., description="Veredicto textual atribuido a la organización evaluadora")
    url: str = Field(..., description="URL permanente del análisis de verificación")
    date: Optional[str] = Field(default=None, description="Fecha de publicación de la verificación")


class SourceScoreInfo(BaseModel):
    """Versioned rubric factors and transparency indicators."""
    rubric_version: str = Field(default="senda-rubric-v1.0.0", description="Versión de la rúbrica auditada")
    factores: Dict[str, Any] = Field(default_factory=dict, description="Factores auditados y evidencias")
    nota: str = Field(default="sin evaluar", description="Estado de evaluación (sin evaluar | evaluada)")


class AIProvenance(BaseModel):
    """Declared AI provenance signals (strictly zero unreliable detectors)."""
    declared_signal: Optional[str] = Field(default=None, description="Señal técnica declarada (ej. credencial C2PA, metadato de autor)")
    status: str = Field(default="no determinado", description="declarado | no determinado")


class SearchResultItem(BaseModel):
    """Normalized search result item extended with verifiable provenance.
    
    Adheres strictly to the Senda Verifiable Provenance schema:
    Any unknown field is null or 'desconocido', never fabricated.
    """
    # Core search fields (backward-compatible)
    title: str = Field(..., description="Document title / Título")
    url: str = Field(..., description="Canonical or target URL")
    snippet: str = Field(default="", description="Snippet or highlighted excerpt")
    source: str = Field(default="Senda", description="Originating provider (Senda, SearXNG, Brave, Mojeek, Crossref, etc.)")
    date: Optional[str] = Field(default=None, description="Publication or indexing date")
    language: Optional[str] = Field(default=None, description="Content language code")
    doc_type: str = Field(default="web", description="Vertical category: web, images, news, videos, library")
    media_url: Optional[str] = Field(default=None, description="Direct thumbnail/media URL for media items")
    is_sponsored: bool = Field(default=False, description="Strict boolean flag. Ads are visually separated and never mixed with organic results.")
    score: float = Field(default=0.0, description="Ranking or BM25 relevance score")
    why_seen: str = Field(default="", description="Honest, transparent explanation of why this result was included and ranked.")

    # Verifiable Provenance extended schema
    canonical_url: Optional[str] = Field(default=None, description="URL canónica comprobada")
    source_type: str = Field(
        default="desconocida",
        description="tipo_fuente: primaria_oficial | académica | noticia | verificación | web | red_abierta | desconocida"
    )
    content_type: str = Field(
        default="desconocido",
        description="tipo_contenido: artículo | preprint | tesis | dataset | noticia | opinión | patrocinado | otro | desconocido"
    )
    published_date: Optional[str] = Field(default=None, description="Fecha formal de publicación")
    updated_date: Optional[str] = Field(default=None, description="Fecha formal de actualización / corrección")
    authors: List[str] = Field(default_factory=list, description="Lista nominal de autor(es)")
    corrections: List[str] = Field(default_factory=list, description="Registro formal de correcciones o fe de erratas")
    retraction: Optional[RetractionInfo] = Field(default=None, description="Estado de retractación auditable")
    primary_citations: List[str] = Field(default_factory=list, description="Citas y enlaces directos a fuentes primarias")
    verifications: List[VerificationItem] = Field(default_factory=list, description="Verificaciones de terceros atribuidas")
    security_signals: List[str] = Field(default_factory=list, description="Señales técnicas de listas de amenazas (malware, phishing)")
    source_score: Optional[SourceScoreInfo] = Field(default=None, description="Puntuación y factores de la rúbrica versionada")
    provider_origin: str = Field(default="Senda", description="Identificador técnico del proveedor")
    ai_provenance: Optional[AIProvenance] = Field(default=None, description="Procedencia declarada de IA")

    @property
    def domain(self) -> str:
        """Extract domain from URL safely."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            return parsed.netloc or ""
        except Exception:
            return ""

    def to_provenance_dict(self) -> Dict[str, Any]:
        """Serialize into the exact canonical Senda Verifiable Provenance dictionary."""
        retraction_dict = None
        if self.retraction:
            retraction_dict = {
                "estado": self.retraction.status,
                "fuente": self.retraction.source,
                "fecha": self.retraction.date,
            }
        else:
            retraction_dict = {
                "estado": "ninguna",
                "fuente": None,
                "fecha": None,
            }

        verif_list = [
            {
                "verificador": v.verifier,
                "veredicto_atribuido": v.attributed_verdict,
                "url": v.url,
                "fecha": v.date,
            }
            for v in self.verifications
        ]

        score_dict = None
        if self.source_score:
            score_dict = {
                "versión_rúbrica": self.source_score.rubric_version,
                "factores": self.source_score.factores,
                "nota": self.source_score.nota,
            }
        else:
            score_dict = {
                "versión_rúbrica": "senda-rubric-v1.0.0",
                "factores": {},
                "nota": "sin evaluar",
            }

        ai_dict = None
        if self.ai_provenance:
            ai_dict = {
                "señal_declarada": self.ai_provenance.declared_signal,
                "estado": self.ai_provenance.status,
            }
        else:
            ai_dict = {
                "señal_declarada": None,
                "estado": "no determinado",
            }

        return {
            "título": self.title,
            "url": self.url,
            "url_canónica": self.canonical_url or self.url,
            "fragmento": self.snippet,
            "fuente": self.source,
            "tipo_fuente": self.source_type,
            "tipo_contenido": self.content_type,
            "fecha_publicación": self.published_date or self.date,
            "fecha_actualización": self.updated_date,
            "autor(es)": self.authors,
            "correcciones": self.corrections,
            "retractación": retraction_dict,
            "citas_a_primarias": self.primary_citations,
            "verificaciones": verif_list,
            "señales_seguridad": self.security_signals,
            "puntuación_fuente": score_dict,
            "origen_proveedor": self.provider_origin,
            "es_patrocinado": self.is_sponsored,
            "procedencia_ia": ai_dict,
        }


class SearchProvider(ABC):
    """Abstract search provider adapter enforcing zero tracking and header neutralization."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/endpoints are set."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        category: str = "all",
        page: int = 1,
        page_size: int = 10,
        time_filter: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: str = "off",
    ) -> List[SearchResultItem]:
        """Execute search, strip identifying headers, and normalize output."""
        pass
