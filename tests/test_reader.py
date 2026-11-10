# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import pytest
from senda.reader import SovereignReader


def test_reader_html_sanitization():
    raw_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Noticia Científica Importante</title>
        <meta name="author" content="Dra. Elena Ramos">
        <meta property="article:published_time" content="2026-11-10T10:00:00Z">
    </head>
    <body>
        <header><nav><a href="/">Inicio</a></nav></header>
        <div class="cookie-banner">Acepta cookies por favor</div>
        <article>
            <h1>Descubrimiento revolucionario en física cuántica</h1>
            <p>Los investigadores han alcanzado un nuevo hito experimental sin precedentes.</p>
            <script>alert('malicious')</script>
            <iframe src="https://evil.com/tracker"></iframe>
            <p style="color:red;" onclick="stealData()">Este es un segundo párrafo de contenido verificado con enlace a <a href="/fuente" onclick="bad()">la fuente</a>.</p>
            <div class="sidebar-advert">Compre nuestro producto ahora</div>
        </article>
        <footer>Pie de página corporativo</footer>
    </body>
    </html>
    """
    reader = SovereignReader()
    article = reader.extract_html(raw_html, base_url="https://ejemplo.org/articulo")

    assert "Noticia Científica" in article.title or "Descubrimiento revolucionario" in article.title
    assert article.byline == "Dra. Elena Ramos"
    assert article.published_date == "2026-11-10"
    assert "revolucionario" in article.content_html
    assert "cookie" not in article.content_html.lower()
    assert "<script" not in article.content_html
    assert "<iframe" not in article.content_html
    assert "onclick" not in article.content_html
    assert 'rel="noopener noreferrer nofollow"' in article.content_html
    assert 'href="https://ejemplo.org/fuente"' in article.content_html
    assert article.reading_time_min >= 1
    assert article.word_count > 0


@pytest.mark.asyncio
async def test_reader_url_validation():
    reader = SovereignReader()
    with pytest.raises(ValueError):
        await reader.extract_url("ftp://example.com/file")
    with pytest.raises(ValueError):
        await reader.extract_url("javascript:alert(1)")
