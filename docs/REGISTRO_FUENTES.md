# Senda — Registro Oficial de Fuentes y Licencias de Datos

**Versión:** 1.0.0  
**Fecha de Publicación:** Noviembre 2026  
**Licencia del Documento:** GPL-3.0-or-later  
**Gobernanza:** IDEH Labs <https://ideh.top>  

> [!IMPORTANT]
> **REGLA DE SEGURIDAD JURÍDICA Y GOBERNANZA:**
> Toda fuente de datos, catálogo o feed de inteligencia de amenazas debe estar inventariada en este registro antes de cualquier integración en el código.
> **Ningún agente automatizado o IA puede marcar una fuente como "verificado por humano".** El estado inicial es obligatoriamente `recopilado por agente, pendiente` o `NO VERIFICADO`.
> **Cualquier fuente en estado distinto de "verificado por humano en [fecha]" NO SE ACTIVA EN PRODUCCIÓN.**

---

## 1. Inventario de Fuentes de Datos y Feeds Técnicos

| Identificador | Nombre / Entidad | URL de Términos / Documentación | Licencia Legal Declarada | Uso Comercial | Requisitos de Atribución | Límites de Tasa y Cuotas | Costo | Estado de Verificación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `threat-urlhaus` | **URLhaus** (abuse.ch) | `https://urlhaus.abuse.ch/api/` | Creative Commons CC0 1.0 Universal (Dominio Público) | Permitido sin restricciones | Mención de cortesía recomendada: "Data provided by URLhaus (abuse.ch)" | API REST ~1 req/s para búsquedas individuales; descargas masivas en JSON/CSV cada 5 minutos | Gratuito ($0) | `recopilado por agente, pendiente` |
| `threat-phishtank` | **PhishTank** (Cisco OpenDNS) | `https://www.phishtank.com/developer_info.php` | Términos de Desarrollador PhishTank / Cisco | Restringido: prohibida la comercialización directa sin acuerdo con Cisco | Logotipo y enlace de atribución a PhishTank obligatorio en interfaces que muestren datos | Requiere App Key gratuita; descarga masiva `online-valid.json` con cuota diaria | Gratuito para uso no comercial | `recopilado por agente, pendiente` |
| `acad-crossref` | **Crossref REST API** | `https://www.crossref.org/documentation/retrieve-metadata/rest-api/` | Creative Commons CC0 1.0 Universal (Metadatos bibliográficos) | Permitido | Enlaces de resolución DOI persistentes (`https://doi.org/...`) | Pool educado ("Polite Pool") con cabecera `mailto:`: ~50 req/s con ráfagas controladas | Gratuito ($0) | `recopilado por agente, pendiente` |
| `acad-arxiv` | **arXiv API** (Cornell University) | `https://info.arxiv.org/help/api/tou.html` | Términos de la API de arXiv / Metadatos abiertos | Requiere acuerdo para uso comercial formal según TOU; permitido para interoperabilidad abierta | Mención obligatoria: "Thank you to arXiv for use of its open access interoperability" | Estricto: máximo 1 petición cada 3 segundos (0.33 req/s); sin concurrencia; sin scraping en horas pico | Gratuito ($0) | `recopilado por agente, pendiente` |
| `acad-pubmed` | **PubMed / NCBI E-utilities** (NLM / NIH) | `https://www.ncbi.nlm.nih.gov/books/NBK25497/` | Dominio público (Obras gubernamentales de EE.UU.); derechos de autor editoriales en textos completos | Permitido para metadatos públicos con atribución | Cita formal a NCBI / National Library of Medicine | Máximo 3 req/s sin clave; hasta 10 req/s con NCBI API key gratuita. Parámetros obligatorios: `tool` y `email` | Gratuito ($0) | `recopilado por agente, pendiente` |
| `acad-doaj` | **DOAJ (Directory of Open Access Journals)** | `https://doaj.org/terms/` | Creative Commons Reconocimiento-CompartirIgual 4.0 (CC BY-SA 4.0) | Permitido bajo términos de CC BY-SA 4.0 | Atribución explícita a DOAJ requerida | Peticiones a API REST v2 de búsqueda pública con límites razonables de cortesía | Gratuito ($0) | `recopilado por agente, pendiente` |
| `acad-retractionwatch` | **Retraction Watch Database** (vía Crossref) | `https://www.crossref.org/blog/news-crossref-and-retraction-watch/` | Creative Commons CC0 1.0 (Integrado en metadatos Crossref desde 2023) | Permitido bajo CC0 | Atribución a Crossref y The Retraction Watch Database recomendada | Mismos límites del endpoint REST de Crossref | Gratuito ($0) | `recopilado por agente, pendiente` |
| `acad-scielo` | **SciELO / Redalyc** | `https://scielo.org/` y `https://www.redalyc.org/` | Acceso Abierto (Mayoría CC BY o CC BY-NC) | Variable según cada revista (muchas revistas aplican CC BY-NC no comercial) | Atribución al repositorio institucional y enlace a la revista de origen | OAI-PMH estándar; uso obligatorio de `resumptionToken` e intervalos de cortesía | Gratuito ($0) | `recopilado por agente, pendiente` |
| `acad-openalex` | **OpenAlex API** (OurResearch) | `https://docs.openalex.org/how-to-use-the-api/api-overview` | Creative Commons CC0 1.0 Universal | Permitido | Atribución de cortesía a OurResearch / OpenAlex | Desde feb-2026: exige clave de API (1 crédito por consulta de lista); 30 req/min configuradas en Senda | Clave gratuita básica; créditos de pago para uso empresarial masivo | `recopilado por agente, pendiente` |

---

## 2. Protocolo de Aprobación Humana

Para promover cualquier fuente del estado `recopilado por agente, pendiente` a `verificado por humano en [AAAA-MM-DD]`:
1. El responsable legal y técnico del proyecto debe ingresar al enlace oficial de los términos de la fuente.
2. Comprobar que no existen cláusulas incompatibles con la licencia **GPL-3.0-or-later** de Senda ni restricciones no declaradas.
3. Actualizar la celda correspondiente en este archivo consignando:
   `verificado por humano en [AAAA-MM-DD] por [Firma/Nombre]`
4. Solo a partir de ese momento, el adaptador correspondiente podrá ser habilitado en la configuración de producción.
