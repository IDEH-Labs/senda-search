#!/usr/bin/env python3
"""
Senda Search Engine — Brand Identity & Vector Asset Generator
SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 IDEH Labs <https://ideh.top>

Generates all official Senda logo variants:
- Adaptive SVG (Dual Theme dark/light automatic)
- Dark Mode Aurora Master (Teal / Emerald / Sky)
- Light Mode High-Contrast Master (WCAG AAA Emerald / Cobalt)
- Monochrome White & Monochrome Dark Slate
- Compact UI Emblems (24px, 32px, 48px)
- Squircle App Icons (512px, 192px)
- Favicon (SVG & PNG)
- Horizontal Brand Lockup (Emblem + Senda Typography)
- OpenGraph Card (1200x630)
"""

import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_IMG_DIR = BASE_DIR / "src" / "senda" / "ui" / "static" / "img"
STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)

# Senda S-Curve Canonical SVG Path Data
SENDA_S_CURVE = (
    "M 306 170 C 306 135 272 120 230 120 "
    "C 180 120 154 145 154 188 "
    "C 154 238 204 256 254 272 "
    "C 314 290 348 316 348 358 "
    "C 348 408 296 434 236 434 "
    "C 176 434 142 400 142 358"
)

# 1. Dark Mode Master Symbol (Aurora Glow)
SVG_SYMBOL_DARK = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="Senda Logo">
  <title>Senda — Dark Theme Master</title>
  <defs>
    <linearGradient id="senda-curve-dark" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2dd4bf"/>
      <stop offset="50%" stop-color="#00d2a0"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
    <radialGradient id="senda-halo-dark" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00d2a0" stop-opacity="0.35"/>
      <stop offset="60%" stop-color="#38bdf8" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#080c14" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow-dark" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  <!-- Ambient Halo -->
  <circle cx="256" cy="256" r="160" fill="url(#senda-halo-dark)"/>
  <!-- Orbit Ring -->
  <circle cx="256" cy="256" r="148" fill="none" stroke="#00d2a0" stroke-width="2.5" opacity="0.38"/>
  <circle cx="256" cy="256" r="148" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="14 18" opacity="0.45"/>
  <!-- Senda S-Curve -->
  <path d="{SENDA_S_CURVE}"
        fill="none" stroke="url(#senda-curve-dark)" stroke-width="42" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow-dark)"/>
</svg>
'''

# 2. Light Mode Master Symbol (WCAG AAA High Contrast)
SVG_SYMBOL_LIGHT = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="Senda Logo">
  <title>Senda — Light Theme Master</title>
  <defs>
    <linearGradient id="senda-curve-light" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f766e"/>
      <stop offset="50%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <radialGradient id="senda-halo-light" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#059669" stop-opacity="0.16"/>
      <stop offset="60%" stop-color="#0284c7" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <filter id="shadow-light" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#0f766e" flood-opacity="0.22"/>
    </filter>
  </defs>
  <!-- Ambient Halo -->
  <circle cx="256" cy="256" r="160" fill="url(#senda-halo-light)"/>
  <!-- Orbit Ring -->
  <circle cx="256" cy="256" r="148" fill="none" stroke="#059669" stroke-width="2.5" opacity="0.30"/>
  <circle cx="256" cy="256" r="148" fill="none" stroke="#0284c7" stroke-width="1.5" stroke-dasharray="14 18" opacity="0.35"/>
  <!-- Senda S-Curve -->
  <path d="{SENDA_S_CURVE}"
        fill="none" stroke="url(#senda-curve-light)" stroke-width="42" stroke-linecap="round" stroke-linejoin="round" filter="url(#shadow-light)"/>
</svg>
'''

