from pathlib import Path
from types import SimpleNamespace

import pytest

from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
    TableElement,
)
from src.pipelines.structured_extract import (
    _convert_document,
    extract_structured_document,
)


class FakeDocument:
    """Minimal Docling-like document for conversion tests."""

    def __init__(self, items):
        self.items = items

    def iterate_items(self):
        for item in self.items:
            yield item, 0


def make_item(label, text, level=None):
    return SimpleNamespace(
        label=label,
        text=text,
        level=level,
    )


def test_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        extract_structured_document("missing.pdf")


def test_convert_document_returns_structured_document():
    from docling_core.types.doc import DocItemLabel

    document = FakeDocument([
        make_item(
            DocItemLabel.TEXT,
            "Lumine processes documents.",
        )
    ])

    result = _convert_document(document)

    assert isinstance(result, StructuredDocument)


def test_heading_is_preserved():
    from docling_core.types.doc import DocItemLabel

    document = FakeDocument([
        make_item(
            DocItemLabel.SECTION_HEADER,
            "CHAPTER 1",
            level=1,
        )
    ])

    result = _convert_document(document)

    assert result.elements == (
        DocumentElement(
            type=ElementType.HEADING,
            text="CHAPTER 1",
            level=1,
        ),
    )


def test_paragraph_is_preserved():
    from docling_core.types.doc import DocItemLabel

    document = FakeDocument([
        make_item(
            DocItemLabel.TEXT,
            "A useful paragraph.",
        )
    ])

    result = _convert_document(document)

    assert result.elements == (
        DocumentElement(
            type=ElementType.PARAGRAPH,
            text="A useful paragraph.",
        ),
    )


def test_page_footer_is_excluded():
    from docling_core.types.doc import DocItemLabel

    document = FakeDocument([
        make_item(DocItemLabel.PAGE_FOOTER, "42"),
        make_item(DocItemLabel.TEXT, "Useful content."),
    ])

    result = _convert_document(document)

    assert len(result.elements) == 1
    assert result.elements[0].text == "Useful content."

def test_table_is_converted_to_rows():
    from types import SimpleNamespace

    from src.pipelines.structured_extract import _convert_table

    cells = [
        SimpleNamespace(
            text="Stage",
            start_row_offset_idx=0,
            end_row_offset_idx=1,
            start_col_offset_idx=0,
            end_col_offset_idx=1,
        ),
        SimpleNamespace(
            text="Output",
            start_row_offset_idx=0,
            end_row_offset_idx=1,
            start_col_offset_idx=1,
            end_col_offset_idx=2,
        ),
        SimpleNamespace(
            text="Extract",
            start_row_offset_idx=1,
            end_row_offset_idx=2,
            start_col_offset_idx=0,
            end_col_offset_idx=1,
        ),
        SimpleNamespace(
            text="Structured document",
            start_row_offset_idx=1,
            end_row_offset_idx=2,
            start_col_offset_idx=1,
            end_col_offset_idx=2,
        ),
    ]

    table = SimpleNamespace(
        data=SimpleNamespace(
            num_rows=2,
            num_cols=2,
            table_cells=cells,
        )
    )

    result = _convert_table(table)

    assert result.rows == (
        ("Stage", "Output"),
        ("Extract", "Structured document"),
    )