from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import (
    DocItemLabel,
    DoclingDocument,
    TableItem,
)

from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
    TableElement,
)


def _convert_table(table: TableItem) -> TableElement:
    """Convert a Docling table into Lumine's table representation."""

    data = table.data

    rows = [
        [""] * data.num_cols
        for _ in range(data.num_rows)
    ]

    for cell in data.table_cells:
        for row in range(
            cell.start_row_offset_idx,
            cell.end_row_offset_idx,
        ):
            for col in range(
                cell.start_col_offset_idx,
                cell.end_col_offset_idx,
            ):
                rows[row][col] = cell.text

    return TableElement(
        rows=tuple(tuple(row) for row in rows)
    )


def _convert_document(
    document: DoclingDocument,
) -> StructuredDocument:
    """Convert a Docling document into Lumine's representation."""

    elements: list[DocumentElement | TableElement] = []

    for item, _level in document.iterate_items():
        label = getattr(item, "label", None)
        text = getattr(item, "text", None)

        if label in {
            DocItemLabel.PAGE_HEADER,
            DocItemLabel.PAGE_FOOTER,
        }:
            continue

        if isinstance(item, TableItem):
            elements.append(_convert_table(item))
            continue

        if label == DocItemLabel.SECTION_HEADER and text:
            elements.append(
                DocumentElement(
                    type=ElementType.HEADING,
                    text=text,
                    level=getattr(item, "level", None),
                )
            )
            continue

        if label == DocItemLabel.LIST_ITEM and text:
            elements.append(
                DocumentElement(
                    type=ElementType.LIST_ITEM,
                    text=text,
                )
            )
            continue

        if label == DocItemLabel.CAPTION and text:
            elements.append(
                DocumentElement(
                    type=ElementType.CAPTION,
                    text=text,
                )
            )
            continue

        if label == DocItemLabel.TEXT and text:
            elements.append(
                DocumentElement(
                    type=ElementType.PARAGRAPH,
                    text=text,
                )
            )

    return StructuredDocument(elements=tuple(elements))


def extract_structured_document(
    file_path: str | Path,
) -> StructuredDocument:
    """Extract a document into Lumine's structured representation."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    result = DocumentConverter().convert(path)

    return _convert_document(result.document)