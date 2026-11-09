# Senda — Política y Arquitectura de Privacidad (Privacy Architecture)

**Identificador de Licencia SPDX:** `GPL-3.0-or-later`  
**Idioma Primario de Referencia:** Español (Colombia)  
**Fecha de Actualización:** Noviembre 2026  

---

## 1. Declaración de Principios y Marco Ético

La privacidad en **Senda** no es una promesa comercial ni una declaración de intenciones: es una **restricción arquitectónica inmutable**. El sistema ha sido diseñado desde cero bajo los principios de Privacidad por Diseño y por Defecto (*Privacy by Design & by Default*), alineado con la filosofía de software libre de la Free Software Foundation (FSF) y los principios rectores del tratamiento de datos personales de la **Ley Estatutaria 1581 de 2012 de Colombia** y el **Reglamento General de Protección de Datos (RGPD / GDPR - Reglamento UE 2016/679)**.

> **Aviso de transparencia legal:** El cumplimiento descrito a continuación constituye una especificación técnica y arquitectónica de ingeniería de software; no constituye asesoría jurídica formal.

---

## 2. Lo que Senda HACE

1. **Anonimización y Limpieza de Cabeceras en el Proxy:**
   Cuando Senda consulta adaptadores externos configurados por el administrador (instancia local de SearXNG, Brave Search API o Mojeek API), actúa como un proxy ciego. Elimina cabeceras identificadoras del usuario final (`X-Forwarded-For`, `Client-IP`, `User-Agent` del cliente, cookies) y sustituye la petición por una petición genérica de servidor.
2. **Normalización Transparente de Resultados:**
   Cada resultado devuelto al usuario es normalizado bajo un esquema neutral:
   `{ título, url, fragmento, fuente, fecha, idioma, tipo, es_patrocinado, por_qué_veo_esto }`.
3. **Botón de Transparencia "¿Por qué veo esto?":**
   Cada enlace muestra el proveedor de origen (Índice Soberano FTS5, SearXNG, Brave, Mojeek), la fecha de indexación si está disponible, y si ha intervenido algún filtro o lente local aplicado por el usuario. Si no hay datos adicionales de ordenamiento, el sistema lo indica explícitamente sin inventar explicaciones.
4. **Almacenamiento Estrictamente Local en el Dispositivo del Usuario:**
   Toda preferencia (modo visual claro/oscuro/alto contraste, densidad compacta/cómoda, idioma de interfaz, filtros de región y lentes personalizados de reordenamiento de dominios) se almacena única y exclusivamente en el navegador del usuario (`localStorage`). Jamás se envían al servidor ni se guardan en bases de datos remotas.
5. **Autocompletado Local:**
   Las sugerencias de búsqueda se generan a partir de la memoria local del navegador o índices estáticos descargados, **sin enviar cada pulsación de teclado a servidores de terceros**.
6. **Política de Referencia Estricta (`no-referrer`):**
   Al hacer clic en un resultado orgánico, el navegador no transmite la URL de origen ni los términos de búsqueda ingresados al sitio de destino (`rel="noopener noreferrer"` y cabecera `Referrer-Policy: no-referrer`).
7. **Soporte de Búsqueda por POST:**
   Senda admite el envío de búsquedas a través de solicitudes HTTP `POST /search`, evitando que las palabras de búsqueda queden registradas en el historial local del navegador o en los logs de proxies intermediarios de la red.
8. **Funcionalidad Completa sin JavaScript:**
   La consulta básica, los resultados paginados, los filtros y los atajos funcionan al 100% mediante HTML semántico y CSS estándar, garantizando accesibilidad y resistencia ante entornos con scripts deshabilitados por seguridad.

---

## 3. Lo que Senda NO HACE

- ❌ **NO registra consultas de búsqueda (*Zero Query Logging*):** Las consultas se procesan en la memoria volátil del proceso durante el ciclo de vida de la petición HTTP y nunca se escriben en disco, bases de datos o archivos de registro.
- ❌ **NO almacena direcciones IP:** Las direcciones IP de conexión son descartadas o enmascaradas inmediatamente a nivel de servidor web y aplicación.
- ❌ **NO crea perfiles de comportamiento:** Senda no rastrea sesiones repetidas, no crea identidades de usuario, ni correlaciona búsquedas a lo largo del tiempo.
- ❌ **NO utiliza cookies de seguimiento ni no esenciales:** Cero cookies de sesión de rastreo, cero cookies analíticas, cero cookies de terceros.
- ❌ **NO incluye analítica de terceros ni balizas (*web beacons*):** Cero Google Analytics, cero píxeles de Meta, cero scripts de telemetría remota.
- ❌ **NO depende de CDNs externas:** Todos los estilos, tipografías SVG y scripts se sirven localmente desde el propio servidor de Senda, impidiendo que terceros rastreen las descargas de recursos.
- ❌ **NO realiza redirecciones de rastreo de clics:** Los enlaces apuntan directamente a la URL de destino final sin pasar por pasarelas intermedias de medición de tasa de clics (CTR).
- ❌ **NO aplica burbujas de filtro ni personalización oculta:** El orden de los resultados responde a criterios objetivos (BM25 y relevancia lexical del proveedor) y a las reglas configuradas explícitamente por el usuario (lentes/goggles). No existen sesgos algorítmicos basados en suposiciones sobre el perfil del usuario.
- ❌ **NO presenta contenido publicitario disfrazado ni personalizado:** Por defecto, los resultados no contienen anuncios. Si un proveedor externo incluye un resultado patrocinado, este se etiqueta de forma inequívoca como `[Anuncio]`, separado visualmente del contenido orgánico y sin rastreo conductual.
- ❌ **NO hace scraping de motores de búsqueda que lo prohíban en sus Términos de Servicio:** Senda solo utiliza fuentes soberanas locales o APIs oficiales respetando las cuotas y condiciones de uso.

