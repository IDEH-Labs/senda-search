# Rúbrica de Procedencia y Factores de Fuentes — Senda

**Versión:** 1.0.0  
**Fecha de Publicación:** Noviembre 2026  
**Licencia:** GPL-3.0-or-later  
**Ámbito de Aplicación:** Evaluación y presentación de evidencias en el panel "¿Por qué veo esto?" de Senda.  
**Identificador de Versión Semántica:** `senda-rubric-v1.0.0`  

---

## 1. Declaración de Principios de la Rúbrica

1. **La orientación política, editorial, ideológica o confesional NO es un factor de calidad ni de calificación.** Senda rechaza tajantemente cualquier mecanismo que penalice o premie medios en función de sus líneas de opinión, posturas políticas o valores editoriales.
2. **Cada afirmación mostrada al usuario responde a hechos objetivos verificables**, nunca a opiniones arbitrarias de los desarrolladores o de evaluadores anónimos.
3. **Todo factor ausente se reporta como "dato no disponible" o "sin evaluar".** No existen inferencias estadísticas que asuman calidad o falta de calidad ante la ausencia de metadatos.
4. **Cero puntuaciones opacas o cajas negras.** Si un indicador se muestra, se desglosa factor por factor para que el usuario entienda con exactitud qué se midió, cómo se midió y qué limitaciones técnicas tiene la medición.

---

## 2. Factores Verificables de la Rúbrica v1.0.0

A continuación se detalla la matriz de factores que componen la rúbrica versionada de Senda. Cada factor especifica su definición técnica, la evidencia auditable que exige, las fuentes de datos utilizadas y sus limitaciones intrínsecas:

