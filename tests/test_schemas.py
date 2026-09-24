"""Tests for src/schemas.py — Pydantic model validation."""

import pytest
from pydantic import ValidationError

from src.schemas import Finding, ReviewResult


# ---------------------------------------------------------------------------
# Finding — valid construction
# ---------------------------------------------------------------------------


def test_finding_minimal_valid():
    """Finding is constructed with only required fields."""
    f = Finding(
        category="security",
        severity="high",
        file="main.py",
        title="Hardcoded secret",
        description="API key found in source.",
        recommendation="Use environment variables.",
        confidence=0.9,
    )
    assert f.category == "security"
    assert f.severity == "high"
    assert f.line is None


def test_finding_with_line_number():
    """Finding accepts a valid positive line number."""
    f = Finding(
        category="performance",
        severity="medium",
        file="utils.py",
        line=42,
        title="N+1 query",
        description="Query inside loop.",
        recommendation="Batch the queries.",
        confidence=0.75,
    )
    assert f.line == 42


@pytest.mark.parametrize("category", ["security", "standards", "tests", "performance"])
def test_finding_all_valid_categories(category):
    """All four allowed categories are accepted."""
    f = Finding(
        category=category,
        severity="low",
        file="x.py",
        title="T",
        description="D",
        recommendation="R",
        confidence=0.5,
    )
    assert f.category == category


@pytest.mark.parametrize("severity", ["critical", "high", "medium", "low", "info"])
def test_finding_all_valid_severities(severity):
    """All five allowed severities are accepted."""
    f = Finding(
        category="tests",
        severity=severity,
        file="x.py",
        title="T",
        description="D",
        recommendation="R",
        confidence=0.5,
    )
    assert f.severity == severity


# ---------------------------------------------------------------------------
# Finding — boundary values for confidence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_finding_confidence_boundary_values(confidence):
    """Confidence accepts 0.0, 0.5, and 1.0."""
    f = Finding(
        category="security",
        severity="info",
        file="x.py",
        title="T",
        description="D",
        recommendation="R",
        confidence=confidence,
    )
    assert f.confidence == confidence


# ---------------------------------------------------------------------------
# Finding — validation errors
# ---------------------------------------------------------------------------


def test_finding_rejects_invalid_category():
    """Unknown category raises a ValidationError."""
    with pytest.raises(ValidationError):
        Finding(
            category="unknown",  # type: ignore[arg-type]
            severity="high",
            file="x.py",
            title="T",
            description="D",
            recommendation="R",
            confidence=0.5,
        )


def test_finding_rejects_invalid_severity():
    """Unknown severity raises a ValidationError."""
    with pytest.raises(ValidationError):
        Finding(
            category="security",
            severity="critical-plus",  # type: ignore[arg-type]
            file="x.py",
            title="T",
            description="D",
            recommendation="R",
            confidence=0.5,
        )


def test_finding_rejects_confidence_above_1():
    """Confidence > 1.0 raises a ValidationError."""
    with pytest.raises(ValidationError):
        Finding(
            category="security",
            severity="high",
            file="x.py",
            title="T",
            description="D",
            recommendation="R",
            confidence=1.1,
        )


def test_finding_rejects_confidence_below_0():
    """Confidence < 0.0 raises a ValidationError."""
    with pytest.raises(ValidationError):
        Finding(
            category="security",
            severity="high",
            file="x.py",
            title="T",
            description="D",
            recommendation="R",
            confidence=-0.01,
        )


def test_finding_rejects_line_zero():
    """line=0 violates the ge=1 constraint."""
    with pytest.raises(ValidationError):
        Finding(
            category="security",
            severity="high",
            file="x.py",
            line=0,
            title="T",
            description="D",
            recommendation="R",
            confidence=0.5,
        )


def test_finding_rejects_negative_line():
    """Negative line numbers violate the ge=1 constraint."""
    with pytest.raises(ValidationError):
        Finding(
            category="security",
            severity="high",
            file="x.py",
            line=-5,
            title="T",
            description="D",
            recommendation="R",
            confidence=0.5,
        )


# ---------------------------------------------------------------------------
# ReviewResult — aggregation
# ---------------------------------------------------------------------------


def test_review_result_defaults_to_empty_list():
    """ReviewResult.findings defaults to an empty list."""
    result = ReviewResult()
    assert result.findings == []


def test_review_result_with_findings():
    """ReviewResult stores a list of Finding objects."""
    finding = Finding(
        category="security",
        severity="critical",
        file="auth.py",
        line=99,
        title="SQL injection",
        description="Unparameterized query.",
        recommendation="Use ORM or parameterized queries.",
        confidence=0.99,
    )
    result = ReviewResult(findings=[finding])
    assert len(result.findings) == 1
    assert result.findings[0].severity == "critical"
