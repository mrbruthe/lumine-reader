import re
from src.pipelines.document import (
    DocumentElement,
    StructuredDocument,
    TableElement,
)

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
CITATION_PATTERN = re.compile(r"\[\d+\]")


def remove_urls(text: str) -> str:
    """Remove raw URLs that should not be narrated."""

    return URL_PATTERN.sub("", text)


def remove_citation_markers(text: str) -> str:
    """Remove simple numeric citation markers."""

    return CITATION_PATTERN.sub("", text)


def normalize_symbols(text: str) -> str:
    """Normalize common written symbols for speech."""

    text = text.replace("R&D", "R and D")
    text = text.replace("&", " and ")

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
        # Scaled amounts: £2.4 million -> 2.4 million pounds
        text = re.sub(
            rf"{re.escape(symbol)}(\d+(?:\.\d+)?)\s+({scales})",
            rf"\1 \2 {currency}",
            text,
            flags=re.IGNORECASE,
        )

        # Simple amounts: $50 -> 50 dollars
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
    text = normalize_percentages(text)
    text = normalize_currency(text)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +([.,!?;:])", r"\1", text)

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
    """Convert a structured table into speech-ready text."""

    if not table.rows:
        return ""

    headers = table.rows[0]
    data_rows = table.rows[1:]

    narrated_rows: list[str] = []

    for row in data_rows:
        cells: list[str] = []

        for header, value in zip(headers, row):
            header_text = normalize_for_tts(header)
            value_text = normalize_for_tts(value)

            cells.append(f"{header_text}: {value_text}")

        narrated_rows.append(". ".join(cells) + ".")

    return " ".join(narrated_rows)