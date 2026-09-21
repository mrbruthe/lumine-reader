import re

from src.pipelines.document import (
    DocumentElement,
    StructuredDocument,
    TableElement,
)


URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
CITATION_PATTERN = re.compile(r"\[\d+\]")


def remove_urls(text: str) -> str:
    """Remove URLs without leaving common dangling navigation phrases."""

    # Remove phrases such as:
    # "or visit https://example.com"
    # while preserving a natural sentence boundary.
    text = re.sub(
        r"\s+(?:or\s+)?visit\s+"
        r"(?:https?://\S+|www\.\S+)",
        ".",
        text,
        flags=re.IGNORECASE,
    )

    # Remove any remaining raw URLs.
    return URL_PATTERN.sub("", text)


def remove_citation_markers(text: str) -> str:
    """Remove simple numeric citation markers."""

    return CITATION_PATTERN.sub("", text)


def normalize_symbols(text: str) -> str:
    """Normalize common written symbols for speech."""

    text = text.replace("R&D", "R and D")
    text = text.replace("&", " and ")

    return text


def normalize_math(text: str) -> str:
    """Normalize common mathematical notation for natural speech."""

    # Superscript powers observed in real audiobook content.
    text = re.sub(
        r"([A-Za-z0-9])²",
        r"\1 squared",
        text,
    )

    text = re.sub(
        r"([A-Za-z0-9])³",
        r"\1 cubed",
        text,
    )

    # Common mathematical operators.
    text = re.sub(
        r"\s*\+\s*",
        " plus ",
        text,
    )

    text = re.sub(
        r"\s*=\s*",
        " equals ",
        text,
    )

    return text


def normalize_percentages(text: str) -> str:
    """Convert percentage symbols into spoken form."""

    return re.sub(
        r"(\d+(?:\.\d+)?)%",
        r"\1 percent",
        text,
    )


def normalize_currency(text: str) -> str:
    """Convert common currency expressions into spoken form."""

    currencies = {
        "£": "pounds",
        "$": "dollars",
        "€": "euros",
    }

    scales = r"(?:thousand|million|billion|trillion)"

    for symbol, currency in currencies.items():
        # Scaled amounts:
        # £2.4 million -> 2.4 million pounds
        text = re.sub(
            rf"{re.escape(symbol)}(\d+(?:\.\d+)?)\s+({scales})",
            rf"\1 \2 {currency}",
            text,
            flags=re.IGNORECASE,
        )

        # Simple amounts:
        # $50 -> 50 dollars
        text = re.sub(
            rf"{re.escape(symbol)}(\d+(?:\.\d+)?)",
            rf"\1 {currency}",
            text,
        )

    return text


def normalize_for_tts(text: str) -> str:
    """Convert canonical text into speech-ready text."""

    text = remove_urls(text)
    text = remove_citation_markers(text)
    text = normalize_symbols(text)
    text = normalize_math(text)
    text = normalize_percentages(text)
    text = normalize_currency(text)

    # Clean whitespace introduced by normalization.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces immediately before punctuation.
    text = re.sub(
        r" +([.,!?;:])",
        r"\1",
        text,
    )

    return text.strip()


def normalize_document_for_tts(
    document: StructuredDocument,
) -> StructuredDocument:
    """Normalize document content for speech while preserving structure."""

    elements: list[DocumentElement | TableElement] = []

    for element in document.elements:
        if isinstance(element, TableElement):
            elements.append(element)
            continue

        elements.append(
            DocumentElement(
                type=element.type,
                text=normalize_for_tts(element.text),
                level=element.level,
            )
        )

    return StructuredDocument(elements=tuple(elements))

def narrate_table(table: TableElement) -> str:
    """Convert a structured table into compact speech-ready text."""

    if not table.rows:
        return ""

    headers = tuple(
        normalize_for_tts(header)
        for header in table.rows[0]
    )

    data_rows = table.rows[1:]

    if not headers:
        return ""

    # Announce the table structure once.
    header_intro = ", ".join(headers) + "."

    narrated_rows: list[str] = []

    for row in data_rows:
        values = tuple(
            normalize_for_tts(value)
            for value in row
        )

        if not values:
            continue

        # The first column identifies the row.
        anchor = values[0]

        # Remaining columns provide the row's details.
        details = [
            value
            for value in values[1:]
            if value
        ]

        if anchor and details:
            narrated_rows.append(
                f"{anchor}: {'; '.join(details)}."
            )
        elif anchor:
            narrated_rows.append(
                f"{anchor}."
            )
        elif details:
            narrated_rows.append(
                f"{'; '.join(details)}."
            )

    if not narrated_rows:
        return header_intro

    return f"{header_intro} {' '.join(narrated_rows)}"