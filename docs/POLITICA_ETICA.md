# Senda — Política Ética y Principios de Procedencia Verificable

**Versión:** 1.0.0  
**Licencia:** GPL-3.0-or-later  
**Ámbito:** Arquitectura técnica, recolección, indexación, presentación y gobernanza de resultados de búsqueda.  
**Entidad editora:** IDEH Labs <https://ideh.top>  

---

## 1. Misión y Filosofía Fundamental

**Senda** es un motor de búsqueda y agregador de procedencia verificable diseñado para devolver a las personas el control sobre su acceso al conocimiento humano, respetando de manera innegociable su privacidad, su autonomía cognitiva y los principios del Software Libre proclamados por la Free Software Foundation (FSF).

Senda opera bajo una premisa fundacional: **un motor de búsqueda no debe ser un árbitro de la verdad ontológica ni un censor moral oculto**. Senda **NO** certifica qué es "verdadero" o "falso" por cuenta propia; en su lugar, expone con total transparencia:
1. De dónde proviene cada resultado.
2. Quién respalda o financia la fuente que lo emite.
3. Cuándo fue publicado, actualizado o formalmente corregido.
4. Si cuenta con retractaciones académicas o señalamientos de verificación independiente (*fact-checking* atribuido).
5. Qué fuentes primarias cita y sostiene su argumentación.

Cuando la evidencia sobre un asunto o afirmación no está disponible, el sistema lo indica de forma explícita: **"Dato no disponible"** o **"Sin evaluar"**. Senda nunca fabrica métricas de confianza arbitrarias, nunca rellena vacíos informativos con suposiciones y nunca impone una narrativa editorial uniforme.

---

## 2. Principios No Negociables (Orden de Prevalencia)

En caso de conflicto técnico o de diseño, las decisiones de ingeniería en Senda se dirimen según la siguiente jerarquía estricta:

### Principio 1: Veracidad e Integridad de la Evidencia
- No se inventan datos, métricas, fuentes, capacidades ni resultados de verificación.
- En todos los informes técnicos y de desarrollo se distingue rigurosamente lo que ha sido implementado en código ejecutable, lo que ha sido verificado mediante pruebas automatizadas, y lo que constituye una hipótesis o limitación teórica.
- Toda afirmación mostrada al usuario en la interfaz debe poder rastrearse hasta un registro de metadatos auditable o un documento fuente real. Si no hay evidencia verificable, la etiqueta es invariablemente **"dato no disponible"** o **"sin evaluar"**.

