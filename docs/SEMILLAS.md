# Senda — Registro Versionado de Semillas Curadas

**Versión:** 1.0.0  
**Fecha de Publicación:** Noviembre 2026  
**Licencia:** GPL-3.0-or-later  
**Gobernanza:** IDEH Labs <https://ideh.top>  

> [!IMPORTANT]
> **POLÍTICA DE TRANSPARENCIA EN SEMILLAS:**
> Senda no realiza rastreo indiscriminado de toda la web ni scraping invasivo. El rastreo general se inicia a partir de una lista pública, auditable y versionada de semillas institucionales, de preservación y de acceso abierto.
> Cada semilla documenta su titular, motivo de inclusión, licencia de contenidos y política de cortesía en `robots.txt`.

---

## 1. Directorio de Semillas Curadas (v1.0.0)

| Identificador | Dominio / URL Semilla | Entidad Titular | Categoría Vertical | Licencia / Términos de Contenido | Motivo de Inclusión | Estado Robots.txt |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `seed-fsf` | `https://www.fsf.org/` | Free Software Foundation | Software Libre / Derechos | FDL / CC BY-ND 4.0 | Fuente primaria fundamental de la filosofía del software libre y directrices de soberanía. | Permitido; directiva `Crawl-delay: 10` respetada estrictamente. |
| `seed-gnu` | `https://www.gnu.org/` | Proyecto GNU | Software Libre / Manuales | GNU FDL 1.3 / CC BY-ND | Documentación técnica, manuales oficiales del sistema operativo libre y manifiesto GNU. | Permitido; respeto de exclusiones técnicas y crawl delay. |
| `seed-eff` | `https://www.eff.org/` | Electronic Frontier Foundation | Derechos Digitales / Privacidad | Creative Commons CC BY 3.0 US | Análisis jurídico y técnico sobre privacidad, libertad de expresión y criptografía. | Permitido; respeto integral de directivas en `/robots.txt`. |
| `seed-archive` | `https://archive.org/` | Internet Archive | Preservación / Biblioteca | Dominio Público / Creative Commons / Open Access | Biblioteca digital universal sin ánimo de lucro y custodia de la memoria web histórica. | Permitido; respeto a exclusiones de colecciones restringidas y tasa de cortesía. |
| `seed-wikipedia` | `https://en.wikipedia.org/` | Wikimedia Foundation | Enciclopedia / Conocimiento Libre | CC BY-SA 4.0 / GNU FDL | Enciclopedia comunitaria abierta de referencia mundial. | Permitido; respeto a directiva de cortesía y exclusión de páginas de edición/historial. |
| `seed-doaj` | `https://doaj.org/` | Directory of Open Access Journals | Ciencia Abierta / Académica | CC BY-SA 4.0 | Catálogo global de revistas científicas evaluadas por pares en acceso abierto estricto. | Permitido; respeto a API y endpoints de búsqueda. |
| `seed-arxiv` | `https://arxiv.org/` | Cornell University | Ciencia Abierta / Preprints | Contenidos abiertos bajo términos de arXiv | Archivo de preprints de investigación en física, matemáticas, computación y biomedicina. | Permitido; respeto riguroso al intervalo de 3s por consulta. |
| `seed-debian` | `https://www.debian.org/` | Proyecto Debian | Software Libre / Distribución | Directrices de Software Libre de Debian (DFSG) | Sistema operativo universal libre y gobernanza comunitaria transparente. | Permitido; respeto de directivas de indexación. |
| `seed-datos-gov-co`| `https://www.datos.gov.co/` | Gobierno de Colombia / MinTIC | Datos Públicos / Oficial | Datos Abiertos del Estado Colombiano | Conjuntos de datos primarios abiertos de interés general y rendición de cuentas pública. | Permitido; consulta de conjuntos de datos y metadatos públicos. |
| `seed-w3c` | `https://www.w3.org/` | World Wide Web Consortium | Estándares Web / Accesibilidad | W3C Software and Document License | Fuente primaria de estándares de la web abierta (HTML5, WCAG 2.2, CSS, WAI-ARIA). | Permitido; respeto de directivas de archivo y borradores. |

---

## 2. Reglas Operativas de Rastreo y Preservación

1. **Sin Scraping Ciego ni Huellas Agresivas:**  
   El crawler opera con un hilo único por dominio, respetando estrictamente los intervalos de cortesía declarados (`Crawl-delay`) o aplicando un retardo mínimo de seguridad (3 a 10 segundos).
2. **Respeto a `meta name="robots" content="noindex"`:**  
   Si una página de una semilla curada contiene la directiva `noindex`, Senda se abstiene de insertarla en el índice de búsqueda. Si contiene `nofollow`, no se extraen enlaces salientes.
3. **Deduplicación por URL Canónica (`rel="canonical"`):**  
   Si una página declara `<link rel="canonical" href="...">`, el indexador asocia el contenido al enlace canónico oficial para evitar la fragmentación del índice y la duplicación de páginas con parámetros de rastreo.
