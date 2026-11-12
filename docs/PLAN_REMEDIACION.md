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

---

## 5. Resultados de Pruebas Automatizadas

```text
============================= test session starts ==============================
collected 231 items

tests/test_academic_providers.py ............                            [  5%]
tests/test_anti_slop.py .                                                [  5%]
tests/test_api.py ....................................................   [ 28%]
tests/test_calculator.py ........                                        [ 32%]
tests/test_canonical.py ........                                         [ 35%]
tests/test_cli.py .....                                                  [ 37%]
tests/test_clustering.py ...                                             [ 38%]
tests/test_converters.py ...                                             [ 40%]
tests/test_countries.py ...                                              [ 41%]
tests/test_crawler_runner.py ...                                         [ 42%]
tests/test_curated_crawl_and_hybrid_scoring.py ....                      [ 44%]
tests/test_extractor.py .........                                        [ 48%]
tests/test_fediverse_bluesky.py .........                                [ 52%]
tests/test_fetcher.py .......                                            [ 55%]
tests/test_goggles.py ......                                             [ 58%]
tests/test_grounded_synthesis.py ........                                [ 61%]
tests/test_indexer.py .............                                      [ 67%]
tests/test_language_results.py ..                                        [ 68%]
tests/test_network_guard.py ...........                                  [ 72%]
tests/test_news_and_claim_review.py ............                         [ 77%]
tests/test_news_and_images_providers.py ............                     [ 83%]
tests/test_openalex.py ......                                            [ 85%]
tests/test_p0_security_remediation.py ........................           [ 96%]
tests/test_providers.py .......                                          [ 99%]
tests/test_ranking.py ........                                           [100%]
...
======================== 231 passed, 2 warnings in 63.88s =======================
```

* **Pruebas preexistentes (Línea base):** 207 (207 superadas, 0 regresiones).
* **Pruebas nuevas añadidas (`tests/test_p0_security_remediation.py`):** 24 pruebas:
  * **21 pruebas de seguridad de red y anti-SSRF:** validación `.onion`, verificación de handshake SOCKS5 local (`ATYP=0x03`), proxy HTTP rechazado para `.onion`, manejo de proxy inaccesible (fail-closed sin fallback), revalidación en redirecciones (a otro `.onion`, a destino público, a loopback, a IP privada, a metadatos de nube y con esquemas no permitidos), bloqueo de rangos reservados/CGNAT, IPv4 mapeada en IPv6 y pinning anti-TOCTOU directo.
  * **3 pruebas de privacidad de recursos remotos:** ausencia de etiquetas `<img>` externas en resultados de imágenes y videos, presencia de placeholders SVG locales, y cabecera CSP estricta `img-src 'self' data:;`.
* **Total de pruebas en la suite actual:** **231 superadas (100% de éxito en 63.88s).**

---

## 6. Riesgos Residuales Técnicos y Limitaciones

1. **Riesgo TOCTOU y fuga DNS local en proxy para destinos públicos (no-.onion):** Conforme a la Decisión D1, se mantuvo la pre-validación DNS/IP local en el servidor antes de entregar la petición al proxy para evitar conexiones a redes privadas. Existe una ventana teórica de TOCTOU si el registro DNS cambia entre la comprobación local y la conexión del proxy, así como exposición de las consultas al resolvedor DNS local de la máquina anfitriona para dominios públicos.
2. **Entorno de pruebas y alcance empírico:** Las validaciones de SOCKS y `.onion` se ejecutaron sobre un servidor SOCKS5 simulado local y mocks controlados; no constituyen una prueba en la red Tor viva ni certifican el comportamiento ante demonios `tor` mal configurados o latencias de red extremas.
3. **CSP `'unsafe-inline'` y protección XSS:** Se mantiene temporalmente en `style-src` y `script-src` para no romper la interfaz visual existente. La protección del navegador frente a inyecciones XSS complejas sigue siendo débil mientras esta directiva no se reemplace por nonces criptográficos en la Etapa 2.
4. **Cookies funcionales de preferencia:** Siguen operando para garantizar accesibilidad en entornos Zero-JS y Tor; su armonización en `PRIVACY.md` corresponde a la Etapa 2.
5. **Especificidad del entorno:** El entorno local de ejecución utiliza una distribución rolling-release (Gentoo) con Python 3.14.6 experimental; estos resultados deben ser reproducidos en entornos estándar (Python 3.12 / 3.13) en etapas de CI/CD.
