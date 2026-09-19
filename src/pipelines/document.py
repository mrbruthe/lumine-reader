from dataclasses import dataclass
from enum import Enum


class ElementType(str, Enum):
    """Semantic element types understood by Lumine."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    CAPTION = "caption"
    TABLE = "table"


@dataclass(frozen=True)
class DocumentElement:
    """A single semantic text element in a Lumine document."""

    type: ElementType
    text: str
    level: int | None = None


@dataclass(frozen=True)
class TableElement:
    """A structured table in a Lumine document."""

    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class StructuredDocument:
    """Lumine's canonical structured document representation."""

    elements: tuple[DocumentElement | TableElement, ...]