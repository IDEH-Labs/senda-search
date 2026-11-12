# Senda Search — Plan de Remediación Técnica y Ética

**Fecha de actualización:** 2026-11-11  
**Repositorio:** `https://codeberg.org/IDEH-Labs/senda-search`  
**Commit auditado inicial (Línea Base):** `ff05a753bfaf1de1087d4d748c5cad7023b96cdd`  
**Rama de trabajo:** `remediacion/p0-seguridad`  
**Licencia:** `GPL-3.0-or-later`  

---

## 1. Alcance Autorizado y Estado de Ejecución

* **Etapa 0 (Verificación e Inspección):** **Completada**.
* **Etapa 1 (Remediación P0 de Red y Privacidad Remota):** **Completada y Validada**.
* **Etapa 2 (Cookies, Preferencias y CSP Integral):** **Bloqueada** (Pendiente de autorización).
* **Etapa 3 (Políticas Editoriales, Anti-Slop y Supply Chain):** **Bloqueada** (Pendiente de autorización).
* **Etapa 4 (Calidad, Accesibilidad y Gobernanza):** **Bloqueada** (Pendiente de autorización).

---

## 2. Línea Base (Etapa 0)

* **Entorno:** Linux x86_64, Python 3.14.6, `pytest 9.2.0`, `httpx 0.28.1`, `httpcore 1.0.9`.
* **Pruebas de la suite original ejecutadas:** 207 pruebas.
* **Resultado de línea base:** 207 superadas, 0 fallidas, 0 omitidas en 64.43 segundos.

---

## 3. Matriz de Hallazgos y Estado tras Etapa 1

| ID | Hallazgo | Estado Inicial | Corrección en Etapa 1 | Estado Actual |
| :--- | :--- | :--- | :--- | :--- |
| **H1** | Retorno de `127.0.0.1` en dominios `.onion` en `network_guard.py` | **Confirmado** (Vulnerabilidad crítica SSRF) | Corregido y validado en entorno local controlado. `.onion` se prohíbe sin proxy SOCKS y nunca retorna loopback ni resuelve localmente. | **Corregido y validado (entorno local)** |
| **H2** | Encolado de enlaces salientes `.onion` sin proxy en `runner.py` | **Confirmado** (Vector de inducción SSRF) | Filtrado en `runner.py`: si no hay proxy Tor, los enlaces `.onion` se descartan. | **Corregido y validado** |
| **H3** | Pérdida de socket pinning en `fetcher.py` con proxy | **Confirmado** (Riesgo TOCTOU con proxy) | Documentado técnicamente; para no-.onion se preserva validación DNS local asumiendo el riesgo residual; para .onion se delega en proxy. | **Riesgo aceptado y documentado (Decisión D1)** |
| **H4** | Falta de dependencia `httpx[socks]` / `socksio` | **Confirmado** (`ImportError` al usar proxy) | Añadido `httpx[socks]>=0.27.0` en `pyproject.toml` y registrado en `SBOM.md`. | **Corregido y validado** |
| **H5** | Comportamiento HTTPX `socks5://` vs `socks5h://` | **Confirmado** (httpcore pasa hostname ATYP=3) | Verificado empíricamente con servidor SOCKS de prueba; se exige esquema SOCKS para `.onion`. | **Verificado y documentado** |
| **H6** | Exposición de DNS local previo a conexión por proxy | **Confirmado** (Decisión D1) | Conservada validación DNS local para destinos públicos no-.onion; prohibida para `.onion`. | **Mitigado (Decisión D1)** |
| **H7** | Carga automática de imágenes externas (Fuga de IP) | **Confirmado** (En fichas, imágenes y videos) | Eliminados tags `<img src="...">` externos; sustituidos por placeholders SVG locales y enlaces directos. | **Corregido y validado** |
| **H8** | Cookies funcionales no declaradas en `PRIVACY.md` | **Confirmado** | Registrado para Etapa 2. No modificado en Etapa 1. | **Pendiente (Etapa 2)** |
| **H9** | CSP permisiva (`img-src * data:`) | **Confirmado** | Restringido `img-src 'self' data:;`. Resto de CSP reservado para Etapa 2. | **Corregido parcialmente en img-src** |
| **H10** | Anti-slop vs política ética contra detectores IA | **Confirmado** | Registrado para Etapa 3. No modificado en Etapa 1. | **Pendiente (Etapa 3)** |
| **H11** | Denominación de síntesis determinista como IA | **Confirmado** | Registrado para Etapa 3. No modificado en Etapa 1. | **Pendiente (Etapa 3)** |
| **H12** | `docker-compose.yml` ausente y tag mutable en README | **Confirmado** | Registrado para Etapa 3. No modificado en Etapa 1. | **Pendiente (Etapa 3)** |
| **H13** | Enlace roto a `docs/ACCESSIBILITY.md` | **Confirmado** | Registrado para Etapa 4. No modificado en Etapa 1. | **Pendiente (Etapa 4)** |

