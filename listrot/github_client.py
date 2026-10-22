"""Thin wrapper around the GitHub REST API for the metadata listrot needs."""

import subprocess

import requests

API_ROOT = "https://api.github.com"


def resolve_token(explicit_token: str | None) -> str | None:
    """Resolves a GitHub token: explicit arg, then `gh auth token`, then None (unauthenticated)."""
    if explicit_token:
        return explicit_token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        token = result.stdout.strip()
        return token or None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def build_session(token: str | None) -> requests.Session:
    session = requests.Session()
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    session.headers.update(headers)
    return session


def fetch_repo(session: requests.Session, owner: str, repo: str) -> dict:
    """Returns {"status": "ok"|"not_found"|"error", "data": {...} | None}."""
    url = f"{API_ROOT}/repos/{owner}/{repo}"
    try:
        response = session.get(url, timeout=10)
    except requests.RequestException as exc:
        return {"status": "error", "data": None, "error": str(exc)}

    if response.status_code == 404:
        return {"status": "not_found", "data": None, "error": None}
    if response.status_code == 403:
        return {"status": "error", "data": None, "error": "rate_limited"}
    if response.status_code != 200:
        return {"status": "error", "data": None, "error": f"http_{response.status_code}"}

    return {"status": "ok", "data": response.json(), "error": None}


def fetch_readme_text(session: requests.Session, owner: str, repo: str) -> str | None:
    """Fetches a repo's rendered README as raw markdown text, or None if unavailable."""
    url = f"{API_ROOT}/repos/{owner}/{repo}/readme"
    try:
        response = session.get(url, headers={"Accept": "application/vnd.github.raw+json"}, timeout=10)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    return response.text
