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
4. **Gestión de Preferencias y Cookies Funcionales de Interfaz:**
   Para respetar la privacidad de las personas y garantizar la accesibilidad universal sin discriminación de entorno tecnológico:
   - **En navegadores con JavaScript:** Las preferencias seleccionadas (modo visual, idioma, región y filtros) se gestionan localmente en el cliente mediante `localStorage`.
   - **En clientes con scripts inactivos o navegadores en modo estricto (como Tor Browser en nivel *Safest* para búsqueda básica):** El servidor emite dos cookies técnicas funcionales de preferencia de interfaz:
     * `senda_theme`: almacena exclusivamente el valor de tema (`"light"` o `"dark"`).
     * `senda_lang`: almacena exclusivamente el código de idioma (`"es"`, `"en"`, etc.).
     * **Atributos técnicos:** `SameSite=Lax`, `Path=/`, `Max-Age=31536000` (1 año), con bandera `Secure` automática en conexiones directas HTTPS o detrás de proxy inverso (`X-Forwarded-Proto: https`, `Forwarded: proto=https`). El atributo `HttpOnly=False` se establece para permitir que clientes con JavaScript activo puedan sincronizar sus preferencias con `localStorage`; los clientes con JavaScript inactivo no dependen de esta lectura y transmiten sus opciones directamente mediante las cabeceras HTTP de cada petición.
     * **Finalidad exclusiva:** Mantener la coherencia visual y el idioma elegido al navegar o paginar resultados en clientes que no ejecutan scripts.
     * **Garantía estricta:** Estas cookies NO contienen identificadores de usuario, hashes de sesión, marcas temporales de rastreo ni datos personales. Jamás se emplean para correlacionar búsquedas ni se comparten con terceros.
5. **Autocompletado Local:**
   Las sugerencias de búsqueda se generan a partir de la memoria local del navegador o índices estáticos descargados, **sin enviar cada pulsación de teclado a servidores de terceros**.
6. **Política de Referencia Estricta (`no-referrer`):**
   Al hacer clic en un resultado orgánico, el navegador no transmite la URL de origen ni los términos de búsqueda ingresados al sitio de destino (`rel="noopener noreferrer"` y cabecera `Referrer-Policy: no-referrer`).
7. **Soporte de Búsqueda por POST:**
   Senda admite el envío de búsquedas a través de solicitudes HTTP `POST /search`, evitando que las palabras de búsqueda queden registradas en el historial local del navegador o en los logs de proxies intermediarios de la red.
8. **Funcionalidad Completa sin JavaScript:**
   La consulta básica, los resultados paginados, los filtros y los atajos operan mediante HTML semántico y CSS estándar, garantizando accesibilidad y resistencia ante entornos con scripts deshabilitados por seguridad.
   
   La portada utiliza JavaScript progresivo ligero para el cambio rápido de categorías mediante chips y atajos de teclado locales; en caso de no disponer de scripts, la búsqueda general procesa y envía la consulta directamente mediante formularios HTTP nativos.
9. **Arquitectura de Registros Transparentes (Server Logs Disclosure):**
   - **Nginx `senda_access.log`:** Emplea el formato soberano `0.0.0.0 - - [$time_local] "$request_method $uri $server_protocol" $status $body_bytes_sent "-"`. La dirección IP se anonimiza forzosamente a `0.0.0.0`, la ruta se trunca a `$uri` (omitiendo parámetros de consulta `?q=...` para no almacenar términos de búsqueda en disco) y la cabecera `Referer` se sustituye por guion (`"-"`).
   - **Nginx Redirección Puerto 80:** Se desactiva el registro de acceso (`access_log off;`) en el servidor de redirección hacia HTTPS para prevenir el almacenamiento involuntario de IPs en los registros globales del sistema.
   - **Nginx `senda_error.log` y Limitación de Tasa:** El nivel de error está configurado en `warn;` y las alertas de `limit_req` se degradan a nivel `notice;`, garantizando que las denegaciones por exceso de tasa no registren la dirección IP del cliente en disco.
   - **Servidor ASGI (Uvicorn) y Systemd (`journald`):** Senda desactiva el registro de acceso por petición (`access_log=False`) por defecto en la CLI de arranque, impidiendo que el journal del sistema operativo capture consultas de búsqueda en texto plano.
   - **Divulgación de Registro Histórico y Remediación:** Durante la fase de despliegue inicial previa a la implementación de mitigaciones de privacidad (entre el 9 de noviembre a las 04:20 UTC y el 12 de noviembre a las 14:00 UTC), la salida estándar del servidor de aplicaciones registró peticiones HTTP con términos de búsqueda en `journald` (con IP de cliente anonimizada a `0.0.0.0:0`), y los registros rotados de Nginx anteriores a la fecha conservaron cadenas completas de solicitud. Asimismo, el registro global por defecto de Nginx (`/var/log/nginx/access.log`) capturó direcciones IP de peticiones de borde y escáneres de red hasta el 13 de noviembre, fecha en que se desactivó dicho registro central (`access_log off;`) y se depuraron los archivos rotados residuales del disco local. El registro de peticiones en Uvicorn quedó desactivado a fecha de 13 de noviembre de 2026, el formato de Nginx fue restringido a `$uri` sin parámetros, y se eliminaron los registros históricos del disco local del servidor (la presencia en copias de seguridad remotas o instantáneas del proveedor de hosting previas a esta fecha no queda cubierta por este saneamiento local).
