from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
)
from src.storage.artifacts import (
    load_speech_chunks,
    load_speech_units,
    load_structured_document,
    save_speech_chunks,
    save_speech_units,
    save_structured_document,
)
from src.tts.chunk import SpeechChunk
from src.tts.render import SpeechUnit, SpeechUnitType


def test_structured_document_round_trip(tmp_path):
    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="Chapter One",
                level=1,
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="This is the opening paragraph.",
            ),
        )
    )

    artifact_path = tmp_path / "structured_document.json"

    save_structured_document(document, artifact_path)

    restored = load_structured_document(artifact_path)

    assert artifact_path.exists()
    assert restored == document


def test_speech_units_round_trip(tmp_path):
    units = (
        SpeechUnit(
            type=SpeechUnitType.HEADING,
            text="Chapter One.",
            level=1,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="This is the opening paragraph.",
        ),
    )

    artifact_path = tmp_path / "speech_units.json"

    save_speech_units(units, artifact_path)

    restored = load_speech_units(artifact_path)

    assert artifact_path.exists()
    assert restored == units


def test_speech_chunks_round_trip(tmp_path):
    units = (
        SpeechUnit(
            type=SpeechUnitType.HEADING,
            text="Chapter One.",
            level=1,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="This is the opening paragraph.",
        ),
    )

    chunks = (
        SpeechChunk(
            index=0,
            units=units,
            text="Chapter One.\n\nThis is the opening paragraph.",
        ),
    )

    artifact_path = tmp_path / "chunks.json"

    save_speech_chunks(chunks, artifact_path)

    restored = load_speech_chunks(artifact_path)

    assert artifact_path.exists()
    assert restored == chunks