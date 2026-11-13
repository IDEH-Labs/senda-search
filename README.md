# Senda — Motor de Búsqueda Web Ético, Rápido y Transparente

[![Licencia: GPL v3+](https://img.shields.io/badge/Licencia-GPL%20v3%2B-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Privacidad: Cero Rastreo](https://img.shields.io/badge/Privacidad-Cero%20Rastreo-brightgreen.svg)](PRIVACY.md)
[![Pruebas: 150 Aprobadas](https://img.shields.io/badge/Pruebas-150%20Aprobadas-success.svg)](tests/)
[![Accesibilidad: WCAG 2.2 AA](https://img.shields.io/badge/Accesibilidad-WCAG%202.2%20AA-purple.svg)](docs/ACCESSIBILITY.md)

> **Senda** es una interfaz y motor de búsqueda web rápida, limpia, privada y transparente que devuelve el control total de la información al usuario. Desarrollado por **IDEH Labs** bajo la filosofía del Software Libre (FSF).

---

## 🎯 Jerarquía de Valores de Senda

1. **Honestidad hacia el usuario:** Sin datos ocultos, sin explicaciones inventadas, sin sesgos disimulados.
2. **Privacidad estricta:** Cero registro de consultas, cero almacenamiento de IP, cero cookies de seguimiento.
3. **Utilidad de los resultados:** Fusión soberana y multi-proveedor con esquema normalizado.
4. **Accesibilidad universal:** Diseñado con WCAG 2.2 AA como objetivo (auditoría formal con usuarios y lectores de pantalla pendiente); navegación por teclado y degradación funcional para búsqueda sin JavaScript.
5. **Velocidad y ligereza:** Presupuesto frontend <100 KB JS comprimido, LCP < 1,5 s en 4G.
6. **Estética minimalista atemporal:** Jerarquía visual clara, densidad ajustable (cómoda/compacta), sin imitar marcas comerciales.

---

## 🏗️ Arquitectura y Estructura del Proyecto

Senda implementa un frontend ultraligero con mejora progresiva y un backend proxy delgado con la interfaz `SearchProvider` intercambiable.

```
senda-search/
├── src/
│   └── senda/
│       ├── api/               # API REST FastAPI, enrutamiento, seguridad HTTP y proxy
│       │   ├── app.py         # Endpoints: /, /search, /how-it-works, /about, /health
│       │   └── ...
│       ├── providers/         # Adaptadores intercambiables de SearchProvider
│       │   ├── __init__.py    # Exportación unificada de proveedores
│       │   ├── base.py        # Esquema SearchResultItem y clase abstracta SearchProvider
│       │   ├── internal.py    # Adaptador SQLite FTS5 soberano local
│       │   ├── searxng.py     # Adaptador SearXNG autoalojado
│       │   ├── brave.py       # Adaptador Brave Search API (oficial, sin rastreo)
│       │   ├── mojeek.py      # Adaptador Mojeek API (buscador independiente)
│       │   └── aggregator.py  # Agregador asíncrono, lentes de usuario y atajos bang
│       ├── crawler/           # Rastreador ético asíncrono RFC 9309, anti-SSRF
│       ├── extractor/         # Extractor semántico DOM y deduplicación SHA-256
│       ├── frontier/          # Cola de prioridades, anti-trampas de araña
│       ├── indexer/           # Motor de almacenamiento SQLite FTS5 con BM25
│       ├── ranking/           # Ponderación lexical y generador de fragmentos
│       ├── ui/                # Frontend minimalista sin dependencias pesadas
│       │   ├── templates/     # Plantillas Jinja2 semánticas (index, results, how_it_works, base)
│       │   └── static/        # CSS puro sin frameworks y scripts sin dependencias externas
│       │       ├── css/senda.css   # Tokens de diseño, modo claro/oscuro/alto contraste, densidad
│       │       ├── js/i18n.js      # Internacionalización local, lentes y atajos
│       │       └── img/            # Logotipos y favicons vectoriales SVG
│       └── config.py          # Configuración de variables de entorno y defaults
├── tests/                     # Suite de pruebas unitarias y de integración (245+ pruebas)
│   ├── test_providers.py      # Pruebas de normalización, agregador, lentes y bangs
│   ├── test_indexer.py        # Pruebas FTS5
│   └── ...
├── Dockerfile                 # Contenedor mínimo sin privilegios de root (Python 3.12-slim)
├── docker-compose.yml         # Despliegue conjunto y reproducible de Senda y SearXNG
├── PRIVACY.md                 # Declaración auditada de privacidad y límites técnicos
├── SECURITY.md                # Política de seguridad, SSRF pinning y modelo de amenazas
├── README.md                  # Manual y documentación principal
└── pyproject.toml             # Especificación de paquete y dependencias auditables
```

---

## 🚀 Despliegue Rápido

### Opción 1: Entorno de Desarrollo Local

```bash
# Clonar el repositorio oficial desde Codeberg
git clone https://codeberg.org/IDEH-Labs/senda-search.git
cd senda-search

# Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Ejecutar la suite completa de pruebas
pytest -v

# Iniciar servidor web
senda serve --host 127.0.0.1 --port 8000
```

### Opción 2: Despliegue Reproducible con Docker Compose

Para levantar Senda junto con una instancia aislada de SearXNG con fijación determinista de imágenes:

```bash
# Iniciar servicios en segundo plano
docker compose up -d

# Verificar estado y logs
docker compose ps
docker compose logs -f senda
```

O si prefieres ejecutar SearXNG manualmente con una versión inmutable fijada:

```bash
# 1. Ejecutar SearXNG en un contenedor Docker con tag inmutable
docker run -d \
  --name senda-searxng \
  -p 8888:8080 \
  -e "SEARXNG_BASE_URL=http://localhost:8888" \
  -e "SEARXNG_SECRET=$(openssl rand -hex 32)" \
  --restart unless-stopped \
  searxng/searxng:2024.11.1-7b0be77

# 2. Configurar la URL de SearXNG en las variables de entorno de Senda
export SENDA_SEARXNG_URL="http://127.0.0.1:8888"

# 3. (Opcional) Configurar claves para Brave Search o Mojeek
export SENDA_BRAVE_API_KEY="tu_clave_brave_aqui"
export SENDA_MOJEEK_API_KEY="tu_clave_mojeek_aqui"

# 4. Iniciar Senda
senda serve --host 0.0.0.0 --port 8000
```

---

## ⚙️ Variables de Configuración

Las siguientes variables de entorno permiten controlar los adaptadores de búsqueda y comportamiento regional:

| Variable | Descripción | Valor por Defecto |
|---|---|---|
| `SENDA_DEFAULT_REGION` | Región geográfica por defecto | `co` (Colombia) |
| `SENDA_DEFAULT_LANGUAGE` | Idioma de interfaz y filtrado preferente | `es` (Español) |
| `SENDA_SEARXNG_URL` | URL de la instancia local de SearXNG | `None` (desactivado si no se define) |
| `SENDA_BRAVE_API_KEY` | Clave API oficial de Brave Search | `None` (desactivado si no se define) |
| `SENDA_MOJEEK_API_KEY` | Clave API oficial de Mojeek | `None` (desactivado si no se define) |
| `SENDA_SAFE_SEARCH` | Nivel de SafeSearch (`strict`, `moderate`, `off`) | `moderate` |
| `SENDA_STORAGE_PATH` | Ruta de la base de datos SQLite FTS5 | `~/.senda/index.db` |

---

## ⚡ Atajos de Búsqueda Tipo Bang (`!bangs`)

Senda permite redirigir directamente la consulta a recursos libres y de conocimiento público sin rastreo intermedio:

| Atajo | Destino | Ejemplo |
|---|---|---|
| `!w` | Wikipedia (Español) | `!w Gabriel García Márquez` |
| `!osm` | OpenStreetMap | `!osm Plaza de Bolívar Bogotá` |
| `!ia` | Internet Archive Wayback Machine | `!ia fsf.org` |
| `!gut` | Proyecto Gutenberg | `!gut Don Quijote` |
| `!fsf` | Free Software Foundation | `!fsf GNU General Public License` |
| `!codeberg`| Repositorios en Codeberg | `!codeberg senda` |
| `!arch` | Wiki de Arch Linux | `!arch udev rules` |
| `!ddg` | DuckDuckGo HTML | `!ddg privacy tools` |

---

## 🔍 Funciones Éticas Clave

- **Botón "¿Por qué veo esto?":** Cada resultado tiene un botón informativo nativo (`<dialog>`) que expone con exactitud la fuente de indexación, fecha conocida y si el resultado fue modificado por filtros personales.
- **Lentes de Usuario (Goggles):** Configuración en formato JSON guardada exclusivamente en el navegador (`localStorage`) que permite subir de posición (`boost`), bajar (`bury`) o bloquear (`block`) dominios específicos según el criterio de cada usuario.
- **Filtro "Sin Anuncios" Activo por Defecto:** Los resultados patrocinados se descartan por defecto. Si se activa la visualización, se presentan bajo etiqueta inequívoca `[Anuncio]` sin rastreo de perfil.
- **Modo Cómodo / Compacto:** Permite adaptar la densidad de información a pantallas de diferentes resoluciones y necesidades visuales.
- **Navegación por Teclado:** Presione `/` para enfocar la barra de búsqueda, `Esc` para limpiar o cerrar modales, y tabule fluidamente por todos los elementos interactivos con foco de alto contraste.

---

## ⚖️ Licencia y Justificación

Senda se distribuye bajo la licencia **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`).

### Justificación de la Licencia
Se eligió la licencia recíproca `GPL-3.0-or-later` para garantizar que cualquier modificación, mejora o redistribución de esta tecnología de búsqueda conserve obligatoriamente las 4 libertades esenciales del Software Libre proclamadas por la Free Software Foundation (FSF). Esto previene que intermediarios privativos privaticen las mejoras de privacidad y transparencia implementadas en beneficio de la comunidad.
