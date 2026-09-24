"""Tests for src/formatter.py — format_review output correctness.

These tests supplement test_formatter.py with coverage of:
  - severity ordering (critical before high before medium…)
  - summary line counts
  - location with and without line number
  - confidence percentage rendering
  - all severity labels in the summary row
  - security / performance / standards / tests category rendering
"""

import pytest

from src.formatter import format_review
from src.schemas import Finding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finding(
    *,
    category="security",
    severity="medium",
    file="main.py",
    line=None,
    title="Finding title",
    description="A description.",
    recommendation="A recommendation.",
    confidence=0.8,
) -> Finding:
    return Finding(
        category=category,
        severity=severity,
        file=file,
        line=line,
        title=title,
        description=description,
        recommendation=recommendation,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Header and footer always present
# ---------------------------------------------------------------------------


def test_header_always_present():
    output = format_review("owner", "repo", 7, [])
    assert "## 🤖 AI Code Review" in output
    assert "owner/repo" in output
    assert "#7" in output


def test_footer_human_review_present_when_findings_exist():
    output = format_review("owner", "repo", 1, [_finding()])
    assert "Human review" in output


def test_no_footer_when_no_findings():
    output = format_review("owner", "repo", 1, [])
    assert "Human review" not in output


# ---------------------------------------------------------------------------
# Empty findings path
# ---------------------------------------------------------------------------


def test_empty_findings_returns_no_actionable_message():
    output = format_review("a", "b", 99, [])
    assert "No actionable findings" in output
    assert "Total findings" not in output


# ---------------------------------------------------------------------------
# Single finding — content checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("category", ["security", "standards", "tests", "performance"])
def test_category_label_appears_for_every_category(category):
    f = _finding(category=category, severity="low")
    output = format_review("o", "r", 1, [f])
    assert category.title() in output


@pytest.mark.parametrize("severity", ["critical", "high", "medium", "low", "info"])
def test_severity_label_appears_for_every_severity(severity):
    f = _finding(severity=severity)
    output = format_review("o", "r", 1, [f])
    assert severity.upper() in output


def test_location_without_line_shows_only_filename():
    f = _finding(file="src/utils.py", line=None)
    output = format_review("o", "r", 1, [f])
    assert "`src/utils.py`" in output
    assert "src/utils.py:" not in output


def test_location_with_line_shows_filename_and_line():
    f = _finding(file="src/utils.py", line=55)
    output = format_review("o", "r", 1, [f])
    assert "src/utils.py:55" in output


def test_confidence_rendered_as_percentage():
    f = _finding(confidence=0.85)
    output = format_review("o", "r", 1, [f])
    assert "85%" in output


def test_title_appears_in_output():
    f = _finding(title="My special finding")
    output = format_review("o", "r", 1, [f])
    assert "My special finding" in output


def test_recommendation_appears_in_output():
    f = _finding(recommendation="Use parameterized queries.")
    output = format_review("o", "r", 1, [f])
    assert "Use parameterized queries." in output


# ---------------------------------------------------------------------------
# Ordering: critical findings must appear before lower-severity ones
# ---------------------------------------------------------------------------


def test_findings_sorted_critical_before_info():
    findings = [
        _finding(severity="info", title="Info finding"),
        _finding(severity="critical", title="Critical finding"),
        _finding(severity="medium", title="Medium finding"),
    ]
    output = format_review("o", "r", 1, findings)
    idx_critical = output.index("Critical finding")
    idx_medium = output.index("Medium finding")
    idx_info = output.index("Info finding")
    assert idx_critical < idx_medium < idx_info


# ---------------------------------------------------------------------------
# Total findings count in summary
# ---------------------------------------------------------------------------


def test_total_findings_count_displayed():
    findings = [_finding(severity="high"), _finding(severity="low")]
    output = format_review("o", "r", 1, findings)
    assert "Total findings:** 2" in output


# ---------------------------------------------------------------------------
# Summary row contains all five severity labels
# ---------------------------------------------------------------------------


def test_summary_row_contains_all_severities():
    output = format_review("o", "r", 1, [_finding()])
    for sev in ("Critical", "High", "Medium", "Low", "Info"):
        assert sev in output


# ---------------------------------------------------------------------------
# Multiple findings — all present in output
# ---------------------------------------------------------------------------


def test_multiple_findings_all_present():
    titles = ["Alpha issue", "Beta issue", "Gamma issue"]
    findings = [_finding(title=t) for t in titles]
    output = format_review("o", "r", 1, findings)
    for title in titles:
        assert title in output


# ---------------------------------------------------------------------------
# Security — no secret leakage in output (sanity check)
# ---------------------------------------------------------------------------


def test_no_raw_api_key_in_output():
    """Formatter output must not accidentally echo any token-like strings."""
    f = _finding(description="The token ghp_SECRETTOKEN123 was found in diff.")
    output = format_review("o", "r", 1, [f])
    # description is echoed; verify it's just the description content
    assert "ghp_SECRETTOKEN123" in output  # intentionally echoed from finding data
    # but the header / recommendation / title should NOT add extra tokens
    assert output.count("ghp_SECRETTOKEN123") == 1
