"""Tests for src/config.py — Settings loading and validation."""

import pytest

from src.config import Settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FULL_ENV = {
    "OPENAI_API_KEY": "sk-test",
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_test",
    "GITHUB_OWNER": "octocat",
    "GITHUB_REPO": "hello-world",
}


def _make_env(overrides: dict | None = None, *, remove: list[str] | None = None) -> dict:
    env = dict(_FULL_ENV)
    if overrides:
        env.update(overrides)
    for key in remove or []:
        env.pop(key, None)
    return env


# ---------------------------------------------------------------------------
# Happy-path: OpenAI key
# ---------------------------------------------------------------------------


def test_settings_from_env_with_openai_key(monkeypatch):
    """Settings loads correctly when OPENAI_API_KEY is set."""
    for k, v in _make_env().items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    assert settings.openai_api_key == "sk-test"
    assert settings.github_token == "ghp_test"
    assert settings.github_owner == "octocat"
    assert settings.github_repo == "hello-world"
    # OpenAI path must NOT inject the Gemini base URL
    assert settings.openai_base_url is None
    assert settings.openai_model == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Happy-path: Gemini key
# ---------------------------------------------------------------------------


def test_settings_from_env_with_gemini_key(monkeypatch):
    """When only GEMINI_API_KEY is set the Gemini base URL and model are used."""
    env = _make_env(
        {"GEMINI_API_KEY": "AIza-test"},
        remove=["OPENAI_API_KEY"],
    )
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    assert settings.openai_api_key == "AIza-test"
    assert "generativelanguage.googleapis.com" in settings.openai_base_url
    assert settings.openai_model == "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Happy-path: explicit overrides
# ---------------------------------------------------------------------------


def test_settings_custom_model_and_base_url(monkeypatch):
    """OPENAI_MODEL and OPENAI_BASE_URL env vars override the defaults."""
    env = _make_env(
        {
            "OPENAI_MODEL": "gpt-4-turbo",
            "OPENAI_BASE_URL": "https://custom.api/v1/",
        }
    )
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    assert settings.openai_model == "gpt-4-turbo"
    assert settings.openai_base_url == "https://custom.api/v1/"


# ---------------------------------------------------------------------------
# Validation errors - missing required vars
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing_key, expected_fragment",
    [
        ("OPENAI_API_KEY", "GEMINI_API_KEY or OPENAI_API_KEY"),
        ("GITHUB_PERSONAL_ACCESS_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"),
        ("GITHUB_OWNER", "GITHUB_OWNER"),
        ("GITHUB_REPO", "GITHUB_REPO"),
    ],
)
def test_settings_raises_for_missing_required_var(
    monkeypatch, missing_key, expected_fragment
):
    """RuntimeError is raised for each missing required env var."""
    env = _make_env(remove=[missing_key])
    # Unset any key not in our dict so previous test runs don't bleed through
    for k in _FULL_ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    for k, v in env.items():
        monkeypatch.setenv(k, v)

    with pytest.raises(RuntimeError, match=expected_fragment):
        Settings.from_env()


def test_settings_raises_listing_all_missing_vars(monkeypatch):
    """Error message lists every missing variable when several are absent."""
    for k in _FULL_ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        Settings.from_env()

    msg = str(exc_info.value)
    assert "GEMINI_API_KEY or OPENAI_API_KEY" in msg
    assert "GITHUB_PERSONAL_ACCESS_TOKEN" in msg
    assert "GITHUB_OWNER" in msg
    assert "GITHUB_REPO" in msg


# ---------------------------------------------------------------------------
# Immutability (frozen dataclass)
# ---------------------------------------------------------------------------


def test_settings_is_frozen(monkeypatch):
    """Settings must be immutable — assignment raises FrozenInstanceError."""
    for k, v in _make_env().items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    with pytest.raises(Exception):  # FrozenInstanceError is a subtype
        settings.openai_api_key = "hacked"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# OpenAI key takes precedence over Gemini key when both are set
# ---------------------------------------------------------------------------


def test_openai_key_takes_precedence_over_gemini(monkeypatch):
    """When both OPENAI_API_KEY and GEMINI_API_KEY are set, OpenAI wins."""
    env = _make_env({"GEMINI_API_KEY": "AIza-test"})
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    # OpenAI key should be used, NOT the Gemini key
    assert settings.openai_api_key == "sk-test"
    # Gemini base URL must NOT be injected
    assert settings.openai_base_url is None


# ---------------------------------------------------------------------------
# _clean_env — GitHub Actions CI mask / blank variable defence
# This is the root cause of the `Illegal header value b'*** '` crash:
# GitHub Actions injects empty strings or masked `***` values for undefined
# repository variables. These must NEVER be forwarded as HTTP headers.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_value",
    [
        "",           # undefined GitHub Actions variable
        "   ",        # whitespace only
        "***",        # fully masked secret (GitHub Actions log mask)
        "*** ",       # masked + trailing space (the exact crash value)
        " *** ",      # masked with surrounding whitespace
        "****",       # longer mask
    ],
)
def test_blank_or_masked_openai_model_falls_back_to_default(monkeypatch, bad_value):
    """Blank/masked OPENAI_MODEL must fall back to the provider default, not crash."""
    for k, v in _make_env({"OPENAI_MODEL": bad_value}).items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    # Must resolve to the real default, never forward the masked/blank value
    assert settings.openai_model == "gpt-4o-mini"


@pytest.mark.parametrize(
    "bad_value",
    [
        "",
        "   ",
        "***",
        "*** ",
    ],
)
def test_blank_or_masked_openai_base_url_falls_back_to_none(monkeypatch, bad_value):
    """Blank/masked OPENAI_BASE_URL must be treated as absent (None), not crash."""
    for k, v in _make_env({"OPENAI_BASE_URL": bad_value}).items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    assert settings.openai_base_url is None


def test_masked_api_key_treated_as_missing(monkeypatch):
    """A masked GEMINI_API_KEY (***) must be treated as absent → RuntimeError."""
    env = _make_env({"GEMINI_API_KEY": "***"}, remove=["OPENAI_API_KEY"])
    for k in _FULL_ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY or OPENAI_API_KEY"):
        Settings.from_env()


def test_whitespace_trimmed_from_valid_values(monkeypatch):
    """Leading/trailing whitespace in real (non-masked) values is stripped."""
    env = _make_env(
        {
            "OPENAI_MODEL": "  gpt-4-turbo  ",
            "OPENAI_BASE_URL": "  https://custom.api/v1/  ",
        }
    )
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    settings = Settings.from_env()

    assert settings.openai_model == "gpt-4-turbo"
    assert settings.openai_base_url == "https://custom.api/v1/"
