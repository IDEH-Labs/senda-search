# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Command-line interface (CLI) for Senda Search Engine administration."""

import argparse
import asyncio
import sys
from urllib.parse import urlparse
import uvicorn

from senda.config import settings
from senda.crawler.runner import CrawlerRunner
from senda.indexer.storage import StorageEngine
from senda.ranking.retriever import SearchRetriever


def format_bytes(size: int) -> str:
    """Format bytes into human-readable representation."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def cmd_stats(args):
    """Display index statistics."""
    storage = StorageEngine()
    stats = storage.get_stats()
    print("\n=== Senda Index Statistics ===")
    print(f"Database Path:    {stats['database_path']}")
    print(f"Total Documents:  {stats['total_documents']:,}")
    print(f"Total Domains:    {stats['total_domains']:,}")
    print(f"Storage Size:     {format_bytes(stats['database_size_bytes'])}")
    print("===============================\n")


def cmd_search(args):
    """Execute search query in the terminal."""
    storage = StorageEngine()
    retriever = SearchRetriever(storage)
    results = retriever.search(args.query, page=args.page, page_size=args.limit, category=args.category)

    cat_label = f" [{args.category.upper()}]" if args.category != "all" else ""
    print(f"\nSenda Search{cat_label}: '{args.query}'")
    print(f"Matched {results.total_matches} items in {results.duration_ms} ms (Page {results.page}/{results.total_pages or 1})\n")

    if not results.items:
        print("No matching items found.")
        return

    for i, item in enumerate(results.items, start=1):
        clean_snippet = item.snippet.replace("<mark>", "\033[1;33m").replace("</mark>", "\033[0m")
        badge = f" [{item.doc_type.upper()}]" if item.doc_type != "web" else ""
        print(f"[{i}]\033[1;35m{badge}\033[0m \033[1;34m{item.title}\033[0m")
        if item.media_url:
            print(f"    \033[36mMedia: {item.media_url}\033[0m")
        print(f"    \033[90m{item.url}\033[0m")
        print(f"    {clean_snippet}")
        print(f"    \033[32m[BM25 Score: {item.relevance_score}]\033[0m\n")


def cmd_crawl(args):
    """Crawl web pages starting from a seed URL or seeds file."""
    seeds = []
    if args.seed:
        seeds.append(args.seed)
    if args.seeds_file:
        from pathlib import Path
        seeds_path = Path(args.seeds_file)
        if not seeds_path.exists():
            print(f"Error: Seeds file not found: {args.seeds_file}")
            return
        for line in seeds_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                seeds.append(line)

    if not seeds:
        print("Error: Must provide either a seed URL or --seeds-file.")
        return

    runner = CrawlerRunner()

    def progress(url: str, title: str, count: int):
        print(f"[{count}/{args.max_pages}] Indexed: {title[:50]}... ({url})")

    print(f"\n[Senda Crawler] Starting crawl with {len(seeds)} seed(s)")
    print(f"Max Pages: {args.max_pages} | Max Depth: {args.max_depth} | Politeness: {settings.DEFAULT_CRAWL_DELAY_SECONDS}s")

    try:
        indexed = asyncio.run(
            runner.crawl_seeds(
                seed_urls=seeds,
                max_pages=args.max_pages,
                max_depth=args.max_depth,
                on_page_indexed=progress,
            )
        )
        print(f"\n[Crawl Complete] Successfully indexed {indexed} new/updated documents.\n")
    except KeyboardInterrupt:
        print("\n[Crawl Cancelled] Interrupted by user.")


def cmd_purge_domain(args):
    """Purge all indexed documents from a specified domain."""
    storage = StorageEngine()
    deleted = storage.purge_domain(args.domain)
    print(f"Purged {deleted} document(s) belonging to domain '{args.domain}'.")


def cmd_purge_url(args):
    """Purge a specific URL from the index."""
    storage = StorageEngine()
    deleted = storage.purge_url(args.url)
    print(f"Purged {deleted} document matching URL '{args.url}'.")


def cmd_serve(args):
    """Launch the Senda web server."""
    host = args.host or settings.SERVER_HOST
    port = args.port or settings.SERVER_PORT
    print(f"Starting Senda Sovereign Search Web UI on http://{host}:{port}")
    uvicorn.run("senda.api.app:app", host=host, port=port, log_level="info")


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="senda",
        description="Senda Sovereign Search Engine - CLI & Administration Tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: stats
    subparsers.add_parser("stats", help="Display search index metrics")

    # Command: search
    p_search = subparsers.add_parser("search", help="Query the local search index")
    p_search.add_argument("query", help="Search terms or quoted phrases")
    p_search.add_argument("--category", choices=["all", "web", "news", "images", "library"], default="all", help="Search vertical (default: all)")
    p_search.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_search.add_argument("--limit", type=int, default=10, help="Results per page (default: 10)")

    # Command: crawl
    p_crawl = subparsers.add_parser("crawl", help="Crawl and index websites")
    p_crawl.add_argument("seed", nargs="?", default=None, help="Seed URL to begin crawling")
    p_crawl.add_argument("--seeds-file", help="Path to text file containing seed URLs (one per line)")
    p_crawl.add_argument("--max-pages", type=int, default=10, help="Max documents to index (default: 10)")
    p_crawl.add_argument("--max-depth", type=int, default=2, help="Max link hop depth (default: 2)")

    # Command: purge-domain
    p_purgd = subparsers.add_parser("purge-domain", help="Takedown/purge entire domain from index")
    p_purgd.add_argument("domain", help="Domain name to purge (e.g. example.com)")

    # Command: purge-url
    p_purgu = subparsers.add_parser("purge-url", help="Takedown/purge single URL from index")
    p_purgu.add_argument("url", help="Exact URL to purge")

    # Command: serve
    p_serve = subparsers.add_parser("serve", help="Run the web search interface and API")
    p_serve.add_argument("--host", default=None, help=f"Host interface (default: {settings.SERVER_HOST})")
    p_serve.add_argument("--port", type=int, default=None, help=f"Port number (default: {settings.SERVER_PORT})")

    args = parser.parse_args()

    commands = {
        "stats": cmd_stats,
        "search": cmd_search,
        "crawl": cmd_crawl,
        "purge-domain": cmd_purge_domain,
        "purge-url": cmd_purge_url,
        "serve": cmd_serve,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
