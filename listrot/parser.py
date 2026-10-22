"""Extracts GitHub repo references (owner, repo) from markdown text."""

import re

_LINK_PATTERN = re.compile(
    r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)

# Path segments that are GitHub features, not usernames/orgs.
_RESERVED_OWNERS = {
    "sponsors", "orgs", "topics", "marketplace", "apps", "features",
    "settings", "notifications", "issues", "pulls", "search", "trending",
    "collections", "about", "pricing", "contact", "login", "join",
    "security", "customer-stories", "readme", "resources", "events",
}


def extract_repo_links(markdown_text: str) -> list[tuple[str, str]]:
    """Returns deduplicated (owner, repo) pairs found in the text, in first-seen order."""
    seen: dict[tuple[str, str], None] = {}
    for owner, repo in _LINK_PATTERN.findall(markdown_text):
        owner_lower = owner.lower()
        if owner_lower in _RESERVED_OWNERS:
            continue
        repo = repo.rstrip("/")
        if repo.endswith(".git"):
            repo = repo[:-4]
        if not repo or not owner:
            continue
        seen.setdefault((owner, repo), None)
    return list(seen.keys())
