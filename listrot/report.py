"""Renders a list of RepoStatus results as a console table or a markdown report."""

from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

from .checker import RepoStatus


def render_table(results: list[RepoStatus]) -> Table:
    table = Table(title="listrot report")
    table.add_column("repo", style="bold")
    table.add_column("stars", justify="right")
    table.add_column("last push", justify="right")
    table.add_column("status")

    for r in sorted(results, key=lambda r: (r.status != "ok", -r.stars)):
        if r.status == "not_found":
            table.add_row(r.slug, "-", "-", "[red]dead link[/red]")
        elif r.status == "error":
            table.add_row(r.slug, "-", "-", f"[yellow]check failed ({r.error})[/yellow]")
        else:
            last_push = f"{r.days_since_push}d ago" if r.days_since_push is not None else "unknown"
            flag_text = ", ".join(r.flags) if r.flags else "[green]ok[/green]"
            table.add_row(r.slug, str(r.stars), last_push, flag_text)

    return table


def print_table(results: list[RepoStatus], console: Console | None = None) -> None:
    (console or Console()).print(render_table(results))


def render_markdown(results: list[RepoStatus], source: str) -> str:
    total = len(results)
    dead = sum(1 for r in results if r.status == "not_found")
    flagged = sum(1 for r in results if r.status == "ok" and r.flags)
    healthy = total - dead - flagged - sum(1 for r in results if r.status == "error")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# listrot report",
        "",
        f"Source: {source}",
        f"Generated: {generated_at}",
        "",
        f"- **{total}** repos checked",
        f"- **{healthy}** healthy",
        f"- **{flagged}** flagged",
        f"- **{dead}** dead links",
        "",
        "| Repo | Stars | Last push | Status |",
        "|---|---|---|---|",
    ]

    for r in sorted(results, key=lambda r: (r.status != "ok", -r.stars)):
        if r.status == "not_found":
            lines.append(f"| {r.slug} | - | - | dead link |")
        elif r.status == "error":
            lines.append(f"| {r.slug} | - | - | check failed ({r.error}) |")
        else:
            last_push = f"{r.days_since_push}d ago" if r.days_since_push is not None else "unknown"
            status = ", ".join(r.flags) if r.flags else "ok"
            lines.append(f"| {r.slug} | {r.stars} | {last_push} | {status} |")

    return "\n".join(lines) + "\n"
