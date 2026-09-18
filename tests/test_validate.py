import pytest

from src.pipelines.validate import (
    ValidationStatus,
    validate_text,
)


def test_healthy_text_passes() -> None:
    extracted = "Lumine Reader is a document processing system."
    cleaned = "Lumine Reader is a document processing system."

    result = validate_text(extracted, cleaned)

    assert result.status == ValidationStatus.PASS
    assert result.issues == ()
    assert result.retention_ratio == 1.0


def test_empty_cleaned_text_fails() -> None:
    extracted = "This document originally contained useful information."
    cleaned = ""

    result = validate_text(extracted, cleaned)

    assert result.status == ValidationStatus.FAIL
    assert "EMPTY_CLEANED_TEXT" in result.issues
    assert "NO_MEANINGFUL_CONTENT" in result.issues
    assert "LOW_CONTENT_RETENTION" not in result.issues


def test_noise_only_text_fails() -> None:
    extracted = "This document originally contained useful information."
    cleaned = "!!! --- ???"

    result = validate_text(extracted, cleaned)

    assert result.status == ValidationStatus.FAIL
    assert "NO_MEANINGFUL_CONTENT" in result.issues


def test_low_content_retention_warns() -> None:
    extracted = "A" * 1000
    cleaned = "A" * 300

    result = validate_text(extracted, cleaned)

    assert result.status == ValidationStatus.WARNING
    assert result.issues == ("LOW_CONTENT_RETENTION",)
    assert result.retention_ratio == pytest.approx(0.30)


def test_replacement_character_warns() -> None:
    extracted = "Lumine Reader processes documents reliably."
    cleaned = "Lumine Reader processes � documents reliably."

    result = validate_text(extracted, cleaned)

    assert result.status == ValidationStatus.WARNING
    assert "INVALID_REPLACEMENT_CHARACTER" in result.issues


def test_retention_ratio_can_exceed_one() -> None:
    extracted = "Short text."
    cleaned = "Short expanded text."

    result = validate_text(extracted, cleaned)

    assert result.retention_ratio > 1.0


def test_empty_extracted_text_does_not_divide_by_zero() -> None:
    result = validate_text("", "")

    assert result.retention_ratio == 0.0
    assert result.status == ValidationStatus.FAIL