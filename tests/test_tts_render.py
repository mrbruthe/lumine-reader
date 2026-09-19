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
            text="Stage: Extract. Output: Structured document.",
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