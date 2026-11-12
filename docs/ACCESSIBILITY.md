# Senda — Política y Auditoría de Accesibilidad (WCAG 2.1 / 2.2 AA)

SPDX-License-Identifier: GPL-3.0-or-later  
SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

---

## 1. Compromiso Ético con la Accesibilidad Universal

Para **Senda**, la accesibilidad web no es una capa cosmética ni una concesión secundaria; es una dimensión innegociable de la soberanía digital y los derechos humanos fundamentales. Un buscador que excluye a personas con discapacidad o a usuarios de entornos con tecnologías de asistencia vulnera su principio ético fundacional de universalidad y no discriminación.

Senda está diseñado y auditado para cumplir y superar las pautas de las **Pautas de Accesibilidad para el Contenido Web (WCAG 2.1 y 2.2) en su nivel AA**.

---

## 2. Dimensiones Técnicas de Accesibilidad Implementadas

### 2.1. Navegación Completa sin JavaScript (Zero-JS)
* **Resiliencia Operativa:** El 100% de la funcionalidad esencial de búsqueda, consulta, paginación, filtros de categorías, cambio de modo de visualización e idioma de interfaz opera exclusivamente mediante HTML5 semántico estándar y envío de formularios HTTP GET/POST nativos.
* **Compatibilidad Estricta:** Compatible con **GNU LibreJS**, navegación en modo *Safest* de **Tor Browser**, navegadores en modo texto (`w3m`, `lynx`) y entornos donde la ejecución de scripts está restringida por políticas de seguridad o limitaciones de hardware.

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

## 3. Matriz de Verificación WCAG

| Criterio WCAG 2.1 / 2.2 | Nivel | Estado en Senda | Verificación Técnica |
| :--- | :--- | :--- | :--- |
| **1.1.1 Contenido no textual** | A | **Cumplido** | Placeholders SVG locales accesibles, iconos con `aria-hidden`, enlaces salientes con texto explícito. |
| **1.3.1 Información y relaciones** | A | **Cumplido** | HTML5 semántico (`<main>`, `<header>`, `<nav>`, `<aside>`), formularios con `<label>` asociados. |
| **1.4.3 Contraste mínimo** | AA | **Cumplido** | Contraste superior a 4.5:1 verificado en paletas claro y oscuro. |
| **1.4.11 Contraste no textual** | AA | **Cumplido** | Bordes de campos de entrada y botones con contraste superior a 3:1. |
| **2.1.1 Teclado** | A | **Cumplido** | Operable al 100% mediante teclado (`Tab`, `Shift+Tab`, `Enter`, `Space`). |
| **2.1.2 Sin trampas de teclado** | A | **Cumplido** | El foco se mueve libremente por el documento sin quedar retenido. |
| **2.4.1 Evitar bloques** | A | **Cumplido** | Enlace de salto al contenido principal disponible en todas las vistas. |
| **2.4.7 Foco visible** | AA | **Cumplido** | Indicador de foco evidente en todos los elementos interactivos. |
| **3.1.1 Idioma de la página** | A | **Cumplido** | Atributo `lang="..."` dinámico en la etiqueta `<html>` sincronizado con la preferencia del usuario. |
| **4.1.2 Nombre, función, valor** | A | **Cumplido** | Controles de interfaz nativos sin sobrecarga de widgets opacos. |

---

## 4. Reporte de Incidencias de Accesibilidad

Si encuentras cualquier barrera de accesibilidad o dificultad técnica al interactuar con Senda utilizando lectores de pantalla, navegadores en modo texto o tecnologías de asistencia, por favor repórtalo para su priorización inmediata:

* **Correo:** **contact@ideh.top** (Asunto: *Reporte de Accesibilidad Senda*)
* **Repositorio oficial:** <https://codeberg.org/IDEH-Labs/senda-search/issues>
* **Compromiso:** Respuesta técnica en menos de 48 horas y remediación prioritaria en el ciclo de mantenimiento.
