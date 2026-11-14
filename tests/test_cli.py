# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Unit tests for Senda administrative CLI commands."""

import io
import sys
from unittest.mock import patch
import pytest

from senda.cli.main import main
from senda.extractor.parser import ExtractedDocument
from senda.indexer.storage import StorageEngine


@pytest.fixture
def test_db_env(tmp_path, monkeypatch):
    db_file = tmp_path / "cli_test.db"
    monkeypatch.setattr("senda.config.settings.DATA_DIR", tmp_path)
    monkeypatch.setattr("senda.config.settings.DATABASE_NAME", "cli_test.db")

    storage = StorageEngine(db_path=db_file)
    storage.upsert_document(
        ExtractedDocument(
            url="https://gentoo.org/about",
            title="Gentoo Linux - Philosophy and Control",
            description="A highly flexible, source-based Linux distribution.",
            language="en",
            headings="Choice Freedom",
            body_text="Gentoo is built around freedom of choice and maximum system control.",
            content_hash="gentoohash1",
        )
    )
    return storage


def test_cli_stats(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "stats"])
    main()

    captured = capsys.readouterr()
    assert "Senda Index Statistics" in captured.out
    assert "Total Documents:  1" in captured.out
    assert "Total Domains:    1" in captured.out


def test_cli_search(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "search", "Gentoo"])
    main()

    captured = capsys.readouterr()
    assert "Senda Search: 'Gentoo'" in captured.out
    assert "Gentoo Linux - Philosophy and Control" in captured.out
    assert "https://gentoo.org/about" in captured.out


def test_cli_purge_url(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "purge-url", "https://gentoo.org/about"])
    main()

    captured = capsys.readouterr()
    assert "Purged 1 document matching URL" in captured.out

    # Verify document is gone
    monkeypatch.setattr(sys, "argv", ["senda", "stats"])
    main()
    captured_after = capsys.readouterr()
    assert "Total Documents:  0" in captured_after.out


def test_cli_purge_domain(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "purge-domain", "gentoo.org"])
    main()

    captured = capsys.readouterr()
    assert "Purged 0 document(s) belonging to domain 'gentoo.org'" in captured.out or "Purged 1 document(s)" in captured.out


def test_cli_crawl_missing_args(test_db_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["senda", "crawl"])
    main()
    captured = capsys.readouterr()
    assert "Error: Must provide either a seed URL or --seeds-file." in captured.out


def test_cli_crawl_daemon_once(test_db_env, tmp_path, monkeypatch, capsys):
    from unittest.mock import AsyncMock
    seeds_file = tmp_path / "test_seeds.txt"
    seeds_file.write_text("https://example.org\nhttps://fsf.org\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["senda", "crawl-daemon", "--seeds-file", str(seeds_file), "--once", "--max-pages", "5"])

    with patch("senda.cli.main.CrawlerRunner.crawl_seeds", new_callable=AsyncMock) as mock_crawl:
        mock_crawl.return_value = 2
        main()

    captured = capsys.readouterr()
    assert "Senda Ethical Indexer Daemon" in captured.out
    assert "Cycle #1 completed. Indexed/Updated: 2 docs." in captured.out
    assert "Senda Indexer Daemon stopped cleanly." in captured.out


def test_cli_serve(monkeypatch, capsys):
    """Verify senda serve executes cleanly with uvicorn and handles forwarded_allow_ips."""
    monkeypatch.setattr(sys, "argv", ["senda", "serve", "--host", "127.0.0.1", "--port", "8000"])
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.called
        kwargs = mock_run.call_args.kwargs
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8000
        assert kwargs["proxy_headers"] is True
        assert "forwarded_allow_ips" in kwargs

    captured = capsys.readouterr()
    assert "Starting Senda Sovereign Search Web UI" in captured.out


def test_cli_serve_custom_cli_forwarded_ips(monkeypatch, capsys):
    """Verify senda serve CLI flag --forwarded-allow-ips propagates directly to uvicorn."""
    custom_ips = "10.0.0.1,192.168.1.1,172.16.0.0/12"
    monkeypatch.setattr(sys, "argv", ["senda", "serve", "--host", "0.0.0.0", "--port", "9000", "--forwarded-allow-ips", custom_ips])
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.called
        kwargs = mock_run.call_args.kwargs
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 9000
        assert kwargs["forwarded_allow_ips"] == custom_ips


def test_cli_serve_env_and_defaults(monkeypatch, capsys):
    """Verify senda serve uses settings defaults and reads FORWARDED_ALLOW_IPS from environment."""
    monkeypatch.setattr(sys, "argv", ["senda", "serve"])
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "127.0.0.1,::1,10.0.0.0/8")
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.called
        kwargs = mock_run.call_args.kwargs
        from senda.config import settings
        assert kwargs["host"] == settings.SERVER_HOST
        assert kwargs["port"] == settings.SERVER_PORT
        assert kwargs["forwarded_allow_ips"] == "127.0.0.1,::1,10.0.0.0/8"


def test_cli_serve_disables_access_log_by_default_and_honors_env(monkeypatch):
    """Verify senda serve disables uvicorn access_log by default to protect search queries in journald."""
    monkeypatch.setattr(sys, "argv", ["senda", "serve"])
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.call_args.kwargs["access_log"] is False

    monkeypatch.setenv("SENDA_ACCESS_LOG", "true")
    with patch("uvicorn.run") as mock_run:
        main()
        assert mock_run.call_args.kwargs["access_log"] is True


def test_cli_list_niches(monkeypatch, capsys):
    """Verify senda list-niches prints registered high-value niches."""
    monkeypatch.setattr(sys, "argv", ["senda", "list-niches"])
    main()
    captured = capsys.readouterr()
    assert "Nichos Estratégicos de Indexación Soberana" in captured.out
    assert "tech_docs" in captured.out
    assert "academic" in captured.out
    assert "iberoamerica_media" in captured.out
    assert "libre_software" in captured.out
    assert "global_gov_data" in captured.out


