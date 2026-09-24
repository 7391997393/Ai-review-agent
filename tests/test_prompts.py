"""Tests for src/prompts.py — prompt building correctness.

Covers:
  - All four review categories produce non-empty prompts
  - BASE_INSTRUCTIONS are always included
  - Category-specific instructions are included for the right category
  - Context is injected only when non-empty
  - Invalid category raises KeyError (guard against typos)
"""

import pytest

from src.prompts import BASE_INSTRUCTIONS, CATEGORY_INSTRUCTIONS, build_prompt


# ---------------------------------------------------------------------------
# All categories produce valid prompts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("category", ["security", "standards", "tests", "performance"])
def test_build_prompt_returns_non_empty_string(category):
    result = build_prompt(category)
    assert isinstance(result, str)
    assert len(result.strip()) > 0


@pytest.mark.parametrize("category", ["security", "standards", "tests", "performance"])
def test_build_prompt_includes_base_instructions(category):
    """BASE_INSTRUCTIONS sentinel text must appear in every prompt."""
    result = build_prompt(category)
    # The instruction warns about untrusted data — a security-critical note
    assert "UNTRUSTED DATA" in result


@pytest.mark.parametrize("category", ["security", "standards", "tests", "performance"])
def test_build_prompt_includes_category_name(category):
    result = build_prompt(category)
    assert category in result


# ---------------------------------------------------------------------------
# Category-specific instructions are correct
# ---------------------------------------------------------------------------


def test_security_prompt_mentions_injection():
    result = build_prompt("security")
    assert "injection" in result.lower()


def test_performance_prompt_mentions_n_plus_1():
    result = build_prompt("performance")
    assert "N+1" in result or "n+1" in result.lower()


def test_tests_prompt_mentions_coverage_disclaimer():
    result = build_prompt("tests")
    assert "coverage" in result.lower()


def test_standards_prompt_mentions_readability():
    result = build_prompt("standards")
    assert "readability" in result.lower()


# ---------------------------------------------------------------------------
# Context injection
# ---------------------------------------------------------------------------


def test_build_prompt_with_context_includes_context():
    result = build_prompt("security", context="diff content here")
    assert "diff content here" in result
    assert "Pull Request context" in result


def test_build_prompt_without_context_omits_context_section():
    result = build_prompt("security")
    assert "Pull Request context" not in result


def test_build_prompt_empty_string_context_omits_section():
    """Passing context='' (the default) must not add the context section."""
    result = build_prompt("security", context="")
    assert "Pull Request context" not in result


# ---------------------------------------------------------------------------
# Invalid category raises KeyError
# ---------------------------------------------------------------------------


def test_build_prompt_raises_for_unknown_category():
    """A typo in category must fail loudly, not silently return empty."""
    with pytest.raises(KeyError):
        build_prompt("typo_category")


# ---------------------------------------------------------------------------
# CATEGORY_INSTRUCTIONS dict completeness
# ---------------------------------------------------------------------------


def test_category_instructions_has_all_four_categories():
    expected = {"security", "standards", "tests", "performance"}
    assert set(CATEGORY_INSTRUCTIONS.keys()) == expected


def test_all_category_instructions_are_non_empty():
    for category, text in CATEGORY_INSTRUCTIONS.items():
        assert text.strip(), f"CATEGORY_INSTRUCTIONS[{category!r}] is empty"