### Principio 2: Privacidad Soberana y Cero Vigilancia
- **Cero registro de consultas (*Zero Query Logging*):** Los términos de búsqueda jamás se almacenan en bases de datos, discos persistentes o registros del servidor.
- **Cero almacenamiento de direcciones IP:** Las IPs de origen se descartan en memoria volátil de forma instantánea.
- **Sin perfiles ni analítica de terceros:** No se instalan cookies de rastreo, ni balizas, ni telemetría comercial, ni identificadores de sesión cruzada.
- **Transparencia en peticiones salientes:** Cualquier proveedor externo o catálogo que reciba peticiones anonimizadas se documenta explícitamente en [PRIVACY.md](file:///home/Familia/Proyectos/senda-search/PRIVACY.md) y en la página informativa */how-it-works*. Ningún proveedor externo se activa por defecto en la búsqueda general sin una justificación pública y documentada.
- **Cero Redirecciones de Rastreo en Noticias:** Senda prohíbe taxativamente entregar URLs intermedias de seguimiento corporativo (tales como `news.google.com/rss/articles/...`). Todo resultado de prensa enlaza directamente al dominio y artículo canónico del medio emisor o a repositorios abiertos (vía feeds RSS directos, GDELT o SearXNG), previniendo cualquier fuga de telemetría hacia intermediarios publicitarios.

### Principio 3: Bloqueo Solo por Daño Objetivo Comprobable; Etiquetado para lo Demás
Senda distingue de forma tajante entre **amenazas técnicas objetivas a la seguridad/integridad humana** y **discrepancias editoriales, ideológicas o cualitativas**:
- El **bloqueo duro** (exclusión del índice e imposibilidad de redirección) se reserva de forma estricta y restrictiva a cuatro categorías objetivas de daño (ver Sección 3).
- Todo el resto de la web (incluyendo medios satíricos, fuentes de baja calidad, blogs controvertidos o información dudosa) **se muestra con etiquetas de procedencia**, permitiendo al usuario juzgar con base en la evidencia expuesta. Jamás se oculta información por motivaciones políticas, corporativas o presiones ideológicas.

### Principio 4: Ausencia de Árbitro Editorial Oculto
- Los criterios de ponderación, ordenamiento lexical (BM25) y factores de la rúbrica de fuentes son 100% públicos, versionados y auditables en [docs/RUBRICA_FUENTES.md](file:///home/Familia/Proyectos/senda-search/docs/RUBRICA_FUENTES.md).
- La orientación política, confesional o editorial de una fuente **no constituye bajo ninguna circunstancia un factor de demérito ni de calidad**.

### Principio 5: Cero Patrones Oscuros y Cero Pago por Posicionamiento
- Senda no comercializa posiciones en los resultados de búsqueda.
- Si en alguna configuración federada o externa se recupera un resultado con vínculo de patrocinio de origen, este se separa físicamente en un bloque visual claramente delimitado como `[Contenido Patrocinado / Anuncio]`, sin mezcla con los resultados orgánicos y desprovisto de rastreadores conductuales.

---

## 3. Criterios Taxativos de Bloqueo Duro (Daño Objetivo)

Un recurso web solo puede ser objeto de bloqueo duro por Senda si encuadra de manera comprobable y documentada en una de las siguientes cuatro categorías:

| Categoría | Criterio de Activación | Fuente de Evidencia Exigida |
| :--- | :--- | :--- |
| **1. Malware Activo** | Sitios o URLs que distribuyen binarios maliciosos, exploits de navegador, troyanos o ransomware. | Coincidencia en feeds técnicos de inteligencia de amenazas verificados (ej. URLhaus CC0 de abuse.ch) con comprobación criptográfica. |
| **2. Phishing y Suplantación** | Sitios diseñados para engañar activamente a la persona simulando entidades bancarias, gubernamentales o de identidad para sustraer credenciales. | Coincidencia en feeds verificados de anti-phishing con análisis técnico reproducible. |
| **3. Fraude y Estafa Masiva** | Plataformas fraudulentas con evidencia técnica y documental concluyente de sustracción patrimonial ilegítima. | Veredictos concluyentes de autoridades judiciales o reguladoras oficiales comprobables. |
| **4. Abuso Sexual Infantil (CSAM)** | Cualquier URL o material que contenga, distribuya o facilite explotación o abuso sexual de menores. | Listas oficiales de autoridades policiales y de protección a la infancia con base en hashes estandarizados. Tolerancia cero absoluta. |

### Garantías contra la Censura Arbitraria
1. **Registro de Auditoría de Bloqueos:** Todo bloqueo ejecutado por el crawler o el despachador de resultados queda consignado en un registro interno de auditoría técnica que especifica: URL bloqueada, categoría de bloqueo, identificador de la regla o lista de amenazas que la originó, y fecha de aplicación.
2. **Procedimiento de Apelación:** Cualquier operador de un sitio web, investigador o usuario puede consultar el motivo técnico de un bloqueo y someter una apelación mediante el procedimiento documentado en [docs/APELACIONES.md](file:///home/Familia/Proyectos/senda-search/docs/APELACIONES.md).

---

## 4. Política de Tratamiento de Contenido Dudoso y Declaraciones de IA

### 4.1 Contenido Dudoso o Sin Evaluar
- Un sitio web que presente información controvertida, hipótesis marginales, opiniones radicales o teorías no consensuadas **NO se bloquea**.
- Si el sitio no ha sido evaluado bajo la rúbrica de fuentes de Senda, se muestra con la etiqueta explícita: **`[Fuente sin evaluar]`**.
- Si el sitio cuenta con evaluaciones en la rúbrica, el panel "¿Por qué veo esto?" desplegará los hechos auditados (ej. *"Propiedad: no declarada | Política de correcciones: no disponible | Autoría: anónima"*). El usuario toma sus propias decisiones con base en los hechos revelados.

### 4.2 Prohibición de Afirmaciones Falsas de "Revisión por Pares"
- El acceso abierto (Open Access) no es sinónimo de revisión por pares. Plataformas como arXiv, bioRxiv, Zenodo o repositorios institucionales contienen preprints, datasets y ponencias de trabajo de enorme valor, pero que no han completado una evaluación por pares formal.
- Senda tiene prohibido mostrar la etiqueta "Revisada por pares" a menos que un metadato explícito y verificado del catálogo (ej. registro en DOAJ o metadato `peer_reviewed: true` de Crossref) lo certifique fehacientemente. En ausencia de dicho dato, la etiqueta obligatoria es: **`[Revisión por pares no verificada]`**.

### 4.3 Prohibición de Detectores Automáticos de IA
- Los detectores heurísticos o estadísticos de "texto generado por IA" han demostrado elevadísimas tasas de falsos positivos y sesgos sistemáticos contra hablantes no nativos o textos técnicos estructurados.
- Senda **prohíbe el uso de detectores probabilísticos de IA** para clasificar o penalizar contenidos.
- La etiqueta de origen de inteligencia artificial solo se aplica cuando exista una **señal declarada de procedencia** (por ejemplo, credenciales criptográficas C2PA / Content Credentials, o declaración explícita de los autores en metadatos). En todos los demás casos, el estado oficial es: **`[Procedencia: No determinado]`**.

---

## 5. Neutralidad de Agentes y Respeto a Estándares de la Red

1. **Cumplimiento Estricto del Estándar de Exclusión de Robots (RFC 9309):**  
   El crawler de Senda respeta rigurosamente `robots.txt`, directivas `Disallow`, `Crawl-delay` y directivas `meta name="robots" content="noindex, nofollow"`.
2. **Identificación Transparente:**  
   Todas las solicitudes HTTP emitidas por el crawler o adaptadores de Senda contienen un `User-Agent` institucional con enlace público a nuestra documentación y dirección de correo de contacto de abuso.
3. **Aislamiento Técnico:**  
   El crawler opera sin ejecución de motores JavaScript del lado del cliente para eliminar vectores de ataque dinámicos (XSS, zero-day browser exploits), en entornos de ejecución con privilegios mínimos y con defensas estrictas contra falsificación de peticiones del lado del servidor (SSRF) hacia rangos RFC 1918 / Loopback.
4. **Prohibición de Extracción de Datos Privados:**  
   Senda no rastrea ni indexa perfiles privados de personas naturales, redes sociales cerradas o plataformas que exijan sortear controles de autenticación o barreras técnicas. Únicamente se indexan fuentes web públicas y protocolos abiertos institucionales (Fediverse/ActivityPub, Bluesky/ATProto) cuyos términos de uso lo permitan de forma explícita.
