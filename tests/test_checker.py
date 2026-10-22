from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from listrot.checker import check_repo


def _mock_session(json_data=None, status_code=200):
    session = MagicMock()
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    session.get.return_value = response
    return session


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_not_found_repo_is_flagged_dead_link():
    session = _mock_session(status_code=404)
    result = check_repo(session, "nobody", "ghost")
    assert result.status == "not_found"
    assert "dead link" in result.flags


def test_healthy_recent_repo_has_no_flags():
    now = datetime.now(timezone.utc)
    session = _mock_session({
        "archived": False, "disabled": False,
        "stargazers_count": 10, "forks_count": 2, "open_issues_count": 1,
        "pushed_at": _iso(now - timedelta(days=5)),
        "created_at": _iso(now - timedelta(days=400)),
    })
    result = check_repo(session, "alice", "foo")
    assert result.status == "ok"
    assert result.flags == []


def test_archived_repo_is_flagged():
    now = datetime.now(timezone.utc)
    session = _mock_session({
        "archived": True, "disabled": False,
        "stargazers_count": 10, "forks_count": 2, "open_issues_count": 0,
        "pushed_at": _iso(now - timedelta(days=5)),
        "created_at": _iso(now - timedelta(days=400)),
    })
    result = check_repo(session, "alice", "foo")
    assert "archived" in result.flags


def test_stale_repo_is_flagged():
    now = datetime.now(timezone.utc)
    session = _mock_session({
        "archived": False, "disabled": False,
        "stargazers_count": 10, "forks_count": 2, "open_issues_count": 0,
        "pushed_at": _iso(now - timedelta(days=900)),
        "created_at": _iso(now - timedelta(days=1500)),
    })
    result = check_repo(session, "alice", "foo", stale_days=730)
    assert any("stale" in flag for flag in result.flags)


def test_fast_low_engagement_star_growth_is_flagged():
    now = datetime.now(timezone.utc)
    session = _mock_session({
        "archived": False, "disabled": False,
        "stargazers_count": 10000, "forks_count": 5, "open_issues_count": 0,
        "pushed_at": _iso(now - timedelta(days=1)),
        "created_at": _iso(now - timedelta(days=10)),
    })
    result = check_repo(session, "alice", "viral")
    assert any("star growth" in flag for flag in result.flags)


def test_slow_organic_growth_is_not_flagged():
    now = datetime.now(timezone.utc)
    session = _mock_session({
        "archived": False, "disabled": False,
        "stargazers_count": 10000, "forks_count": 1500, "open_issues_count": 0,
        "pushed_at": _iso(now - timedelta(days=1)),
        "created_at": _iso(now - timedelta(days=2000)),
    })
    result = check_repo(session, "alice", "mature")
    assert result.flags == []
