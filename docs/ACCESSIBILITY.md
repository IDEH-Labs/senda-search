# Senda — Política y Auditoría de Accesibilidad (WCAG 2.1 / 2.2 AA)

SPDX-License-Identifier: GPL-3.0-or-later  
SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

---

## 1. Compromiso Ético con la Accesibilidad Universal

Para **Senda**, la accesibilidad web no es una capa cosmética ni una concesión secundaria; es una dimensión innegociable de la soberanía digital y los derechos humanos fundamentales. Un buscador que excluye a personas con discapacidad o a usuarios de entornos con tecnologías de asistencia vulnera su principio ético fundacional de universalidad y no discriminación.

Senda está diseñado y auditado para cumplir y superar las pautas de las **Pautas de Accesibilidad para el Contenido Web (WCAG 2.1 y 2.2) en su nivel AA**.

---

## 2. Dimensiones Técnicas de Accesibilidad Implementadas

### 2.1. Navegación sin JavaScript (Zero-JS con degradación funcional) y Alcance Técnico
* **Resiliencia Operativa:** El flujo nuclear de búsqueda, paginación, filtros de categorías en la vista de resultados (`/search?q=...&category=...`), selección de idioma por URL y modo de lectura opera exclusivamente mediante HTML5 semántico estándar y peticiones HTTP GET/POST nativas sin requerir la ejecución de scripts.
* **Limitación en Página de Inicio (`/`):** En la portada de inicio, los chips de cambio rápido de categoría (`.cat-chip`) son elementos `<button type="button">` vinculados a un manejador en `static/js/i18n.js` para alternar el campo oculto `category`. En entornos con JavaScript deshabilitado (como Tor Browser *Safest* o navegadores en modo texto), el formulario inicial se envía con la categoría general (`all`), pudiendo el usuario refinar la categoría en la página de resultados subsiguiente o mediante atajos (*bangs*, e.g., `!images`).
* **Compatibilidad:** Compatible con navegación en modo *Safest* de **Tor Browser**, navegadores en modo texto (`w3m`, `lynx`) y navegadores sin soporte para scripts.

### 2.2. Contraste y Modos de Visualización
* **Relación de Contraste:** Todos los elementos de texto y componentes interactivos superan la relación de contraste mínima de **4.5:1** para texto normal y **3:1** para texto grande y elementos de interfaz de usuario.
* **Modos Soportados:**
  - **Modo Oscuro (Dark Theme):** Fondo `#080c14`, texto `#f1f5f9` (Contraste 16.8:1).
  - **Modo Claro (Light Theme):** Fondo `#ffffff`, texto `#0f172a` (Contraste 17.5:1).
  - **Modo de Alto Contraste:** Respeto automático a la directiva del sistema operativo `@media (prefers-contrast: more)`.
* **Ausencia de Dependencia Cromática:** La información crítica nunca se comunica exclusivamente mediante color; se complementa con iconos vectoriales SVG accesibles, etiquetas textuales y atributos ARIA.

### 2.3. Estructura Semántica y Lectores de Pantalla
* **Jerarquía de Encabezados:** Cada página cuenta con una estructura lógica estricta (`<h1>` único, seguido de `<h2>` y `<h3>` jerárquicos) que permite la navegación fluida por secciones en lectores de pantalla (NVDA, Orca, VoiceOver, JAWS).
* **Regiones y Roles ARIA:**
  - `role="search"` para los formularios principales de consulta.
  - `role="region"` y `role="navigation"` para paneles de filtros y paginación.
  - `aria-label` descriptivos en botones y selectores.
* **Texto Alternativo:** Marcadores de posición locales SVG y elementos visuales incluyen etiquetas `aria-hidden="true"` para elementos decorativos y atributos `alt` informativos en imágenes de contenido.

