from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re

from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
)


class MetadataSource(str, Enum):
    """Source from which a metadata value was obtained."""

    EXPLICIT = "explicit"
    STRUCTURED = "structured"
    FILENAME = "filename"


@dataclass(frozen=True)
class BookMetadata:
    """Canonical metadata associated with a source document."""

    title: str
    author: str | None
    source_filename: str
    title_source: MetadataSource
    author_source: MetadataSource | None


def _find_structured_title(
    document: StructuredDocument,
) -> str | None:
    """Return the first non-empty heading as the document title."""

    for element in document.elements:
        if not isinstance(element, DocumentElement):
            continue

        if element.type != ElementType.HEADING:
            continue

        title = element.text.strip()

        if title:
            return title

    return None


def _find_structured_author(
    document: StructuredDocument,
) -> str | None:
    """Find an explicit 'By <author>' declaration near the front matter."""

    for element in document.elements[:10]:
        if not isinstance(element, DocumentElement):
            continue

        text = element.text.strip()

        match = re.fullmatch(
            r"by\s+(.+)",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            author = match.group(1).strip()

            if author:
                return author

    return None


def _title_from_filename(source_filename: str) -> str:
    """Use the filename stem as the final title fallback."""

    return Path(source_filename).stem


def extract_book_metadata(
    document: StructuredDocument,
    source_filename: str,
    explicit_title: str | None = None,
    explicit_author: str | None = None,
) -> BookMetadata:
    """Extract book metadata using deterministic fallback rules."""

    clean_explicit_title = (
        explicit_title.strip()
        if explicit_title and explicit_title.strip()
        else None
    )

    clean_explicit_author = (
        explicit_author.strip()
        if explicit_author and explicit_author.strip()
        else None
    )

    if clean_explicit_title:
        title = clean_explicit_title
        title_source = MetadataSource.EXPLICIT
    else:
        structured_title = _find_structured_title(document)

        if structured_title:
            title = structured_title
            title_source = MetadataSource.STRUCTURED
        else:
            title = _title_from_filename(source_filename)
            title_source = MetadataSource.FILENAME

    if clean_explicit_author:
        author = clean_explicit_author
        author_source = MetadataSource.EXPLICIT
    else:
        structured_author = _find_structured_author(document)

        if structured_author:
            author = structured_author
            author_source = MetadataSource.STRUCTURED
        else:
            author = None
            author_source = None

    return BookMetadata(
        title=title,
        author=author,
        source_filename=source_filename,
        title_source=title_source,
        author_source=author_source,
    )