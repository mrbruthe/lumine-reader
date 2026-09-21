from pathlib import Path

import pytest

from src.tts.chunk import SpeechChunk
from src.tts.generate import (
    DEFAULT_VOICE,
    FEMALE_VOICE,
    MALE_VOICE,
    chunk_filename,
    generate_audio_chunk,
    generate_audio_chunks,
)
from src.tts.render import SpeechUnit, SpeechUnitType


def make_chunk(
    index: int = 0,
    text: str = "Hello from Lumine.",
) -> SpeechChunk:
    unit = SpeechUnit(
        type=SpeechUnitType.PARAGRAPH,
        text=text,
    )

    return SpeechChunk(
        index=index,
        units=(unit,),
        text=text,
    )


def test_default_voice_is_christopher():
    assert MALE_VOICE == "en-US-ChristopherNeural"
    assert DEFAULT_VOICE == MALE_VOICE


def test_female_voice_is_emma():
    assert FEMALE_VOICE == "en-US-EmmaNeural"


def test_chunk_filename_is_deterministic():
    chunk = make_chunk(index=7)

    assert chunk_filename(chunk) == "0007.mp3"


@pytest.mark.anyio
async def test_generate_audio_chunk_creates_audio_file(
    tmp_path: Path,
):
    chunk = make_chunk()

    async def fake_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        assert text == "Hello from Lumine."
        assert voice == MALE_VOICE

        output_path.write_bytes(b"fake-mp3-data")

    result = await generate_audio_chunk(
        chunk=chunk,
        output_dir=tmp_path,
        synthesizer=fake_synthesizer,
    )

    assert result == tmp_path / "0000.mp3"
    assert result.read_bytes() == b"fake-mp3-data"

    assert not (
        tmp_path / "0000.mp3.part"
    ).exists()


@pytest.mark.anyio
async def test_selected_female_voice_is_passed_to_synthesizer(
    tmp_path: Path,
):
    chunk = make_chunk()

    received_voice = None

    async def fake_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        nonlocal received_voice

        received_voice = voice
        output_path.write_bytes(b"fake-mp3-data")

    await generate_audio_chunk(
        chunk=chunk,
        output_dir=tmp_path,
        voice=FEMALE_VOICE,
        synthesizer=fake_synthesizer,
    )

    assert received_voice == FEMALE_VOICE


@pytest.mark.anyio
async def test_existing_completed_chunk_is_skipped(
    tmp_path: Path,
):
    chunk = make_chunk(index=3)

    existing = tmp_path / "0003.mp3"
    existing.write_bytes(b"existing-audio")

    called = False

    async def fake_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        nonlocal called
        called = True

    result = await generate_audio_chunk(
        chunk=chunk,
        output_dir=tmp_path,
        synthesizer=fake_synthesizer,
    )

    assert result == existing
    assert result.read_bytes() == b"existing-audio"
    assert called is False


@pytest.mark.anyio
async def test_stale_partial_file_is_replaced(
    tmp_path: Path,
):
    chunk = make_chunk(index=1)

    partial = tmp_path / "0001.mp3.part"
    partial.write_bytes(b"broken-partial-data")

    async def fake_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        output_path.write_bytes(b"complete-audio")

    result = await generate_audio_chunk(
        chunk=chunk,
        output_dir=tmp_path,
        synthesizer=fake_synthesizer,
    )

    assert result.read_bytes() == b"complete-audio"
    assert not partial.exists()


@pytest.mark.anyio
async def test_failed_generation_removes_partial_file(
    tmp_path: Path,
):
    chunk = make_chunk(index=2)

    async def failing_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        output_path.write_bytes(b"partial-audio")

        raise RuntimeError("TTS failed")

    with pytest.raises(
        RuntimeError,
        match="TTS failed",
    ):
        await generate_audio_chunk(
            chunk=chunk,
            output_dir=tmp_path,
            synthesizer=failing_synthesizer,
        )

    assert not (
        tmp_path / "0002.mp3"
    ).exists()

    assert not (
        tmp_path / "0002.mp3.part"
    ).exists()


@pytest.mark.anyio
async def test_empty_generated_file_is_rejected(
    tmp_path: Path,
):
    chunk = make_chunk(index=4)

    async def empty_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        output_path.touch()

    with pytest.raises(
        RuntimeError,
        match="empty file",
    ):
        await generate_audio_chunk(
            chunk=chunk,
            output_dir=tmp_path,
            synthesizer=empty_synthesizer,
        )

    assert not (
        tmp_path / "0004.mp3"
    ).exists()

    assert not (
        tmp_path / "0004.mp3.part"
    ).exists()

@pytest.mark.anyio
async def test_generate_audio_chunks_preserves_order(
    tmp_path: Path,
):
    chunks = (
        make_chunk(index=0, text="First chunk."),
        make_chunk(index=1, text="Second chunk."),
        make_chunk(index=2, text="Third chunk."),
    )

    generated_texts = []

    async def fake_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        generated_texts.append(text)
        output_path.write_bytes(
            f"audio:{text}".encode()
        )

    paths = await generate_audio_chunks(
        chunks=chunks,
        output_dir=tmp_path,
        synthesizer=fake_synthesizer,
    )

    assert paths == (
        tmp_path / "0000.mp3",
        tmp_path / "0001.mp3",
        tmp_path / "0002.mp3",
    )

    assert generated_texts == [
        "First chunk.",
        "Second chunk.",
        "Third chunk.",
    ]


@pytest.mark.anyio
async def test_generate_audio_chunks_resumes_completed_work(
    tmp_path: Path,
):
    chunks = (
        make_chunk(index=0, text="Already complete."),
        make_chunk(index=1, text="Generate this."),
        make_chunk(index=2, text="Generate this too."),
    )

    completed = tmp_path / "0000.mp3"
    completed.write_bytes(b"existing-audio")

    generated_texts = []

    async def fake_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        generated_texts.append(text)
        output_path.write_bytes(
            f"audio:{text}".encode()
        )

    paths = await generate_audio_chunks(
        chunks=chunks,
        output_dir=tmp_path,
        synthesizer=fake_synthesizer,
    )

    assert paths == (
        tmp_path / "0000.mp3",
        tmp_path / "0001.mp3",
        tmp_path / "0002.mp3",
    )

    assert generated_texts == [
        "Generate this.",
        "Generate this too.",
    ]

    assert completed.read_bytes() == b"existing-audio"


@pytest.mark.anyio
async def test_generate_audio_chunks_stops_on_failure(
    tmp_path: Path,
):
    chunks = (
        make_chunk(index=0, text="First chunk."),
        make_chunk(index=1, text="Fail here."),
        make_chunk(index=2, text="Should not run."),
    )

    generated_texts = []

    async def fake_synthesizer(
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        generated_texts.append(text)

        if text == "Fail here.":
            raise RuntimeError("TTS failed")

        output_path.write_bytes(b"audio")

    with pytest.raises(
        RuntimeError,
        match="TTS failed",
    ):
        await generate_audio_chunks(
            chunks=chunks,
            output_dir=tmp_path,
            synthesizer=fake_synthesizer,
        )

    assert generated_texts == [
        "First chunk.",
        "Fail here.",
    ]

    assert (tmp_path / "0000.mp3").exists()
    assert not (tmp_path / "0001.mp3").exists()
    assert not (tmp_path / "0002.mp3").exists()