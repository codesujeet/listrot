"""Turns raw GitHub repo metadata into a health verdict."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

from .github_client import fetch_repo

DEFAULT_STALE_DAYS = 730  # ~24 months with no push


@dataclass
class RepoStatus:
    owner: str
    repo: str
    status: str  # "ok" | "not_found" | "error"
    archived: bool = False
    disabled: bool = False
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    last_push: datetime | None = None
    days_since_push: int | None = None
    error: str | None = None
    flags: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def is_healthy(self) -> bool:
        return self.status == "ok" and not self.flags


def check_repo(session: requests.Session, owner: str, repo: str, stale_days: int = DEFAULT_STALE_DAYS) -> RepoStatus:
    result = fetch_repo(session, owner, repo)

    if result["status"] == "not_found":
        return RepoStatus(owner, repo, status="not_found", flags=["dead link"])
    if result["status"] == "error":
        return RepoStatus(owner, repo, status="error", error=result["error"])

    data = result["data"]
    flags: list[str] = []

    archived = bool(data.get("archived"))
    disabled = bool(data.get("disabled"))
    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)
    open_issues = data.get("open_issues_count", 0)

    pushed_at_raw = data.get("pushed_at")
    last_push = None
    days_since_push = None
    if pushed_at_raw:
        last_push = datetime.fromisoformat(pushed_at_raw.replace("Z", "+00:00"))
        days_since_push = (datetime.now(timezone.utc) - last_push).days

    if archived:
        flags.append("archived")
    if disabled:
        flags.append("disabled")
    if days_since_push is not None and days_since_push > stale_days and not archived:
        flags.append(f"stale ({days_since_push // 30} months since last push)")

    created_at_raw = data.get("created_at")
    if created_at_raw and stars >= 500:
        created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
        age_days = max((datetime.now(timezone.utc) - created_at).days, 1)
        stars_per_day = stars / age_days
        fork_ratio = forks / stars if stars else 0
        # Heuristic only: very fast, very low-engagement star growth is unusual for organic
        # adoption, but is not proof of inflation on its own — report it as a signal, not a verdict.
        if age_days < 120 and stars_per_day > 50 and fork_ratio < 0.02:
            flags.append("fast, low-engagement star growth (heuristic, verify manually)")

    return RepoStatus(
        owner=owner, repo=repo, status="ok",
        archived=archived, disabled=disabled,
        stars=stars, forks=forks, open_issues=open_issues,
        last_push=last_push, days_since_push=days_since_push,
        flags=flags,
    )