10. **Aislamiento de Privacidad y Enrutamiento en Noticias (Anti-Click-Tracking & Privacy Isolation):**
   En la vertical de noticias, Senda garantiza la máxima privacidad del usuario frente a intermediarios publicitarios. Todos los enlaces se sirven bajo una política estricta de aislamiento de cabeceras (`rel="noopener noreferrer"` y `referrerpolicy="no-referrer"`), garantizando que el navegador nunca transmita la consulta de búsqueda, la dirección IP de origen ni cabeceras referer al medio ni a intermediarios de red. Asimismo, los resultados priorizan feeds RSS directos de medios verificados y la base global abierta GDELT con enlaces limpios y directos al medio editorial emisor, asegurando que el usuario acceda de forma transparente al artículo concreto consultado preservando la autenticidad editorial.

---

## 3. Lo que Senda NO HACE

- ❌ **NO registra consultas de búsqueda (*Zero Query Logging*):** Las consultas se procesan en la memoria volátil del proceso durante el ciclo de vida de la petición HTTP y nunca se escriben en disco, bases de datos o archivos de registro.
- ❌ **NO almacena direcciones IP:** Las direcciones IP de conexión son descartadas o enmascaradas inmediatamente a nivel de servidor web y aplicación.
- ❌ **NO crea perfiles de comportamiento:** Senda no rastrea sesiones repetidas, no crea identidades de usuario, ni correlaciona búsquedas a lo largo del tiempo.
- ❌ **NO utiliza cookies de seguimiento, analítica ni de terceros:** Cero cookies de sesión de rastreo, cero cookies analíticas, cero píxeles de seguimiento. Únicamente se utilizan las dos cookies técnicas funcionales de interfaz descritas en el numeral 4 para persistencia técnica en clientes sin JavaScript.
- ❌ **NO incluye analítica de terceros ni balizas (*web beacons*):** Cero Google Analytics, cero píxeles de Meta, cero scripts de telemetría remota.
- ❌ **NO realiza cargas automáticas de recursos o imágenes remotas:** Las páginas de resultados no cargan miniaturas ni elementos multimedia directamente desde servidores de terceros (evitando que los servidores de origen capturen la IP del usuario). Se emplean marcadores visuales locales y enlaces directos explícitos. La política de seguridad CSP restringe estrictamente el origen de imágenes a `img-src 'self' data:`.
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

## 5. Aislamiento Estricto y Opt-In de Ciencia Abierta y Biblioteca (OpenAlex y Open Library)

Para impedir la fuga o correlación de consultas cotidianas hacia catálogos de literatura científica o bibliotecas externas:

