"""Command-line entry point: listrot <source> [options]."""

import argparse
import concurrent.futures
import re
import sys

from rich.console import Console

from .checker import DEFAULT_STALE_DAYS, check_repo
from .github_client import build_session, fetch_readme_text, resolve_token
from .parser import extract_repo_links
from .report import print_table, render_markdown

_OWNER_REPO_SHORTHAND = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _load_source_text(source: str, session) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        import requests
        response = requests.get(source, timeout=15)
        response.raise_for_status()
        return response.text

    if _OWNER_REPO_SHORTHAND.match(source):
        owner, repo = source.split("/", 1)
        text = fetch_readme_text(session, owner, repo)
        if text is None:
            raise SystemExit(f"Could not fetch README for {source}")
        return text

    with open(source, encoding="utf-8") as f:
        return f.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="listrot",
        description="Checks every GitHub repo linked in a markdown list for dead links, "
                    "archived/disabled status, staleness, and suspicious star growth.",
    )
    parser.add_argument(
        "source",
        help="A URL to a markdown file, an owner/repo shorthand (reads its README), "
             "or a local file path.",
    )
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS,
                         help=f"Days without a push before a repo is flagged stale (default: {DEFAULT_STALE_DAYS}).")
    parser.add_argument("--output", "-o", help="Write a markdown report to this file.")
    parser.add_argument("--token", help="GitHub token to use instead of `gh auth token`.")
    parser.add_argument("--concurrency", type=int, default=8, help="Parallel API requests (default: 8).")
    args = parser.parse_args(argv)

    console = Console()
    token = resolve_token(args.token)
    if not token:
        console.print("[yellow]No GitHub token found (gh auth token failed) — unauthenticated "
                       "rate limits apply (60 requests/hour).[/yellow]")
    session = build_session(token)

    console.print(f"Fetching [bold]{args.source}[/bold]...")
    text = _load_source_text(args.source, session)

    links = extract_repo_links(text)
    if not links:
        console.print("[yellow]No GitHub repo links found in the source.[/yellow]")
        return 0

    console.print(f"Found [bold]{len(links)}[/bold] repo links. Checking...")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(check_repo, session, owner, repo, args.stale_days) for owner, repo in links]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    print_table(results, console)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(render_markdown(results, args.source))
        console.print(f"Report written to [bold]{args.output}[/bold]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