```
┌────────────────────────────────────────────────────────────────────────┐
│                     MATRIZ DE FACTORES AUDITABLES                      │
│                                                                        │
│ 1. Transparencia de Propiedad    ──► ¿Quién controla legalmente la web? │
│ 2. Política de Correcciones      ──► ¿Cómo rectifican sus errores?     │
│ 3. Identificación de Autoría     ──► ¿Quién firma la publicación?      │
│ 4. Citas a Fuentes Primarias     ──► ¿Enlaza a documentos originales?  │
│ 5. Historial Técnico del Dominio ──► ¿Edad RDAP y persistencia web?    │
│ 6. Registro de Retractaciones    ──► ¿Hay retractaciones Crossref/RW?  │
│ 7. Verificaciones Independientes ──► ¿ClaimReview emitido por IFCN?    │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Factor 1: Transparencia de Propiedad y Financiamiento (`propiedad_transparente`)

- **Definición:** Grado de accesibilidad pública sobre la identidad jurídica de la entidad propietaria, accionistas mayoritarios o fuentes estructurales de financiamiento del medio u organización editora.
- **Evidencia Exigida:**
  - Sección accesible en el sitio web (ej. `Quiénes somos`, `Aviso legal`, `Masthead`, `Transparencia corporativa`) con personería jurídica, número de identificación tributaria o registro mercantil.
  - O declaración explícita de financiamiento estatal, fondos públicos, subvenciones internacionales o donaciones comunitarias.
- **Fuentes de Datos:**
  - Registro de transparencia de medios (Trust Project, Journalism Trust Initiative JTI - ISO/IEC 17065).
  - Marcado estructurado Schema.org (`NewsMediaOrganization.ownershipFundingInfo`).
  - Auditoría documental indexada por Senda.
- **Limitaciones:**
  - Medios independientes en regímenes autoritarios o zonas en conflicto pueden ocultar deliberadamente a sus donantes o propietarios para salvaguardar la vida e integridad de su personal.
  - La presencia de personería jurídica no garantiza ausencia de presiones financieras indirectas.
- **Valores posibles en panel:**
  - `Declarada públicamente`: Enlace a la sección legal del dominio.
  - `Financiamiento estatal/público declarado`: Detalle de la entidad pública matriz.
  - `Dato no disponible / Sin evaluar`: Si no se ha localizado registro o marcado estructurado.

---

### Factor 2: Política Pública de Correcciones (`politica_correcciones`)

- **Definición:** Existencia y aplicación visible de un protocolo claro mediante el cual la publicación atiende señalamientos de inexactitud fáctica, corrige sus contenidos y documenta públicamente la fe de erratas para los lectores.
- **Evidencia Exigida:**
  - Enlace permanente (*permalink*) a una política de correcciones formal publicada en el dominio.
  - O presencia de marcadores de fe de erratas explícitos dentro de los artículos (ej. etiquetas `<meta name="correction">` o marcado estructurado Schema.org `CorrectionSpecification`).
- **Fuentes de Datos:**
  - Marcado estructurado Schema.org (`NewsMediaOrganization.correctionsPolicy`).
  - Verificación cruzada con la International Fact-Checking Network (IFCN) o estándares JTI.
- **Limitaciones:**
  - Publicar un enlace a una política de correcciones no garantiza que la redacción la aplique con honestidad en casos de alto impacto.
  - Medios muy pequeños o blogs individuales suelen corregir directamente en el cuerpo del texto sin contar con una página formal de políticas corporativas.
- **Valores posibles en panel:**
  - `Política documentada`: Enlace directo al protocolo de rectificación del medio.
  - `Dato no disponible / Sin evaluar`: Sin registro auditable.

---

### Factor 3: Identificación de Autoría y Responsabilidad Editorial (`autoria_identificada`)

- **Definición:** Identificación inequívoca de las personas naturales o equipos especializados responsables de la redacción, autoría o supervisión del contenido.
- **Evidencia Exigida:**
  - Firma nominal (*byline*) de autor con biografía profesional, perfil institucional o credencial académica verificable (ej. identificador ORCID en artículos científicos).
  - O firma corporativa institucional claramente atribuida al consejo editorial o agencia de prensa.
- **Fuentes de Datos:**
  - Metadatos HTML semánticos (`<meta name="author">`, `rel="author"`).
  - Marcado estructurado Schema.org (`Article.author`, `Person.sameAs`, `Person.identifier`).
  - Registro ORCID para autores académicos.
- **Limitaciones:**
  - El uso de seudónimos es legítimo en entornos de persecución judicial, activismo de derechos humanos o investigación en zonas hostiles.
  - Autores ficticios o firmas clonadas pueden eludir metadatos simples si no se comprueba la persistencia de la trayectoria del autor.
- **Valores posibles en panel:**
  - `Autor identificado`: Nombre y enlace a trayectoria/ORCID si existe.
  - `Firma institucional`: Publicado bajo la firma colectiva de la redacción o entidad.
  - `Seudónimo / Sin firma identificada`: Si el contenido es anónimo.

---

### Factor 4: Citas y Enlaces a Fuentes Primarias (`citas_a_primarias`)

- **Definición:** Práctica periodística o académica de enlazar o citar directamente los documentos originales en los que se basan las afirmaciones: sentencias judiciales, gacetas oficiales, leyes, datasets crudos, preprints, artículos científicos, informes parlamentarios o declaraciones textuales grabadas.
- **Evidencia Exigida:**
  - Hipervínculos salientes a dominios gubernamentales oficiales (`.gov`, `.gob.*`, `.edu`, `.mil`), registros públicos, repositorios de datos (ej. Zenodo, Dryad) o identificadores persistentes (DOI).
- **Fuentes de Datos:**
  - Análisis estructural de enlaces salientes procesados por el extractor semántico de Senda (`src/senda/extractor/parser.py`).
  - Lista blanca de registros y catálogos de preservación oficial.
- **Limitaciones:**
  - Muchos reportajes de investigación se basan en entrevistas confidenciales o documentos físicos no digitalizados que no admiten hiperenlaces directos.
  - Enlaces rotos (*link rot*) a fuentes primarias a lo largo del tiempo.
- **Valores posibles en panel:**
  - `Enlaza a fuentes primarias (N citas detectadas)`: Desglose de dominios primarios citados.
  - `Citas a fuentes secundarias`: Enlaza a otros portales de noticias o agregadores.
  - `Sin enlaces salientes detectados`: El texto no referencia vínculos externos.

---

### Factor 5: Historial Técnico y Persistencia del Dominio (`historial_dominio`)

- **Definición:** Medición técnica de la estabilidad en el tiempo de la infraestructura del nombre de dominio, evitando el sesgo contra nuevos sitios pero alertando sobre dominios efímeros creados recientemente para operaciones coordinadas de estafa o suplantación.
- **Evidencia Exigida:**
  - Fecha de registro original del dominio mediante consultas al protocolo RDAP (RFC 9082 / RFC 9083) y archivos históricos de zonas DNS.
- **Fuentes de Datos:**
  - Servicios de consulta pública RDAP de los Registros Regionales de Internet (RIRs: LACNIC, RIPE, ARIN, APNIC, AFRINIC) y registradores de dominios de primer nivel (ccTLDs / gTLDs).
- **Limitaciones:**
  - El historial RDAP/WHOIS no indica la calidad intelectual de un medio: un dominio antiguo puede haber sido adquirido recientemente en subasta (*domain flipping/drop catching*) para fines comerciales opacos.
  - Nuevas iniciativas periodísticas legítimas nacen con dominios recientes de pocas semanas o meses de vida.
- **Valores posibles en panel:**
  - `Dominio consolidado`: Registrado hace más de 3 años de forma continuada.
  - `Dominio en consolidación`: Registrado entre 1 y 3 años.
  - `Dominio de reciente creación (< 1 año)`: Notificación neutra de antigüedad.
  - `Dato no disponible`: Servidor RDAP inaccesible o restringido por privacidad técnica.

---

### Factor 6: Historial de Retractaciones Académicas y Periodísticas (`retractaciones`)

- **Definición:** Registro público y auditable de trabajos científicos o periodísticos formalmente retractados, retirados o sometidos a expresiones de preocupación editorial por errores metodológicos o faltas a la integridad.
- **Evidencia Exigida:**
  - Coincidencia del DOI en la base de datos de retractaciones de Crossref / Retraction Watch.
  - O aviso de retractación explícito del consejo editorial en la revista fuente.
- **Fuentes de Datos:**
  - Crossref REST API (propiedad `update-to` con tipo `retraction`, con licencia CC0).
  - OpenAlex API (campo `is_retracted: true` e histórico de versiones).
- **Limitaciones:**
  - El tiempo que transcurre entre la denuncia de una inconsistencia metodológica y la formalización de la retractación puede ser de meses o años.
  - La retractación es un mecanismo saludable de la ciencia para auto-corregirse; la existencia de una retractación puntual no implica necesariamente que todo el trabajo previo del autor sea inválido.
- **Valores posibles en panel:**
  - `Sin retractaciones registradas`: En las bases consultadas a la fecha.
  - `OBRA RETRACTADA`: Identificación de la fecha de retractación, enlace al aviso editorial oficial y motivo declarado.
  - `Expresión de preocupación editorial`: Aviso preliminar formal de la editorial.

---

### Factor 7: Verificaciones de Terceros Independientes Atribuidas (`verificaciones_atribuidas`)

- **Definición:** Identificación de evaluaciones fácticas realizadas por organizaciones de verificación periodística profesional que hayan emitido un dictamen atribuido sobre la afirmación o contenido en cuestión.
- **Evidencia Exigida:**
  - Marcado estructurado ClaimReview (estándar Schema.org) emitido por una organización verificada que cumpla el Código de Principios de la International Fact-Checking Network (IFCN).
- **Fuentes de Datos:**
  - Repositorio y feeds públicos ClaimReview / Fact Check Tools API.
  - Evaluaciones directas sindicadas por organizaciones de verificación acreditadas.
- **Limitaciones:**
  - Los verificadores independientes tienen agendas temáticas acotadas y no cubren la totalidad de los temas del debate público.
  - Existen discrepancias legítimas de criterio entre distintos verificadores sobre matices en el uso del lenguaje.
  - **Senda NUNCA asume el dictamen del verificador como veredicto propio del motor de búsqueda**. Siempre se presenta atribuido: *"Organización X concluyó: [Dictamen atribuido], consultado el [Fecha]"*.
- **Valores posibles en panel:**
  - `Verificación atribuida`: Detalle del verificador, texto de la afirmación analizada, conclusión textual del verificador y enlace al análisis completo.
  - `Sin verificaciones de terceros registradas`: Ningún verificador acreditado ha emitido un ClaimReview sobre este contenido.

---

## 3. Resolución de Casos Límite en la Aplicación de la Rúbrica

Para evitar sesgos estructurales y garantizar la equidad algorítmica, se establecen las siguientes reglas operativas para resolver casos límite:

---

### Caso Límite 1: Medio Local Comunitario o Hiperlocal Pequeño
- **Descripción:** Un periódico comunitario de barrio o municipio pequeño que opera con recursos mínimos, sin infraestructura corporativa, sin equipo de abogados y sin marcado Schema.org avanzado.
- **Riesgo:** Que los algoritmos lo penalicen por carecer de sellos corporativos, páginas de transparencia complejas o certificados JTI.
- **Resolución en Senda:**
  - La ausencia de marcado estructurado no genera penalización ni resta visibilidad al contenido.
  - El panel reporta con neutralidad: `"Transparencia de propiedad: no declarada formalmente | Política de correcciones: no especificada | Fuente: medio local"`.
  - Si el contenido aporta valor contextual o cobertura hiperlocal no disponible en grandes agencias, se indexa y clasifica lexicalmente (BM25) de acuerdo a la consulta del usuario sin barreras artificiales.

---

### Caso Límite 2: Blog Académico o de Investigador Independiente
- **Descripción:** Un artículo de divulgación técnica, científica o jurídica publicado por un profesor, investigador o estudiante en un blog personal, plataforma estática (ej. GitHub Pages) o Substack.
- **Riesgo:** Que sea catalogado erróneamente como "desinformación" o "fuente no confiable" al no tener el respaldo de una editorial académica multinacional.
- **Resolución en Senda:**
  - Se clasifica bajo el tipo de fuente: `web / análisis independiente`.
  - Si el autor incluye credenciales o enlace ORCID, se refleja en el panel de evidencia: `"Autoría: [Nombre] (Enlace académico verificado)"`.
  - El sistema analiza los enlaces salientes: si cita fuentes primarias (artículos de revistas indexadas con DOI, repositorios de código abierto, fallos de cortes), el panel destacará: `"Cita fuentes primarias: Sí (N enlaces a publicaciones académicas)"`.
  - No se le exige haber sido "revisado por pares" y se declara con honestidad: `"Tipo: Análisis independiente / Divulgación"`.

---

### Caso Límite 3: Sitio Web Satírico o de Humor (The Onion, El Mundo Today, Actualidad Panamericana)
- **Descripción:** Portales web cuyo propósito fundamental es la parodia, la sátira política y la ficción humorística.
- **Riesgo:** Que una nota paródica sea clasificada erróneamente como un intento malicioso de desinformación o engaño, o que sea bloqueada por algoritmos ciegos.
- **Resolución en Senda:**
  - Senda **nunca bloquea sitios satíricos**.
  - Si el dominio está reconocido en su propia descripción legal o editorial como portal satírico, se etiqueta explícitamente en la interfaz como: **`[Sátira / Humor]`**.
  - En el panel "¿Por qué veo esto?" se especifica: `"Tipo de contenido: Publicación satírica declarada. Los contenidos de este sitio web tienen fines cómicos o paródicos y no constituyen reportajes fácticos"`.
  - Se evita someter el contenido satírico a verificaciones solemnes fuera de contexto, preservando la libertad artística y humorística.

---

### Caso Límite 4: Medios Financiados o Controlados por un Estado
- **Descripción:** Medios de comunicación que reciben financiamiento total o parcial de fondos públicos, o que operan bajo control editorial de gobiernos (ej. BBC, RTVE, Deutsche Welle, Radio France Internationale, NPR, RT, CGTN, Telesur, TV Pública).
- **Riesgo:** Ocultar al lector la influencia geopolítica o financiera del gobierno emisor, o caer en la censura selectiva de medios estatales según la alineación diplomática del país donde opera el buscador.
- **Resolución en Senda:**
  - Senda **no censura ni bloquea medios estatales**, salvo que incurran en las cuatro causales de daño objetivo (malware activo, phishing comprobado, etc.).
  - La procedencia y el financiamiento estatal se declaran de manera simétrica y transparente para **todos los estados sin excepción**:
    - Si el medio cuenta con independencia editorial garantizada por ley o estatuto público (ej. corporaciones públicas con control parlamentario multipartidista): etiqueta visible **`[Medio de servicio público financiado por fondos estatales: [País]]`**.
    - Si el medio opera bajo control directo de la estructura ejecutiva del gobierno: etiqueta visible **`[Medio financiado o controlado por el gobierno de [País]]`**.
  - La asignación de la etiqueta se fundamenta en registros públicos de gobernanza de medios y se exhibe en el panel con enlace a la fuente que documenta la estructura institucional del medio.

---

## 4. Gobernanza, Versionado y Cambios a la Rúbrica

- Cualquier modificación a los factores, pesos, umbrales o criterios de interpretación de esta rúbrica requiere:
  1. Un incremento de versión semántica (ej. de `1.0.0` a `1.1.0` para ampliaciones compatibles, o a `2.0.0` para cambios estructurales).
  2. Publicación previa del borrador de modificación en el repositorio público con un período mínimo de comentarios de la comunidad de 30 días.
  3. Historial de cambios (*CHANGELOG*) documentado públicamente en `docs/RUBRICA_FUENTES.md`.
