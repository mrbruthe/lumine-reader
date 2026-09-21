import pytest

from src.tts.chunk import (
    chunk_speech_units,
    split_by_words,
    split_oversized_text,
)
from src.tts.render import SpeechUnit, SpeechUnitType


def test_chunking_preserves_unit_order():
    units = (
        SpeechUnit(
            type=SpeechUnitType.HEADING,
            text="CHAPTER 1",
            level=1,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="First paragraph.",
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="Second paragraph.",
        ),
    )

    result = chunk_speech_units(
        units,
        max_chars=100,
    )

    assert len(result) == 1
    assert result[0].units == units


def test_chunking_respects_semantic_boundaries():
    units = (
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="A" * 40,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="B" * 40,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="C" * 40,
        ),
    )

    result = chunk_speech_units(
        units,
        max_chars=85,
    )

    assert len(result) == 2
    assert result[0].units == units[:2]
    assert result[1].units == units[2:]


def test_chunk_indices_are_sequential():
    units = (
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="A" * 50,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="B" * 50,
        ),
    )

    result = chunk_speech_units(
        units,
        max_chars=50,
    )

    assert result[0].index == 0
    assert result[1].index == 1


def test_invalid_max_chars_raises_error():
    with pytest.raises(
        ValueError,
        match="max_chars must be greater than zero",
    ):
        chunk_speech_units(
            (),
            max_chars=0,
        )


def test_oversized_unit_splits_at_sentence_boundary():
    unit = SpeechUnit(
        type=SpeechUnitType.PARAGRAPH,
        text=(
            "First sentence. "
            "Second sentence. "
            "Third sentence."
        ),
    )

    result = chunk_speech_units(
        (unit,),
        max_chars=32,
    )

    assert len(result) == 2

    assert result[0].text == (
        "First sentence. Second sentence."
    )

    assert result[1].text == "Third sentence."


def test_oversized_sentence_splits_at_word_boundary():
    unit = SpeechUnit(
        type=SpeechUnitType.PARAGRAPH,
        text="alpha beta gamma delta epsilon",
    )

    result = chunk_speech_units(
        (unit,),
        max_chars=16,
    )

    assert all(
        len(chunk.text) <= 16
        for chunk in result
    )

    reconstructed = " ".join(
        chunk.text
        for chunk in result
    )

    assert reconstructed == unit.text


def test_no_chunk_exceeds_max_chars():
    units = (
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="A normal paragraph.",
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="word " * 100,
        ),
    )

    result = chunk_speech_units(
        units,
        max_chars=50,
    )

    assert all(
        len(chunk.text) <= 50
        for chunk in result
    )


def test_hard_split_handles_single_oversized_token():
    text = "A" * 25

    result = split_by_words(
        text,
        max_chars=10,
    )

    assert result == (
        "A" * 10,
        "A" * 10,
        "A" * 5,
    )


def test_split_oversized_text_preserves_content():
    text = (
        "This is sentence one. "
        "This is sentence two. "
        "This is sentence three."
    )

    result = split_oversized_text(
        text,
        max_chars=30,
    )

    assert " ".join(result) == text

    assert all(
        len(part) <= 30
        for part in result
    )

def test_heading_boundary_adds_spoken_pause():
    units = (
        SpeechUnit(
            type=SpeechUnitType.HEADING,
            text="LUMINE READER — STRUCTURED EXTRACTION TEST",
            level=1,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="Repeated headers and standalone page numbers",
        ),
    )

    result = chunk_speech_units(
        units,
        max_chars=200,
    )

    assert len(result) == 1

    assert result[0].text == (
        "LUMINE READER — STRUCTURED EXTRACTION TEST.\n\n"
        "Repeated headers and standalone page numbers"
    )