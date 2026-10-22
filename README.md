# listrot

Checks every GitHub repo linked in an `awesome-*` list (or any markdown list) for dead links, archived/disabled repos, staleness, and suspicious star growth.

Awesome-lists rot. Projects get archived, maintainers disappear, repos get renamed or deleted — and the list keeps linking to them as if nothing changed. `listrot` points at a list and tells you what's actually still alive.

## Install

```bash
pip install listrot
```

Or run it straight from source:

```bash
git clone https://github.com/codesujeet/listrot
cd listrot
pip install -e .
```

## Usage

```bash
# Check a GitHub repo's README directly
listrot sindresorhus/awesome

# Check any markdown file by URL
listrot https://raw.githubusercontent.com/vinta/awesome-python/master/README.md

# Check a local file
listrot ./my-list.md

# Write a markdown report
listrot sindresorhus/awesome --output report.md
```

Real run against [sindresorhus/awesome](https://github.com/sindresorhus/awesome) (673 linked repos):

```
673 repos checked
439 healthy
234 flagged
0 dead links
```

`prakhar1989/awesome-courses` — stale, 42 months since last push. `tiimgreen/github-cheat-sheet` — stale, 30 months. Both still listed as current.

## What it checks

- **Dead links** — repo renamed, deleted, or never existed.
- **Archived / disabled** — the repo itself says it's done.
- **Staleness** — no push in a configurable window (default 24 months).
- **Fast, low-engagement star growth** — a heuristic flag (not a verdict) for repos with unusually high stars relative to age and forks. Verify manually before drawing conclusions; this flags a pattern, not fraud.

## Authentication

`listrot` shells out to `gh auth token` automatically if you have the [GitHub CLI](https://cli.github.com/) installed and authenticated, to avoid the 60-requests/hour unauthenticated rate limit. Pass `--token` to override, or just run unauthenticated for small lists.

## Options

```
listrot <source> [--stale-days N] [--output FILE] [--token TOKEN] [--concurrency N]
```

| Flag | Default | Meaning |
|---|---|---|
| `--stale-days` | 730 | Days without a push before a repo is flagged stale |
| `--output`, `-o` | - | Write a markdown report to this file |
| `--token` | - | GitHub token (falls back to `gh auth token`) |
| `--concurrency` | 8 | Parallel API requests |

## Development

```bash
pip install -e . pytest
pytest
```

## License

MIT