---

## 4. Correcciones Realizadas en Etapa 1

### A. Seguridad de Red y Aislamiento de Destinos (Tarea 1.1)
1. **`src/senda/crawler/network_guard.py`:**
   - Métodos `is_onion_hostname()` y `validate_onion_format()`.
   - Se eliminó el retorno de `["127.0.0.1"]` para dominios `.onion`.
   - Si no se autoriza explícitamente el proxy SOCKS (`allow_onion=False`), cualquier resolución o validación de `.onion` lanza `SSRFSecurityViolation`.
   - Si `allow_onion=True`, se valida la sintaxis RFC 7686 y se retorna lista vacía de IPs (resolución remota delegada al demonio Tor, sin consulta DNS local).
2. **`src/senda/crawler/fetcher.py`:**
   - Detección estricta de proxies SOCKS autorizados (`socks5://`, `socks5h://`).
   - Rechazo de esquemas no admitidos para `.onion` (HTTP/HTTPS proxies no autorizados para `.onion`).
   - Validación anti-SSRF en URL inicial y en cada salto de redirección HTTP. Si una redirección intenta apuntar a localhost, rangos privados, metadatos o `.onion` sin proxy, se aborta inmediatamente.
   - Preservación de la firma de llamadas a `validate_url()` para total compatibilidad con pruebas existentes.
3. **`src/senda/crawler/runner.py`:**
   - Filtrado en el encolado de enlaces salientes: los dominios `.onion` se ignoran si no hay un proxy SOCKS configurado.
4. **`pyproject.toml` y `SBOM.md`:**
   - Declaración de `httpx[socks]>=0.27.0` y registro de `socksio==1.*` (MIT).

### B. Privacidad y Recursos Remotos (Tarea 1.2)
1. **`src/senda/ui/templates/results.html`:**
   - Se eliminaron las etiquetas `<img src="...">` remotas en las tres ubicaciones:
     * Ficha enciclopédica (`entity_card.thumbnail_url`).
     * Cuadrícula de imágenes (`item.media_url`).
     * Cuadrícula de videos (`item.media_url`).
   - Se reemplazaron por marcadores de posición SVG locales (`.entity-thumbnail-placeholder`, `.image-thumb-placeholder`, `.video-thumb-placeholder`).
   - Se preservan intactos los enlaces explícitos salientes (`<a href="...">`) con `rel="noopener noreferrer"`.
2. **`src/senda/ui/static/css/senda.css`:**
   - Estilos accesibles para los placeholders locales.
3. **`src/senda/api/app.py`:**
   - Restricción estricta de la directiva CSP: `img-src 'self' data:;` (eliminando el comodín `*`).
4. **`SECURITY.md` y `PRIVACY.md`:**
   - Sincronización técnica de las políticas de SSRF, CSP y recursos remotos.

### C. Cookies Funcionales de Interfaz y CSP Integral (Etapa 2)
1. **`src/senda/api/app.py`:**
   - Generación de nonce criptográfico único por petición (`secrets.token_hex(16)`).
   - Inyección del nonce en la cabecera `Content-Security-Policy`:
     * `script-src 'self' 'nonce-{csp_nonce}';` (eliminado `'unsafe-inline'` de scripts).
     * `object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none';`.
     * `style-src 'self' 'unsafe-inline';` (preservado como riesgo residual aceptado por conveniencia de desarrollo).
   - Propagación de `csp_nonce` al contexto de plantillas Jinja2.
   - Atributo `secure=is_secure` automático en `set_cookie` para `senda_theme` y `senda_lang` en peticiones directas HTTPS y detrás de proxies inversos (`X-Forwarded-Proto: https` y RFC 7239 `Forwarded: proto=https`).
2. **`src/senda/cli/main.py`:**
   - Configuración de Uvicorn con `proxy_headers=True, forwarded_allow_ips="*"` para terminación TLS en proxies inversos.
3. **`src/senda/ui/templates/base.html`:**
   - Se aplicó `nonce="{{ csp_nonce }}"` al bloque `<script>` inline institucional.
4. **`src/senda/ui/templates/index.html` y resultados:**
   - Se eliminaron todos los manejadores de eventos en línea (`onclick=`, etc.) en plantillas y diseños de resultados, unificando la interacción mediante listeners desacoplados en `i18n.js`.
5. **`PRIVACY.md`:**
   - Documentación exhaustiva y transparente de las dos cookies funcionales técnicas (`senda_theme` y `senda_lang`) requeridas para soporte Zero-JS y Tor Safest, con garantía formal de ausencia de identificadores, rastreo o correlación. Se aclara que `HttpOnly=False` se destina a sincronización opcional con scripts en clientes con JS, no para Zero-JS (que las envía vía cabeceras HTTP).