### 2.4. Navegación por Teclado y Enlaces de Salto (*Skip Links*)
* **Foco Visible:** Indicadores de foco visual claros y de alto contraste (`outline: 2px solid var(--accent)`) en todos los elementos interactivos.
* **Enlace de Salto:** Se provee un enlace oculto accesible al tabular (*Skip to main content*) que permite saltar directamente a los resultados de búsqueda evitando la cabecera.
* **Orden Lógico de Tabulación:** El orden del DOM coincide exactamente con el flujo visual de la página, sin trampas de teclado (*keyboard traps*).

---

## 3. Matriz de Verificación y Estado de Cumplimiento

### 3.1. Propiedades Verificadas Empírica y Técnicamente en el Código Base

| Dimensión Técnica | Criterio WCAG | Estado | Evidencia y Verificación en el Repositorio |
| :--- | :--- | :--- | :--- |
| **Búsqueda sin JavaScript** | 2.1.1 (A) | **Parcialmente verificado** | Búsqueda principal, paginación y lectura funcionan con formularios HTTP GET nativos sin scripts. La selección inicial de categoría por chips en la portada y el guardado de preferencias en localStorage emplean mejora progresiva en JS. |
| **Estructura Semántica** | 1.3.1 (A) | **Verificado** | Uso consistente de elementos semánticos de HTML5 (`<main>`, `<header>`, `<nav>`, `<section>`), jerarquía estricta de encabezados y controles de formulario con `<label for="...">` asociados. |
| **Contraste de Paleta** | 1.4.3 / 1.4.11 (AA) | **Verificado** | Relación de contraste calculada matemáticamente en `static/css/main.css`: Modo Claro 17.5:1 (`#0f172a` sobre `#ffffff`), Modo Oscuro 16.8:1 (`#f1f5f9` sobre `#080c14`). |
| **Indicadores de Foco** | 2.4.7 (AA) | **Verificado** | Reglas `:focus-visible` explícitas en CSS (`outline: 2px solid var(--accent)`) sin `outline: none` en elementos interactivos. |
| **Idioma del Documento** | 3.1.1 (A) | **Verificado** | Atributo `<html lang="...">` generado dinámicamente por la plantilla Jinja2 (`app.py` / `index.html` / `results.html`) en concordancia con la preferencia seleccionada. |
| **Contenido no textual** | 1.1.1 (A) | **Verificado** | Ausencia de imágenes externas de terceros; iconos vectoriales SVG marcados con `aria-hidden="true"`, placeholders accesibles con texto descriptivo. |
| **Sin trampas de teclado** | 2.1.2 (A) | **Verificado** | Estructura DOM lineal sin scripts de captura de foco; tabulación secuencial predecible. |

### 3.2. Alcance, Limitaciones y Pruebas con Usuarios Reales

> [!NOTE]
> **Declaración de Transparencia Metodológica:**  
> La presente especificación certifica la conformidad del diseño arquitectónico, las plantillas HTML5 y las hojas de estilo CSS con las directrices WCAG 2.1/2.2 Nivel AA. No obstante, **no sustituye la validación de campo con usuarios humanos y diversidad de tecnologías de asistencia**. Las pruebas interactivas exhaustivas con personas usuarias de lectores de pantalla específicos (Orca en Linux, NVDA/JAWS en Windows, VoiceOver en macOS/iOS) y líneas braille están planificadas como un proceso de auditoría continua en coordinación con la comunidad de usuarios de software libre.

---

## 4. Reporte de Incidencias de Accesibilidad

Si encuentras cualquier barrera de accesibilidad o dificultad técnica al interactuar con Senda utilizando lectores de pantalla, navegadores en modo texto o tecnologías de asistencia, por favor repórtalo para su priorización inmediata:

* **Correo:** **contact@ideh.top** (Asunto: *Reporte de Accesibilidad Senda*)
* **Repositorio oficial:** <https://codeberg.org/IDEH-Labs/senda-search/issues>
* **Compromiso:** Respuesta técnica en menos de 48 horas y remediación prioritaria en el ciclo de mantenimiento.
