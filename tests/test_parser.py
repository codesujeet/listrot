from listrot.parser import extract_repo_links


def test_extracts_basic_links():
    text = "- [Foo](https://github.com/alice/foo) is great\n- [Bar](https://github.com/bob/bar)"
    assert extract_repo_links(text) == [("alice", "foo"), ("bob", "bar")]


def test_deduplicates_repeated_links():
    text = "https://github.com/alice/foo and again https://github.com/alice/foo"
    assert extract_repo_links(text) == [("alice", "foo")]


def test_strips_git_suffix_and_trailing_slash():
    text = "https://github.com/alice/foo.git and https://github.com/bob/bar/"
    assert extract_repo_links(text) == [("alice", "foo"), ("bob", "bar")]


def test_ignores_non_user_github_paths():
    text = "https://github.com/sponsors/alice and https://github.com/topics/python"
    assert extract_repo_links(text) == []


def test_preserves_dots_in_repo_names():
    text = "https://github.com/RocketChat/Rocket.Chat"
    assert extract_repo_links(text) == [("RocketChat", "Rocket.Chat")]


def test_no_links_returns_empty_list():
    assert extract_repo_links("just some text, no links here") == []