6. **`tests/test_etapa2_security_remediation.py`:**
   - 9 pruebas automatizadas que verifican directivas completas de CSP, rotación criptográfica de nonces por petición, renderizado de nonces en plantillas, ausencia de manejadores `on*` en páginas estáticas y dinámicas de resultados, verificación estática de plantillas en disco, atributos de cookies técnicas en HTTP/HTTPS, activación de `Secure` tras proxy inverso y rechazo de identificadores arbitrarios.

---

## 5. Resultados de Pruebas Automatizadas

* **Pruebas preexistentes (Línea base):** 207 (207 superadas, 0 regresiones en pruebas HTTP).
* **Pruebas de Etapa 1 (`tests/test_p0_security_remediation.py`):** 24 pruebas:
  * **21 pruebas de seguridad de red y anti-SSRF:** validación `.onion`, verificación de handshake SOCKS5 local (`ATYP=0x03`), proxy HTTP rechazado para `.onion`, manejo de proxy inaccesible (fail-closed sin fallback), revalidación en redirecciones (a otro `.onion`, a destino público, a loopback, a IP privada, a metadatos de nube y con esquemas no permitidos), bloqueo de rangos reservados/CGNAT, IPv4 mapeada en IPv6 y pinning anti-TOCTOU directo.
  * **3 pruebas de privacidad de recursos remotos:** ausencia de etiquetas `<img>` externas en resultados de imágenes y videos, presencia de placeholders SVG locales, y cabecera CSP estricta `img-src 'self' data:;`.
* **Pruebas de Etapa 2 (`tests/test_etapa2_security_remediation.py`):** 9 pruebas:
  * Directivas completas de CSP y anti-inyección.
  * Generación y unicidad de nonces criptográficos de 16 bytes.
  * Renderizado exacto del nonce en `<script nonce="...">`.
  * Ausencia de manejadores de eventos en línea (`onclick=`, etc.) en todas las páginas clave y rutas de resultados de búsqueda (`/search` en categorías `all`, `images`, `videos`, `news`, `library`).
  * Ausencia estática de manejadores de eventos o URIs `javascript:` en las plantillas HTML en disco.
  * Atributos de cookies técnicas (`senda_theme`, `senda_lang`) en HTTP (`SameSite=Lax`, `Path=/`, `Max-Age=31536000`).
  * Atributo `Secure` forzado en cookies cuando la petición se realiza por conexión directa HTTPS.
  * Atributo `Secure` forzado en cookies cuando la petición llega tras un proxy inverso con cabeceras `X-Forwarded-Proto: https` o `Forwarded: proto=https`.
  * Rechazo estricto de parámetros de cookie con valores o identificadores arbitrarios.
* **Total de pruebas en la suite actual:** **240 superadas (100% de éxito en ejecución de pruebas automatizadas).**
* **Avisos de ejecución (Warnings):** 1 aviso residual de deprecación en biblioteca externa (`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead`), originado en la importación de `starlette.testclient` en el entorno de pruebas, sin impacto en el código fuente de Senda.

---

## 6. Riesgos Residuales Técnicos y Limitaciones

1. **Riesgo TOCTOU y fuga DNS local en proxy para destinos públicos (no-.onion):** Conforme a la Decisión D1, se mantuvo la pre-validación DNS/IP local en el servidor antes de entregar la petición al proxy para evitar conexiones a redes privadas. Existe una ventana teórica de TOCTOU si el registro DNS cambia entre la comprobación local y la conexión del proxy, así como exposición de las consultas al resolvedor DNS local de la máquina anfitriona para dominios públicos.
2. **Entorno de pruebas y alcance empírico:** Las validaciones de SOCKS y `.onion` se ejecutaron sobre un servidor SOCKS5 simulado local y mocks controlados; no constituyen una prueba en la red Tor viva ni certifican el comportamiento ante demonios `tor` mal configurados o latencias de red extremas. Asimismo, las pruebas automatizadas HTTP verifican cabeceras y renderizado HTML, pero no sustituyen una verificación visual interactiva en múltiples navegadores reales.
3. **CSP `'unsafe-inline'` en `style-src` (Riesgo residual aceptado):** La directiva `script-src` ha sido completamente migrada a nonces criptográficos de un solo uso; sin embargo, `style-src` retiene `'unsafe-inline'` como un riesgo residual aceptado por conveniencia de desarrollo (evitando la refactorización inmediata de estilos dinámicos en clases estáticas o nonces). Amenaza: inyección teórica de CSS (exfiltración vía selectores de atributos o redressing); Mitigación sustancial: la restricción estricta de `img-src 'self' data;` y `default-src 'self'` impide que reglas CSS carguen recursos externos vía `url()`, bloqueando canales de exfiltración hacia terceros.
4. **Especificidad del entorno:** El entorno local de ejecución utiliza una distribución rolling-release (Gentoo) con Python 3.14.6 experimental; estos resultados deben ser reproducidos en entornos estándar (Python 3.12 / 3.13) en etapas de CI/CD.
