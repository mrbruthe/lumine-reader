from pathlib import Path


def extract_text(file_path: str | Path) -> str:
    """Extract text from a supported document."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    if path.suffix.lower() != ".txt":
        raise ValueError(f"Unsupported file type: {path.suffix}")

    return path.read_text(encoding="utf-8")


def save_extracted_text(
    text: str,
    output_path: str | Path,
) -> Path:
    """Persist extracted text for downstream processing."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(text, encoding="utf-8")

    return path