---

## 4. Límites Honestos del Sistema

La honestidad hacia el usuario exige transparentar los límites técnicos de cualquier arquitectura:

1. **Tratamiento por Proveedores Externos:**
   Cuando el administrador habilita proveedores externos como Brave Search o Mojeek, la consulta textual (los términos buscados) debe ser transmitida a través de la API correspondiente para obtener los resultados. Aunque Senda elimina la dirección IP y los datos del navegador del usuario final (actuando como escudo intermedio), el proveedor externo recibe la consulta procedente de la IP de nuestro servidor proxy.
2. **Navegación Saliente:**
   Una vez que el usuario hace clic en un resultado y abandona Senda para ingresar al sitio web de destino, la política de privacidad de dicho sitio web entra en vigor. Senda no puede proteger la privacidad del usuario dentro de plataformas de terceros, si bien utiliza `rel="noopener noreferrer"` para no revelar de qué búsqueda proviene.
3. **Redirecciones Directas (Bangs y Mapas):**
   Cuando el usuario invoca un atajo tipográfico (ej. `!osm`, `!w`, `!fsf`), Senda efectúa una redirección directa HTTP 307 al servicio correspondiente. A partir de ese momento, la interacción ocurre directamente entre el usuario y la plataforma destino elegida.

---

## 5. Aislamiento Estricto y Opt-In de Ciencia Abierta (OpenAlex)

Para impedir la fuga o correlación de consultas cotidianas hacia catálogos de literatura científica externos:

1. **Inactivo por Defecto en Búsqueda General:** Durante las consultas generales o web (`category=all`, `category=web`), Senda **NUNCA** realiza solicitudes salientes a la API de OpenAlex.
2. **Activación Exclusiva por Intención Explícita:** La consulta saliente anonimizada hacia OpenAlex únicamente se emite cuando el usuario selecciona expresamente la vertical **Biblioteca** (`category=library`) o activa el parámetro explícito de opt-in académico (`academic=true`).
3. **Caché Local y Protección de Presupuesto:** Cada consulta de lista a OpenAlex consume 1 crédito de API. Senda implementa una memoria intermedia en caché volátil local (TTL de 1 hora) y limitador de tasa de peticiones por minuto. Esto evita consultas duplicadas, minimiza la huella de red y maneja defensivamente códigos HTTP 409 y 429.
4. **Sin Rastreo ni Filtración de Identidad:** La petición saliente se origina exclusivamente desde el servidor proxy de Senda, utilizando una cabecera técnica de cortesía (`User-Agent` institucional). La IP del usuario, sus cookies, datos de navegación y huellas digitales son completamente omitidas.

---

## 6. Aislamiento Estricto y Opt-In de Redes Abiertas (Fediverso y Bluesky)

Para garantizar que las consultas de búsqueda habituales no se filtren a nodos de redes sociales ni a directorios federados:

1. **Inactivo por Defecto en Búsqueda General:** Durante las consultas generales o web (`category=all`, `category=web`), Senda **NUNCA** contacta instancias de Mastodon (ActivityPub) ni endpoints de Bluesky (ATProto).
2. **Activación Exclusiva por Vertical "Redes Abiertas" u Opt-in:** Las solicitudes hacia instancias federadas únicamente se despachan cuando el usuario pulsa explícitamente la pestaña **Redes Abiertas** (`category=social`) o invoca atajos tipográficos soberanos (`!masto`, `!bsky`).
3. **Anonimización Absoluta:** Las solicitudes se originan desde el backend proxy de Senda sin cookies, tokens de usuario ni cabeceras del cliente final. Solo se procesan contenidos declarados como públicos según el protocolo respectivo.

---

## 7. Síntesis Asistida Grounded (Cero Alucinaciones y Desactivada por Defecto)

1. **Desactivada por Defecto:** La síntesis asistida se encuentra inactiva en la configuración estándar del servidor (`ENABLE_AI_SYNTHESIS=False`).
2. **Fundamentación Estricta (*Grounded*):** Si se activa explícitamente, Senda prohíbe categóricamente generar afirmaciones sin respaldo. Toda afirmación debe citar obligatoriamente `[1]`, `[2]` vinculando al documento primario recuperado en la consulta.
3. **Rechazo Ético por Falta de Evidencia:** Si los resultados recuperados son insuficientes o no responden con certeza a la consulta, el sistema se rehúsa formalmente a responder en lugar de especular o inventar respuestas.
4. **Compatibilidad Total LibreJS y Tor Browser:** Se procesa y renderiza al 100% en el servidor mediante HTML semántico nativo (`<aside>`), funcionando sin una sola línea de JavaScript privativo y sin telemetría.

---

## 8. Auditoría y Código Abierto

Todo el código de Senda está publicado bajo la licencia **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`). Cualquier usuario o auditor independiente tiene la libertad de inspeccionar, compilar, ejecutar y verificar que estas afirmaciones se correspondan estrictamente con la implementación en código.
