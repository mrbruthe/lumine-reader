import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """Normalize Unicode into a consistent representation."""
    return unicodedata.normalize("NFKC", text)


def normalize_quotes(text: str) -> str:
    """Normalize common typographic quotes."""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }

    for original, replacement in replacements.items():
        text = text.replace(original, replacement)

    return text


def repair_hyphenated_words(text: str) -> str:
    """Repair words split across lines during extraction."""
    return re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)


def remove_page_numbers(text: str) -> str:
    """Remove standalone numeric page-number lines."""
    return re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)


def remove_html_tags(text: str) -> str:
    """Remove HTML tags while preserving textual content."""
    return re.sub(r"<[^>]+>", "", text)


def normalize_markdown(text: str) -> str:
    """Normalize Markdown syntax while preserving meaningful content."""

    # Remove heading markers but preserve heading text.
    text = re.sub(
        r"^\s*#{1,6}\s+",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Remove emphasis markers but preserve their content.
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)

    return text


def repair_line_breaks(text: str) -> str:
    """Join wrapped lines while preserving paragraph boundaries."""
    paragraphs = re.split(r"\n\s*\n", text)

    cleaned_paragraphs = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        paragraph = re.sub(r"\s*\n\s*", " ", paragraph)
        cleaned_paragraphs.append(paragraph)

    return "\n\n".join(cleaned_paragraphs)


def normalize_whitespace(text: str) -> str:
    """Normalize horizontal whitespace and paragraph spacing."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_text(text: str) -> str:
    """Create a canonical cleaned representation of extracted text."""
    text = normalize_unicode(text)
    text = normalize_quotes(text)
    text = repair_hyphenated_words(text)
    text = remove_page_numbers(text)
    text = remove_html_tags(text)
    text = normalize_markdown(text)
    text = repair_line_breaks(text)
    text = normalize_whitespace(text)

    return text