from dataclasses import dataclass
from enum import Enum


# MVP heuristic. Calibrate using observed document-processing metrics.
MIN_RETENTION_RATIO = 0.50


class ValidationStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    issues: tuple[str, ...]
    extracted_chars: int
    cleaned_chars: int
    retention_ratio: float


def validate_text(
    extracted_text: str,
    cleaned_text: str,
) -> ValidationResult:
    """Validate cleaned text before downstream processing."""

    issues: list[str] = []

    extracted_chars = len(extracted_text)
    cleaned_chars = len(cleaned_text)

    retention_ratio = (
        cleaned_chars / extracted_chars
        if extracted_chars > 0
        else 0.0
    )

    # Fatal: cleaning produced no usable text.
    if not cleaned_text.strip():
        issues.append("EMPTY_CLEANED_TEXT")

    # Fatal: content exists but contains no meaningful alphanumeric data.
    if not any(char.isalnum() for char in cleaned_text):
        issues.append("NO_MEANINGFUL_CONTENT")

    # Warning: cleaning retained an unusually small proportion of the source.
    if (
        extracted_chars > 0
        and cleaned_chars > 0
        and retention_ratio < MIN_RETENTION_RATIO
    ):
        issues.append("LOW_CONTENT_RETENTION")

    # Warning: Unicode replacement characters may indicate decoding corruption.
    if "\ufffd" in cleaned_text:
        issues.append("INVALID_REPLACEMENT_CHARACTER")

    fail_issues = {
        "EMPTY_CLEANED_TEXT",
        "NO_MEANINGFUL_CONTENT",
    }

    if any(issue in fail_issues for issue in issues):
        status = ValidationStatus.FAIL
    elif issues:
        status = ValidationStatus.WARNING
    else:
        status = ValidationStatus.PASS

    return ValidationResult(
        status=status,
        issues=tuple(issues),
        extracted_chars=extracted_chars,
        cleaned_chars=cleaned_chars,
        retention_ratio=retention_ratio,
    )