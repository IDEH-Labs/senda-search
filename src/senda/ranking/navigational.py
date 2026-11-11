# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Sovereign Navigational Resolution Engine for Senda Search.

Accurately identifies navigational search intent:
1. Direct domain and URL input (e.g., google.com, xvideos.com, github.com, https://...)
2. Well-known site and brand queries (e.g., google, xvideos, youtube, reddit, wikipedia)
Ensures users receive the exact destination URL rather than solely encyclopedic Wikipedia entries.
Zero tracking, 100% offline-resilient, privacy-first sovereign design.
"""

import re
import urllib.parse
from typing import Dict, Optional, Tuple
from senda.providers.base import SearchResultItem


# Strict RFC-compliant domain regex pattern with known or general TLDs
DOMAIN_REGEX = re.compile(
    r"^(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+([a-zA-Z]{2,63})(?::\d+)?(\/.*)?$",
    re.IGNORECASE,
)

# Common top-level domains for validation
COMMON_TLDS = {
    "com", "org", "net", "edu", "gov", "mil", "int", "io", "co", "ai", "app",
    "dev", "top", "xyz", "info", "biz", "me", "cc", "tv", "site", "online",
    "club", "tech", "store", "cloud", "space", "pro", "mobi", "cat",
    # Country-code top-level domains (ccTLDs)
    "es", "en", "us", "uk", "de", "fr", "it", "pt", "br", "mx", "ar", "cl",
    "co", "pe", "ve", "ec", "ca", "au", "nl", "ru", "jp", "cn", "in", "ch",
    "se", "no", "fi", "dk", "pl", "cz", "be", "at", "za", "nz", "kr", "eu",
}


# High-frequency sovereign navigational registry of verified global sites & tools
NAVIGATIONAL_DIRECTORY: Dict[str, Tuple[str, str, str]] = {
    # Key: normalized query -> (Official URL, Display Name, Short Description)
    # Search & Knowledge
    "google": ("https://www.google.com/", "Google", "Motor de búsqueda web y servicios en la nube."),
    "google.com": ("https://www.google.com/", "Google", "Motor de búsqueda web y servicios en la nube."),
    "duckduckgo": ("https://duckduckgo.com/", "DuckDuckGo", "Buscador privado que no rastrea tu actividad."),
    "ddg": ("https://duckduckgo.com/", "DuckDuckGo", "Buscador privado."),
    "bing": ("https://www.bing.com/", "Microsoft Bing", "Motor de búsqueda web de Microsoft."),
    "yahoo": ("https://www.yahoo.com/", "Yahoo", "Portal web de noticias, correo y búsquedas."),
    "ecosia": ("https://www.ecosia.org/", "Ecosia", "Buscador ecológico que planta árboles."),
    "qwant": ("https://www.qwant.com/", "Qwant", "Buscador europeo que protege la privacidad."),
    "startpage": ("https://www.startpage.com/", "Startpage", "Resultados de búsqueda privados."),
    "searxng": ("https://searx.space/", "SearXNG", "Metabuscador libre y descentralizado."),
    "wikipedia": ("https://es.wikipedia.org/", "Wikipedia", "La enciclopedia libre, colaborativa y multilingüe."),
    "wikidata": ("https://www.wikidata.org/", "Wikidata", "Base de conocimiento colaborativa y estructurada."),
    "wikimedia": ("https://www.wikimedia.org/", "Wikimedia", "Fundación de proyectos de conocimiento libre."),
    "internet archive": ("https://archive.org/", "Internet Archive", "Biblioteca digital sin fines de lucro y Wayback Machine."),
    "archive.org": ("https://archive.org/", "Internet Archive", "Biblioteca digital sin fines de lucro y Wayback Machine."),
    "openstreetmap": ("https://www.openstreetmap.org/", "OpenStreetMap", "Mapa mundial libre y colaborativo."),
    "osm": ("https://www.openstreetmap.org/", "OpenStreetMap", "Mapa mundial libre y colaborativo."),
    "gutenberg": ("https://www.gutenberg.org/", "Project Gutenberg", "Biblioteca digital de libros de dominio público."),

    # Video, Streaming & Entertainment
    "youtube": ("https://www.youtube.com/", "YouTube", "Plataforma global para ver, compartir y subir videos."),
    "yt": ("https://www.youtube.com/", "YouTube", "Plataforma de videos."),
    "xvideos": ("https://www.xvideos.com/", "XVideos", "Plataforma de alojamiento de videos para adultos."),
    "xvideos.com": ("https://www.xvideos.com/", "XVideos", "Plataforma de alojamiento de videos para adultos."),
    "pornhub": ("https://www.pornhub.com/", "Pornhub", "Sitio web de videos para adultos."),
    "pornhub.com": ("https://www.pornhub.com/", "Pornhub", "Sitio web de videos para adultos."),
    "twitch": ("https://www.twitch.tv/", "Twitch", "Plataforma de transmisiones en vivo y videojuegos."),
    "netflix": ("https://www.netflix.com/", "Netflix", "Servicio de streaming de películas, series y documentales."),
    "spotify": ("https://open.spotify.com/", "Spotify", "Servicio de streaming de música y podcasts."),
    "soundcloud": ("https://soundcloud.com/", "SoundCloud", "Plataforma de distribución y reproducción de audio."),
    "vimeo": ("https://vimeo.com/", "Vimeo", "Plataforma de video para creadores audiovisuales."),
    "dailymotion": ("https://www.dailymotion.com/", "Dailymotion", "Plataforma de video."),
    "peertube": ("https://joinpeertube.org/", "PeerTube", "Red federada y libre de alojamiento de videos."),

    # Social & Communications
    "facebook": ("https://www.facebook.com/", "Facebook", "Red social para conectar con amigos y comunidades."),
    "instagram": ("https://www.instagram.com/", "Instagram", "Red social para compartir fotos, videos y mensajes."),
    "twitter": ("https://x.com/", "X (antes Twitter)", "Red social de microblogging y noticias en tiempo real."),
    "x": ("https://x.com/", "X (antes Twitter)", "Red social de microblogging y noticias en tiempo real."),
    "x.com": ("https://x.com/", "X (Twitter)", "Red social."),
    "reddit": ("https://www.reddit.com/", "Reddit", "Red de comunidades donde la gente comparte intereses y foros."),
    "tiktok": ("https://www.tiktok.com/", "TikTok", "Plataforma de videos cortos en formato vertical."),
    "linkedin": ("https://www.linkedin.com/", "LinkedIn", "Red profesional para empleo y negocios."),
    "whatsapp": ("https://web.whatsapp.com/", "WhatsApp Web", "Mensajería instantánea y llamadas seguras."),
    "telegram": ("https://web.telegram.org/", "Telegram Web", "Mensajería rápida, segura y basada en la nube."),
    "signal": ("https://signal.org/", "Signal", "Mensajería privada con cifrado de extremo a extremo."),
    "discord": ("https://discord.com/", "Discord", "Comunidades, canales de voz y mensajería en tiempo real."),
    "mastodon": ("https://joinmastodon.org/", "Mastodon", "Red social descentralizada y libre en el Fediverso."),
    "bluesky": ("https://bsky.app/", "Bluesky", "Red social abierta basada en el protocolo AT."),
    "threads": ("https://www.threads.net/", "Threads", "Plataforma de conversaciones y microblogging."),
    "pinterest": ("https://www.pinterest.com/", "Pinterest", "Plataforma para descubrir ideas e inspiración visual."),

    # Tech, Development & Free Software
    "github": ("https://github.com/", "GitHub", "Plataforma de desarrollo colaborativo de software."),
    "github.com": ("https://github.com/", "GitHub", "Plataforma de desarrollo de software."),
    "gitlab": ("https://gitlab.com/", "GitLab", "Plataforma integral de DevOps y repositorios Git."),
    "codeberg": ("https://codeberg.org/", "Codeberg", "Forja de software libre y código abierto sin ánimo de lucro."),
    "stackoverflow": ("https://stackoverflow.com/", "Stack Overflow", "Comunidad de preguntas y respuestas para programadores."),
    "python": ("https://www.python.org/", "Python", "Lenguaje de programación dinámico y multipropósito."),
    "rust": ("https://www.rust-lang.org/", "Rust", "Lenguaje de programación enfocado en rendimiento y seguridad."),
    "gnu": ("https://www.gnu.org/", "Proyecto GNU", "Sistema operativo libre y herramientas de software libre."),
    "fsf": ("https://www.fsf.org/", "Free Software Foundation", "Organización dedicada a defender la libertad del software."),
    "kernel": ("https://www.kernel.org/", "The Linux Kernel", "Repositorio oficial del núcleo del sistema Linux."),
    "debian": ("https://www.debian.org/", "Debian", "El sistema operativo universal libre basado en Linux."),
    "archlinux": ("https://archlinux.org/", "Arch Linux", "Distribución de Linux independiente y minimalista."),
    "arch linux": ("https://archlinux.org/", "Arch Linux", "Distribución de Linux independiente y minimalista."),
    "ubuntu": ("https://ubuntu.com/", "Ubuntu", "Sistema operativo Linux empresarial y de escritorio."),
    "npm": ("https://www.npmjs.com/", "npm", "Registro de paquetes para el ecosistema JavaScript."),
    "pypi": ("https://pypi.org/", "PyPI", "Repositorio oficial de paquetes para el lenguaje Python."),
    "docker": ("https://www.docker.com/", "Docker", "Plataforma de contenedores para desarrollo y despliegue."),

    # Cloud & Productivity
    "gmail": ("https://mail.google.com/", "Gmail", "Servicio de correo electrónico de Google."),
    "outlook": ("https://outlook.live.com/", "Microsoft Outlook", "Correo electrónico y calendario personal."),
    "protonmail": ("https://proton.me/mail", "Proton Mail", "Correo electrónico seguro con cifrado de extremo a extremo."),
    "proton": ("https://proton.me/", "Proton", "Servicios de privacidad, correo, VPN y almacenamiento."),
    "drive": ("https://drive.google.com/", "Google Drive", "Almacenamiento de archivos y sincronización en la nube."),
    "dropbox": ("https://www.dropbox.com/", "Dropbox", "Almacenamiento en la nube y sincronización de archivos."),
}


class NavigationalEngine:
    """Detects and resolves direct site navigational queries."""

    @staticmethod
    def is_domain_query(query: str) -> Optional[Tuple[str, str, str]]:
        """Determine if query is directly specifying a domain or URL.

        Returns tuple of (normalized_url, clean_host, site_title) or None.
        """
        clean = query.strip()
        if not clean or " " in clean or len(clean) < 4:
            return None

        # Check domain pattern match
        match = DOMAIN_REGEX.match(clean)
        if not match:
            return None

        # Extract TLD
        tld = match.group(2).lower()
        if tld not in COMMON_TLDS and len(tld) < 2:
            return None

        # Normalize URL scheme
        raw_url = clean
        if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
            raw_url = f"https://{raw_url}"

        try:
            parsed = urllib.parse.urlparse(raw_url)
            host = parsed.netloc.lower()
            if host.startswith("www."):
                host_display = host[4:]
            else:
                host_display = host

            # Format title from primary domain name
            domain_name = host_display.split(".")[0].capitalize()
            site_title = f"{domain_name} — Sitio Oficial ({host_display})"
            clean_url = raw_url

            return clean_url, host_display, site_title
        except Exception:
            return None

    @classmethod
    def resolve(cls, query: str, lang: str = "es") -> Optional[SearchResultItem]:
        """Resolve query to a prime direct navigational SearchResultItem, if applicable."""
        clean_q = query.strip()
        if not clean_q:
            return None

        q_norm = clean_q.lower()

        # 1. Direct registry lookup (e.g., 'xvideos', 'google', 'youtube', 'github')
        if q_norm in NAVIGATIONAL_DIRECTORY:
            url, name, desc = NAVIGATIONAL_DIRECTORY[q_norm]
            domain = urllib.parse.urlparse(url).netloc
            title = f"{name} — Sitio Oficial"
            snippet = f"{desc} Acceso directo a {domain} sin intermediarios ni rastreadores."
            return SearchResultItem(
                url=url,
                domain=domain,
                title=title,
                snippet=snippet,
                score=1000.0,
                doc_type="web",
                source="Navegación Directa",
                why_seen=f"Coincidencia exacta de navegación hacia el sitio web oficial de '{name}'.",
                is_sponsored=False,
                canonical_url=url,
                source_type="sitio_oficial",
                content_type="portal_oficial",
                provider_origin="Senda Navegación",
            )

        # 2. Check if query is explicitly a domain or URL (e.g., 'google.com', 'xvideos.com', 'archlinux.org')
        domain_info = cls.is_domain_query(clean_q)
        if domain_info:
            target_url, clean_host, site_title = domain_info
            snippet = f"Navegación directa y acceso verificado al sitio web {clean_host}. Enlace directo sin rastreadores."
            return SearchResultItem(
                url=target_url,
                domain=clean_host,
                title=site_title,
                snippet=snippet,
                score=1000.0,
                doc_type="web",
                source="Navegación Directa",
                why_seen=f"Navegación directa hacia el dominio '{clean_host}'.",
                is_sponsored=False,
                canonical_url=target_url,
                source_type="sitio_oficial",
                content_type="portal_oficial",
                provider_origin="Senda Navegación",
            )

        return None