1. **Inactivo por Defecto en Búsqueda General sin Términos Relevantes:** Durante las consultas generales o web (`category=all`), Senda no efectúa solicitudes salientes arbitrarias a OpenAlex.
2. **Activación Exclusiva por Intención Explícita:** La consulta saliente anonimizada hacia OpenAlex se emite cuando el usuario selecciona expresamente la vertical **Biblioteca** (`category=library`) o activa el parámetro de opt-in académico (`academic=true`).
3. **Caché Local y Protección de Presupuesto:** Cada consulta consume presupuestos de red de servidores públicos. Senda implementa memoria intermedia en caché volátil local (TTL de 1 hora) y limitadores de tasa de peticiones por minuto con ventanas deslizantes. Esto evita consultas duplicadas, minimiza la huella de red y maneja defensivamente códigos HTTP 409 y 429.
4. **Sin Rastreo ni Filtración de Identidad:** La petición saliente se origina exclusivamente desde el servidor proxy de Senda, utilizando una cabecera técnica de cortesía (`User-Agent` institucional). La IP del usuario, sus cookies, datos de navegación y huellas digitales son completamente omitidas.

---

## 6. Aislamiento Estricto y Opt-In de Redes Abiertas y Foros Federados (Fediverso, Bluesky y Lemmy)

Para garantizar que las consultas de búsqueda habituales no se filtren a nodos de redes sociales ni a directorios federados:

1. **Inactivo por Defecto en Búsqueda General:** Durante las consultas generales o web (`category=all`, `category=web`), Senda **NUNCA** contacta instancias de Mastodon (ActivityPub), endpoints de Bluesky (ATProto) ni instancias federadas de Lemmy.
2. **Activación Exclusiva por Vertical "Comunidad / Redes Abiertas" u Opt-in:** Las solicitudes hacia instancias federadas únicamente se despachan cuando el usuario pulsa explícitamente la pestaña **Comunidad / Redes Abiertas** (`category=community` o `category=social`) o activa la opción correspondiente.
3. **Anonimización Absoluta:** Las solicitudes se originan desde el backend proxy de Senda sin cookies, tokens de usuario ni cabeceras del cliente final. Solo se procesan contenidos declarados como públicos según el protocolo respectivo.

---

## 7. Vertical de Imágenes y Divulgación de Tokens en Openverse

1. **Wikimedia Commons:** Las consultas se canalizan directamente al endpoint de la API pública de Wikimedia Commons bajo User-Agent transparente institucional, sin cookies ni intermediarios.
2. **Openverse y Reto Cloudflare:** La API pública de Openverse opera detrás de la red de entrega de Cloudflare. En entornos de centros de datos (como servidores en la nube), las peticiones no autenticadas pueden ser interceptadas por desafíos anti-bot automáticos (`cf-mitigated: challenge`).
3. **Divulgación de Privacidad sobre Token Registrado:** Para habilitar consultas directas estables, el administrador puede proveer un token de acceso registrado (`SENDA_OPENVERSE_API_KEY`). **Compromiso y advertencia de privacidad:** La utilización de un token de API permite a la entidad proveedora (WordPress Foundation) asociar el conjunto de consultas salientes emitidas por la IP del proxy con la cuenta registrada de la aplicación. La IP del usuario final, sus huellas digitales y cookies jamás se transmiten.
4. **Almacenamiento Seguro de Credenciales:** Dicho token reside exclusivamente en el archivo de entorno seguro del sistema (`/etc/senda/senda.env` con permisos estrictos `600`), sin registrarse jamás en repositorios de código ni en el historial de versiones.

---

## 8. Síntesis Asistida Grounded (Cero Alucinaciones y Desactivada por Defecto)

1. **Desactivada por Defecto:** La síntesis asistida se encuentra inactiva en la configuración estándar del servidor (`ENABLE_AI_SYNTHESIS=False`).
2. **Fundamentación Estricta (*Grounded*):** Si se activa explícitamente, Senda prohíbe categóricamente generar afirmaciones sin respaldo. Toda afirmación debe citar obligatoriamente `[1]`, `[2]` vinculando al documento primario recuperado en la consulta.
3. **Rechazo Ético por Falta de Evidencia:** Si los resultados recuperados son insuficientes o no responden con certeza a la consulta, el sistema se rehúsa formalmente a responder en lugar de especular o inventar respuestas.
4. **Procesamiento del Lado del Servidor y Tor Browser:** La síntesis se genera y renderiza en el servidor mediante HTML semántico (`<aside>`), legible sin requerir JavaScript privativo ni telemetría.

---

## 8. Auditoría y Código Abierto

Todo el código de Senda está publicado bajo la licencia **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`). Cualquier usuario o auditor independiente tiene la libertad de inspeccionar, compilar, ejecutar y verificar que estas afirmaciones se correspondan estrictamente con la implementación en código.
