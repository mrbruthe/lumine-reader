from src.tts.normalize import (
    normalize_currency,
    normalize_for_tts,
    normalize_percentages,
    normalize_symbols,
    remove_citation_markers,
    remove_urls,
)


def test_remove_urls():
    text = "Read more at https://example.com/article."

    result = remove_urls(text)

    assert "https://" not in result


def test_remove_citation_markers():
    text = "Revenue increased significantly [12]."

    result = remove_citation_markers(text)

    assert result == "Revenue increased significantly ."


def test_normalize_percentage():
    assert normalize_percentages("Accuracy was 98.7%.") == (
        "Accuracy was 98.7 percent."
    )


def test_normalize_symbols():
    assert normalize_symbols("R&D") == "R and D"


def test_normalize_simple_currency():
    assert normalize_currency("$50") == "50 dollars"
    assert normalize_currency("€30") == "30 euros"


def test_currency_with_scale_word():
    assert normalize_currency("£2.4 million") == (
        "2.4 million pounds"
    )


def test_normalize_for_tts():
    text = (
        "Revenue increased by 12.5% [12]. "
        "The project received £2.4 million. "
        "Read more at https://example.com/article."
    )

    result = normalize_for_tts(text)

    assert result == (
        "Revenue increased by 12.5 percent. "
        "The project received 2.4 million pounds. "
        "Read more at"
    )


def test_normalize_document_preserves_structure():
    from src.pipelines.document import (
        DocumentElement,
        ElementType,
        StructuredDocument,
        TableElement,
    )
    from src.tts.normalize import normalize_document_for_tts

    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="CHAPTER 1",
                level=1,
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="Accuracy was 98.7% [12].",
            ),
            TableElement(
                rows=(
                    ("Stage", "Output"),
                    ("Extract", "Structured document"),
                )
            ),
        )
    )

    result = normalize_document_for_tts(document)

    assert result.elements[0] == DocumentElement(
        type=ElementType.HEADING,
        text="CHAPTER 1",
        level=1,
    )

    assert result.elements[1] == DocumentElement(
        type=ElementType.PARAGRAPH,
        text="Accuracy was 98.7 percent.",
    )

    assert result.elements[2] == document.elements[2]


def test_narrate_table_uses_first_column_as_row_anchor():
    from src.pipelines.document import TableElement
    from src.tts.normalize import narrate_table

    table = TableElement(
        rows=(
            ("Stage", "Input", "Output"),
            ("Extract", "PDF / EPUB / DOCX", "Structured document"),
            ("Clean", "Extracted content", "Canonical content"),
            ("Validate", "Canonical content", "PASS / WARNING / FAIL"),
            ("TTS Normalize", "Canonical content", "Speech-ready text"),
        )
    )

    result = narrate_table(table)

    assert result == (
        "Stage, Input, Output. "
        "Extract: PDF / EPUB / DOCX; Structured document. "
        "Clean: Extracted content; Canonical content. "
        "Validate: Canonical content; PASS / WARNING / FAIL. "
        "TTS Normalize: Canonical content; Speech-ready text."
    )


def test_url_removal_removes_dangling_visit_phrase():
    text = (
        "Read the Lumine documentation or visit "
        "https://example.com/very/long/path?chapter=1. Revenue"
    )

    result = normalize_for_tts(text)

    assert result == (
        "Read the Lumine documentation. Revenue"
    )


def test_squared_expression_is_spoken_naturally():
    text = "x² + y² = z²."

    result = normalize_for_tts(text)

    assert result == (
        "x squared plus y squared equals z squared."
    )


def test_cubed_expression_is_spoken_naturally():
    text = "x³ + y³ = z³."

    result = normalize_for_tts(text)

    assert result == (
        "x cubed plus y cubed equals z cubed."
    )