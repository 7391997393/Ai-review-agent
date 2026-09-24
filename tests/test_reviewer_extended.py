"""Tests for src/reviewer.py — build_model and review_all_categories.

Uses unittest.mock to avoid real API calls.
Covers:
  - build_model returns a ChatOpenAI instance with correct parameters
  - review_all_categories calls structured model and returns findings
  - Prompt combines all four categories
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.reviewer import CATEGORIES, build_model, review_all_categories
from src.schemas import Finding, ReviewResult


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_settings():
    s = MagicMock()
    s.openai_model = "gpt-4o-mini"
    s.openai_api_key = "sk-test"
    s.openai_base_url = None
    return s


# ---------------------------------------------------------------------------
# build_model
# ---------------------------------------------------------------------------


def test_build_model_returns_callable(fake_settings):
    """build_model is importable and callable — no dead code paths."""
    assert callable(build_model)


def test_build_model_passes_model_name(fake_settings):
    """build_model forwards settings.openai_model to ChatOpenAI."""
    with patch("src.reviewer.ChatOpenAI") as MockChatOpenAI:
        build_model(fake_settings)
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"


def test_build_model_passes_api_key(fake_settings):
    """build_model forwards settings.openai_api_key to ChatOpenAI."""
    with patch("src.reviewer.ChatOpenAI") as MockChatOpenAI:
        build_model(fake_settings)
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["api_key"] == "sk-test"


def test_build_model_passes_base_url(fake_settings):
    """build_model forwards settings.openai_base_url (including None) to ChatOpenAI."""
    with patch("src.reviewer.ChatOpenAI") as MockChatOpenAI:
        build_model(fake_settings)
        call_kwargs = MockChatOpenAI.call_args.kwargs
        assert call_kwargs["base_url"] is None


def test_build_model_sets_timeout(fake_settings):
    with patch("src.reviewer.ChatOpenAI") as MockChatOpenAI:
        build_model(fake_settings)
        assert MockChatOpenAI.call_args.kwargs["timeout"] == 120


def test_build_model_sets_max_retries(fake_settings):
    with patch("src.reviewer.ChatOpenAI") as MockChatOpenAI:
        build_model(fake_settings)
        assert MockChatOpenAI.call_args.kwargs["max_retries"] == 6


# ---------------------------------------------------------------------------
# CATEGORIES constant
# ---------------------------------------------------------------------------


def test_categories_contains_all_four():
    assert set(CATEGORIES) == {"security", "standards", "tests", "performance"}


# ---------------------------------------------------------------------------
# review_all_categories — mocked LLM
# ---------------------------------------------------------------------------


def _make_structured_mock(return_value):
    """Return a MagicMock whose .ainvoke is an AsyncMock returning return_value."""
    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(return_value=return_value)
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_structured
    return mock_model, mock_structured


@pytest.mark.anyio
async def test_review_all_categories_returns_findings(fake_settings):
    """review_all_categories returns the findings list from the structured model."""
    expected_finding = Finding(
        category="security",
        severity="high",
        file="app.py",
        title="Hardcoded secret",
        description="API key in source.",
        recommendation="Use env vars.",
        confidence=0.9,
    )
    mock_result = ReviewResult(findings=[expected_finding])
    mock_model, _ = _make_structured_mock(mock_result)

    with patch("src.reviewer.build_model", return_value=mock_model):
        findings = await review_all_categories(fake_settings, "some diff context")

    assert len(findings) == 1
    assert findings[0].severity == "high"


@pytest.mark.anyio
async def test_review_all_categories_returns_empty_list(fake_settings):
    """review_all_categories returns an empty list when model finds nothing."""
    mock_result = ReviewResult(findings=[])
    mock_model, _ = _make_structured_mock(mock_result)

    with patch("src.reviewer.build_model", return_value=mock_model):
        findings = await review_all_categories(fake_settings, "")

    assert findings == []


@pytest.mark.anyio
async def test_review_all_categories_prompt_includes_all_categories(fake_settings):
    """The combined prompt sent to the model includes all four category names."""
    mock_result = ReviewResult(findings=[])
    captured_prompt: list[str] = []

    async def capture_ainvoke(prompt: str, **kwargs):
        captured_prompt.append(prompt)
        return mock_result

    mock_structured = MagicMock()
    mock_structured.ainvoke = capture_ainvoke
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_structured

    with patch("src.reviewer.build_model", return_value=mock_model):
        await review_all_categories(fake_settings, "ctx")

    assert captured_prompt, "ainvoke was never called"
    prompt_text = captured_prompt[0]
    for cat in ["security", "standards", "tests", "performance"]:
        assert cat in prompt_text, f"Category '{cat}' missing from combined prompt"
