from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
    TableElement,
)
from src.tts.render import (
    SpeechUnit,
    SpeechUnitType,
    render_document,
)


def test_render_document_preserves_reading_order():
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
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="End of chapter.",
            ),
        )
    )

    result = render_document(document)

    assert result == (
        SpeechUnit(
            type=SpeechUnitType.HEADING,
            text="CHAPTER 1",
            level=1,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="Accuracy was 98.7 percent.",
        ),
        SpeechUnit(
            type=SpeechUnitType.TABLE,
            text="Stage, Output. Extract: Structured document.",
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="End of chapter.",
        ),
    )


def test_render_document_skips_empty_speech():
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="https://example.com",
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="Useful content.",
            ),
        )
    )

    result = render_document(document)

    assert len(result) == 1
    assert result[0].text == "Useful content."


def test_numbered_heading_gets_natural_speech_pause():
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="1.1 Wrapped and Hyphenated Text",
                level=2,
            ),
        )
    )

    units = render_document(document)

    assert units[0].text == (
        "1.1. Wrapped and Hyphenated Text"
    )


def test_heading_preserves_complete_title_and_boundary():
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="LUMINE READER — STRUCTURED EXTRACTION TEST",
                level=1,
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="Repeated headers and standalone page numbers",
            ),
        )
    )

    units = render_document(document)

    assert units[0].text == (
        "LUMINE READER — STRUCTURED EXTRACTION TEST"
    )
    assert units[0].type == SpeechUnitType.HEADING

    assert units[1].text == (
        "Repeated headers and standalone page numbers"
    )
    assert units[1].type == SpeechUnitType.PARAGRAPH