# 3. Adaptive Dual-Theme SVG (Pure CSS Media Queries, Zero JS)
SVG_SYMBOL_ADAPTIVE = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="Senda Logo">
  <title>Senda — Logo Adaptable Oficial</title>
  <style>
    :root {{
      --senda-stop-1: #0f766e;
      --senda-stop-2: #059669;
      --senda-stop-3: #0284c7;
      --senda-ring-1: #059669;
      --senda-ring-2: #0284c7;
      --senda-halo-opacity: 0.14;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --senda-stop-1: #2dd4bf;
        --senda-stop-2: #00d2a0;
        --senda-stop-3: #38bdf8;
        --senda-ring-1: #00d2a0;
        --senda-ring-2: #38bdf8;
        --senda-halo-opacity: 0.35;
      }}
    }}
    .senda-halo {{ fill: var(--senda-ring-1); fill-opacity: var(--senda-halo-opacity); }}
    .senda-ring-solid {{ stroke: var(--senda-ring-1); }}
    .senda-ring-dash {{ stroke: var(--senda-ring-2); }}
    .senda-path {{ stroke: url(#adaptive-grad); }}
  </style>
  <defs>
    <linearGradient id="adaptive-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="var(--senda-stop-1)"/>
      <stop offset="50%" stop-color="var(--senda-stop-2)"/>
      <stop offset="100%" stop-color="var(--senda-stop-3)"/>
    </linearGradient>
  </defs>
  <circle cx="256" cy="256" r="160" class="senda-halo"/>
  <circle cx="256" cy="256" r="148" fill="none" class="senda-ring-solid" stroke-width="2.5" opacity="0.35"/>
  <circle cx="256" cy="256" r="148" fill="none" class="senda-ring-dash" stroke-width="1.5" stroke-dasharray="14 18" opacity="0.4"/>
  <path d="{SENDA_S_CURVE}"
        class="senda-path" fill="none" stroke-width="42" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''

# 4. Monochrome Pure White
SVG_SYMBOL_MONO_WHITE = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="Senda Logo">
  <title>Senda — Monocromo Blanco</title>
  <circle cx="256" cy="256" r="148" fill="none" stroke="#ffffff" stroke-width="2.5" opacity="0.25"/>
  <path d="{SENDA_S_CURVE}"
        fill="none" stroke="#ffffff" stroke-width="42" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''

# 5. Monochrome Pure Dark Slate
SVG_SYMBOL_MONO_DARK = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="Senda Logo">
  <title>Senda — Monocromo Tinta</title>
  <circle cx="256" cy="256" r="148" fill="none" stroke="#0f172a" stroke-width="2.5" opacity="0.25"/>
  <path d="{SENDA_S_CURVE}"
        fill="none" stroke="#0f172a" stroke-width="42" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''

# 6. App Icon with Rounded Squircle (Dark Theme for Mobile & Webmanifest)
SVG_ICON_SQUIRCLE_DARK = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bg-squircle-dark" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0f1d"/>
      <stop offset="50%" stop-color="#080c14"/>
      <stop offset="100%" stop-color="#04060a"/>
    </linearGradient>
    <linearGradient id="curve-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2dd4bf"/>
      <stop offset="50%" stop-color="#00d2a0"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
    <radialGradient id="halo-glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00d2a0" stop-opacity="0.30"/>
      <stop offset="65%" stop-color="#38bdf8" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="#080c14" stop-opacity="0"/>
    </radialGradient>
    <filter id="drop-sh" x="-15%" y="-15%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
  </defs>
  <!-- Squircle Base -->
  <rect x="24" y="24" width="464" height="464" rx="104" fill="url(#bg-squircle-dark)" stroke="rgba(45,212,191,0.18)" stroke-width="2"/>
  <!-- Ambient Inner Halo -->
  <circle cx="256" cy="256" r="160" fill="url(#halo-glow)"/>
  <!-- Orbit Ring -->
  <circle cx="256" cy="256" r="148" fill="none" stroke="#00d2a0" stroke-width="2" opacity="0.35"/>
  <circle cx="256" cy="256" r="148" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="14 18" opacity="0.40"/>
  <!-- Senda S-Curve -->
  <path d="{SENDA_S_CURVE}"
        fill="none" stroke="url(#curve-grad)" stroke-width="42" stroke-linecap="round" stroke-linejoin="round" filter="url(#drop-sh)"/>
</svg>
'''

# 7. App Icon with Rounded Squircle (Light Theme)
SVG_ICON_SQUIRCLE_LIGHT = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bg-squircle-light" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f1f5f9"/>
    </linearGradient>
    <linearGradient id="curve-grad-l" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f766e"/>
      <stop offset="50%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <radialGradient id="halo-glow-l" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#059669" stop-opacity="0.14"/>
      <stop offset="70%" stop-color="#0284c7" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <filter id="drop-sh-l" x="-15%" y="-15%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#0f766e" flood-opacity="0.22"/>
    </filter>
  </defs>
  <!-- Squircle Base -->
  <rect x="24" y="24" width="464" height="464" rx="104" fill="url(#bg-squircle-light)" stroke="rgba(15,118,110,0.15)" stroke-width="2"/>
  <!-- Ambient Inner Halo -->
  <circle cx="256" cy="256" r="160" fill="url(#halo-glow-l)"/>
  <!-- Orbit Ring -->
  <circle cx="256" cy="256" r="148" fill="none" stroke="#059669" stroke-width="2" opacity="0.30"/>
  <!-- Senda S-Curve -->
  <path d="{SENDA_S_CURVE}"
        fill="none" stroke="url(#curve-grad-l)" stroke-width="42" stroke-linecap="round" stroke-linejoin="round" filter="url(#drop-sh-l)"/>
</svg>
'''

# 8. Optimized Vector Favicon (Clean 32x32 viewbox)
SVG_FAVICON = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="32" height="32">
  <defs>
    <linearGradient id="fav-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2dd4bf"/>
      <stop offset="50%" stop-color="#00d2a0"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="128" fill="#080c14"/>
  <circle cx="256" cy="256" r="150" fill="none" stroke="#00d2a0" stroke-width="8" opacity="0.4"/>
  <path d="{SENDA_S_CURVE}"
        fill="none" stroke="url(#fav-grad)" stroke-width="56" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''

# 9. Horizontal Brand Lockup (Dark Theme)
SVG_LOCKUP_DARK = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 160" width="640" height="160">
  <defs>
    <linearGradient id="h-curve-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2dd4bf"/>
      <stop offset="50%" stop-color="#00d2a0"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
    <radialGradient id="h-halo" cx="80" cy="80" r="70" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#00d2a0" stop-opacity="0.30"/>
      <stop offset="70%" stop-color="#38bdf8" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="#080c14" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <!-- Emblem Scaled (512x512 scaled to 130x130, translated to x=15, y=15) -->
  <g transform="translate(15, 15) scale(0.254)">
    <circle cx="256" cy="256" r="160" fill="url(#h-halo)"/>
    <circle cx="256" cy="256" r="148" fill="none" stroke="#00d2a0" stroke-width="3" opacity="0.35"/>
    <circle cx="256" cy="256" r="148" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="14 18" opacity="0.40"/>
    <path d="{SENDA_S_CURVE}"
          fill="none" stroke="url(#h-curve-grad)" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <!-- Senda Typography -->
  <text x="175" y="98" fill="#f8fafc" font-family="'Source Sans 3', 'Liberation Sans', -apple-system, BlinkMacSystemFont, sans-serif" font-size="64" font-weight="700" letter-spacing="-0.03em">Senda</text>
  <text x="177" y="128" fill="#94a3b8" font-family="'Source Sans 3', 'Liberation Sans', -apple-system, BlinkMacSystemFont, sans-serif" font-size="16" font-weight="500" letter-spacing="0.14em">BUSCADOR LIBRE</text>
</svg>
'''

# 10. Horizontal Brand Lockup (Light Theme)
SVG_LOCKUP_LIGHT = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 160" width="640" height="160">
  <defs>
    <linearGradient id="hl-curve-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f766e"/>
      <stop offset="50%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
  </defs>
  <g transform="translate(15, 15) scale(0.254)">
    <circle cx="256" cy="256" r="148" fill="none" stroke="#059669" stroke-width="3" opacity="0.30"/>
    <path d="{SENDA_S_CURVE}"
          fill="none" stroke="url(#hl-curve-grad)" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <text x="175" y="98" fill="#0f172a" font-family="'Source Sans 3', 'Liberation Sans', -apple-system, BlinkMacSystemFont, sans-serif" font-size="64" font-weight="700" letter-spacing="-0.03em">Senda</text>
  <text x="177" y="128" fill="#64748b" font-family="'Source Sans 3', 'Liberation Sans', -apple-system, BlinkMacSystemFont, sans-serif" font-size="16" font-weight="500" letter-spacing="0.14em">BUSCADOR LIBRE</text>
</svg>
'''

# 11. OpenGraph Social Share Card (1200x630)
SVG_OPENGRAPH = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <radialGradient id="og-bg" cx="50%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="60%" stop-color="#080c14"/>
      <stop offset="100%" stop-color="#020408"/>
    </radialGradient>
    <radialGradient id="og-ambient" cx="600" cy="220" r="280" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#00d2a0" stop-opacity="0.22"/>
      <stop offset="60%" stop-color="#38bdf8" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#080c14" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="og-curve" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2dd4bf"/>
      <stop offset="50%" stop-color="#00d2a0"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
    <filter id="og-glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="12" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="1200" height="630" fill="url(#og-bg)"/>
  <circle cx="600" cy="220" r="280" fill="url(#og-ambient)"/>

  <!-- Centered Emblem (Scaled from 512 to 210, translated to cx=600, cy=180) -->
  <g transform="translate(495, 75) scale(0.41)">
    <circle cx="256" cy="256" r="160" fill="none" stroke="#00d2a0" stroke-width="2.5" opacity="0.35"/>
    <circle cx="256" cy="256" r="148" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="14 18" opacity="0.45"/>
    <path d="{SENDA_S_CURVE}"
          fill="none" stroke="url(#og-curve)" stroke-width="42" stroke-linecap="round" stroke-linejoin="round" filter="url(#og-glow)"/>
  </g>

  <!-- Typography -->
  <text x="600" y="360" text-anchor="middle" fill="#ffffff" font-family="'Source Sans 3', 'Liberation Sans', sans-serif" font-size="72" font-weight="800" letter-spacing="-0.03em">Senda</text>
  <text x="600" y="420" text-anchor="middle" fill="#94a3b8" font-family="'Source Sans 3', 'Liberation Sans', sans-serif" font-size="24" font-weight="400" letter-spacing="-0.01em">Buscador web ético, rápido y transparente</text>

  <!-- Feature Pills -->
  <g transform="translate(600, 480)" text-anchor="middle">
    <!-- Pill 1: Software Libre -->
    <rect x="-350" y="0" width="210" height="38" rx="19" fill="rgba(16,185,129,0.10)" stroke="#10b981" stroke-width="1.2"/>
    <text x="-245" y="24" fill="#34d399" font-family="'Source Sans 3', sans-serif" font-size="14" font-weight="600" letter-spacing="0.04em">SOFTWARE LIBRE</text>

    <!-- Pill 2: FSF & GPL-3.0 -->
    <rect x="-110" y="0" width="220" height="38" rx="19" fill="rgba(56,189,248,0.10)" stroke="#38bdf8" stroke-width="1.2"/>
    <text x="0" y="24" fill="#38bdf8" font-family="'Source Sans 3', sans-serif" font-size="14" font-weight="600" letter-spacing="0.04em">GNU GPL-3.0-OR-LATER</text>

    <!-- Pill 3: Cero Rastreo -->
    <rect x="140" y="0" width="210" height="38" rx="19" fill="rgba(168,85,247,0.10)" stroke="#c084fc" stroke-width="1.2"/>
    <text x="245" y="24" fill="#c084fc" font-family="'Source Sans 3', sans-serif" font-size="14" font-weight="600" letter-spacing="0.04em">CERO RASTREO</text>
  </g>

  <!-- Subtle bottom credit -->
  <text x="600" y="580" text-anchor="middle" fill="#475569" font-family="'Source Sans 3', sans-serif" font-size="14" font-weight="500" letter-spacing="0.06em">IDEH LABS · COLOMBIA</text>
</svg>
'''

ASSETS = {
    "senda-symbol-dark.svg": SVG_SYMBOL_DARK,
    "senda-symbol-light.svg": SVG_SYMBOL_LIGHT,
    "senda-symbol-adaptive.svg": SVG_SYMBOL_ADAPTIVE,
    "senda-symbol-mono-white.svg": SVG_SYMBOL_MONO_WHITE,
    "senda-symbol-mono-dark.svg": SVG_SYMBOL_MONO_DARK,
    "senda-icon-squircle-dark.svg": SVG_ICON_SQUIRCLE_DARK,
    "senda-icon-squircle-light.svg": SVG_ICON_SQUIRCLE_LIGHT,
    "favicon.svg": SVG_FAVICON,
    "senda-logo-horiz-dark.svg": SVG_LOCKUP_DARK,
    "senda-logo-horiz-light.svg": SVG_LOCKUP_LIGHT,
    "senda-og.svg": SVG_OPENGRAPH,
}

PNG_TARGETS = [
    ("senda-icon-squircle-dark.svg", "senda-icon-512.png", 512, 512),
    ("senda-icon-squircle-dark.svg", "senda-icon-192.png", 192, 192),
    ("senda-icon-squircle-dark.svg", "senda-icon-48.png", 48, 48),
    ("favicon.svg", "favicon.png", 32, 32),
    ("senda-symbol-dark.svg", "senda-symbol-dark-512.png", 512, 512),
    ("senda-symbol-light.svg", "senda-symbol-light-512.png", 512, 512),
    ("senda-og.svg", "senda-og.png", 1200, 630),
]

def main():
    print(f"Generating SVG assets into {STATIC_IMG_DIR}...")
    for filename, content in ASSETS.items():
        filepath = STATIC_IMG_DIR / filename
        filepath.write_text(content, encoding="utf-8")
        print(f"  [+] Wrote {filename}")

    print("\nRendering high-fidelity PNG assets via rsvg-convert...")
    for src_svg, out_png, width, height in PNG_TARGETS:
        src_path = STATIC_IMG_DIR / src_svg
        out_path = STATIC_IMG_DIR / out_png
        cmd = [
            "rsvg-convert",
            "-w", str(width),
            "-h", str(height),
            "-f", "png",
            "-o", str(out_path),
            str(src_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print(f"  [+] Rendered {out_png} ({width}x{height})")
        else:
            print(f"  [!] Error rendering {out_png}: {res.stderr}")

if __name__ == "__main__":
    main()
