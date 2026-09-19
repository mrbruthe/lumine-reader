from pathlib import Path

import pytest

from src.pipelines.document import (
    ElementType,
    StructuredDocument,
    TableElement,
)
from src.pipelines.structured_extract import extract_structured_document


TEST_PDF = Path("data/raw/structured_extraction_test.pdf")


@pytest.mark.integration
def test_real_pdf_structured_extraction():
    document = extract_structured_document(TEST_PDF)

    assert isinstance(document, StructuredDocument)

    # Page footers should not survive extraction.
    text_elements = [
        element
        for element in document.elements
        if not isinstance(element, TableElement)
    ]

    assert not any(
        element.text in {"1", "2", "3", "4"}
        for element in text_elements
    )

    # Known heading should retain its semantic role.
    assert any(
        element.type == ElementType.HEADING
        and element.text == "CHAPTER 1"
        for element in text_elements
    )

    # Table should remain structured.
    tables = [
        element
        for element in document.elements
        if isinstance(element, TableElement)
    ]

    assert len(tables) == 1

    assert tables[0].rows[0] == (
        "Stage",
        "Input",
        "Output",
    )

    # Table should remain in reading order.
    table_index = document.elements.index(tables[0])

    assert document.elements[table_index - 1].text.startswith(
        "The following table"
    )

    assert document.elements[table_index + 1].text == (
        "Processing Throughput"
    )