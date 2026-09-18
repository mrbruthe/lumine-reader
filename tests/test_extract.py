from pathlib import Path

import pytest

from src.pipelines.extract import extract_text, save_extracted_text


def test_extract_text(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("Lumine Reader", encoding="utf-8")

    result = extract_text(source)

    assert result == "Lumine Reader"


def test_missing_file_raises_error(tmp_path: Path) -> None:
    source = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        extract_text(source)


def test_unsupported_file_type_raises_error(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_text("sample", encoding="utf-8")

    with pytest.raises(ValueError):
        extract_text(source)


def test_save_extracted_text(tmp_path: Path) -> None:
    output = tmp_path / "extracted" / "sample.txt"

    result = save_extracted_text("Lumine Reader", output)

    assert result == output
    assert output.read_text(encoding="utf-8") == "Lumine Reader"