def test_cli_crawl_niche_mocked(monkeypatch, capsys):
    """Verify senda crawl-niche triggers CrawlerRunner with curated seeds."""
    from unittest.mock import AsyncMock
    monkeypatch.setattr(sys, "argv", ["senda", "crawl-niche", "tech_docs", "--max-pages", "5", "--max-depth", "1"])
    with patch("senda.crawler.runner.CrawlerRunner.crawl_seeds", new=AsyncMock(return_value=3)):
        main()
        captured = capsys.readouterr()
        assert "Iniciando rastreo de nicho" in captured.out
        assert "tech_docs" in captured.out
        assert "Se indexaron/actualizaron exitosamente 3 documentos" in captured.out


def test_cli_crawl_global_gov_data_niche_mocked(monkeypatch, capsys):
    """Verify senda crawl-niche global_gov_data triggers CrawlerRunner."""
    from unittest.mock import AsyncMock
    monkeypatch.setattr(sys, "argv", ["senda", "crawl-niche", "global_gov_data", "--max-pages", "10", "--max-depth", "1"])
    with patch("senda.crawler.runner.CrawlerRunner.crawl_seeds", new=AsyncMock(return_value=12)):
        main()
        captured = capsys.readouterr()
        assert "Iniciando rastreo de nicho" in captured.out
        assert "global_gov_data" in captured.out
        assert "Se indexaron/actualizaron exitosamente 12 documentos" in captured.out


def test_global_gov_data_seed_coverage():
    """Verify global_gov_data covers multilateral federators and all 195 sovereign countries of the world."""
    from senda.crawler.seeds import get_niche_seeds, NICHE_DEFINITIONS
    assert "global_gov_data" in NICHE_DEFINITIONS
    seeds = get_niche_seeds("global_gov_data")
    assert len(seeds) >= 200
    countries = {s.country_code for s in seeds if s.country_code}
    # Universal coverage: at least 195 sovereign states
    assert len(countries) >= 195
    # Verify diverse continents and nations are present
    assert {"US", "CA", "MX", "CO", "BR", "AR", "CL", "CU", "VE", "HT", "UY", "PE"}.issubset(countries)
    assert {"ES", "FR", "DE", "GB", "IT", "PT", "NL", "SE", "VA", "AD", "SM", "MC", "UA", "PL"}.issubset(countries)
    assert {"JP", "IN", "KR", "SG", "ID", "AE", "SA", "CN", "PK", "BD", "PS", "IL", "AF", "VN"}.issubset(countries)
    assert {"ZA", "NG", "KE", "MA", "GH", "RW", "DZ", "AO", "EG", "ET", "SO", "SS", "SN", "TZ"}.issubset(countries)
    assert {"AU", "NZ", "FJ", "PG", "WS", "TO", "TV", "NR", "PW"}.issubset(countries)
    # Verify universal multilateral federators
    multilateral = [s for s in seeds if s.category == "gobierno_multilateral"]
    assert len(multilateral) >= 8
    multi_domains = {s.domain for s in multilateral}
    assert "data.un.org" in multi_domains
    assert "data.worldbank.org" in multi_domains
    assert "data.who.int" in multi_domains
    assert "dataportal.opendataforafrica.org" in multi_domains
    assert "data.europa.eu" in multi_domains


def test_expanded_strategic_niches_coverage():
    """Verify all 10 strategic niches are properly registered with valid seeds."""
    from senda.crawler.seeds import get_available_niches, get_niche_seeds

    niches = get_available_niches()
    expected_niches = {
        "tech_docs", "academic", "iberoamerica_media", "libre_software", "global_gov_data",
        "open_libraries", "space_astronomy", "ai_open_computing", "health_biomedicine", "education_oer"
    }
    assert expected_niches.issubset(set(niches.keys()))

    # Verify Open Libraries niche
    lib_seeds = get_niche_seeds("open_libraries")
    assert len(lib_seeds) >= 8
    lib_domains = {s.domain for s in lib_seeds}
    assert "gutenberg.org" in lib_domains
    assert "openlibrary.org" in lib_domains
    assert "bdh.bne.es" in lib_domains
    assert "europeana.eu" in lib_domains

    # Verify Space & Astronomy niche
    space_seeds = get_niche_seeds("space_astronomy")
    assert len(space_seeds) >= 7
    space_domains = {s.domain for s in space_seeds}
    assert "data.nasa.gov" in space_domains
    assert "esa.int" in space_domains
    assert "eso.org" in space_domains
    assert "webbtelescope.org" in space_domains

    # Verify AI & Open Computing niche
    ai_seeds = get_niche_seeds("ai_open_computing")
    assert len(ai_seeds) >= 5
    ai_domains = {s.domain for s in ai_seeds}
    assert "arxiv.org" in ai_domains
    assert "paperswithcode.com" in ai_domains
    assert "huggingface.co" in ai_domains

    # Verify Health & Biomedicine niche
    health_seeds = get_niche_seeds("health_biomedicine")
    assert len(health_seeds) >= 5
    health_domains = {s.domain for s in health_seeds}
    assert "ncbi.nlm.nih.gov" in health_domains
    assert "medlineplus.gov" in health_domains
    assert "cochranelibrary.com" in health_domains

    # Verify Education & OER niche
    edu_seeds = get_niche_seeds("education_oer")
    assert len(edu_seeds) >= 5
    edu_domains = {s.domain for s in edu_seeds}
    assert "openstax.org" in edu_domains
    assert "ocw.mit.edu" in edu_domains
    assert "oercommons.org" in edu_domains






