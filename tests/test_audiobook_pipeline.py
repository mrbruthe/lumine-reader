from pathlib import Path

import pytest

from src.pipelines.document import (
    DocumentElement,
    ElementType,
    StructuredDocument,
)
from src.pipelines.metadata import BookMetadata, MetadataSource
from src.tts.chunk import SpeechChunk
from src.tts.render import SpeechUnit, SpeechUnitType


@pytest.mark.anyio
async def test_build_audiobook_runs_pipeline_in_order(
    tmp_path,
    monkeypatch,
):
    from src.pipelines import audiobook

    source_path = tmp_path / "book.pdf"
    source_path.write_bytes(b"fake pdf")

    output_dir = tmp_path / "output"

    document = StructuredDocument(
        elements=(
            DocumentElement(
                type=ElementType.HEADING,
                text="Test Book",
                level=1,
            ),
            DocumentElement(
                type=ElementType.PARAGRAPH,
                text="This is the book.",
            ),
        )
    )

    metadata = BookMetadata(
        title="Test Book",
        author=None,
        source_filename="book.pdf",
        title_source=MetadataSource.STRUCTURED,
        author_source=None,
    )

    speech_units = (
        SpeechUnit(
            type=SpeechUnitType.HEADING,
            text="Test Book",
            level=1,
        ),
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="This is the book.",
        ),
    )

    chunks = (
        SpeechChunk(
            index=0,
            units=speech_units,
            text="Test Book\n\nThis is the book.",
        ),
    )

    chunk_paths = (
        output_dir / "chunks" / "0000.mp3",
    )

    events = []

    def fake_extract(path):
        events.append("extract")
        assert path == source_path
        return document

    def fake_metadata(**kwargs):
        events.append("metadata")
        assert kwargs["document"] == document
        assert kwargs["source_filename"] == "book.pdf"
        return metadata

    def fake_render(received_document):
        events.append("render")
        assert received_document == document
        return speech_units

    def fake_chunk(received_units, max_chars):
        events.append("chunk")
        assert received_units == speech_units
        assert max_chars == 3000
        return chunks

    async def fake_generate(**kwargs):
        events.append("generate")
        assert kwargs["chunks"] == chunks
        assert kwargs["output_dir"] == output_dir / "chunks"
        return chunk_paths

    def fake_assemble(**kwargs):
        events.append("assemble")
        assert kwargs["chunk_paths"] == chunk_paths

        final_path = kwargs["output_path"]
        final_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        final_path.write_bytes(b"final audio")

        return final_path

    monkeypatch.setattr(
        audiobook,
        "extract_structured_document",
        fake_extract,
    )
    monkeypatch.setattr(
        audiobook,
        "extract_book_metadata",
        fake_metadata,
    )
    monkeypatch.setattr(
        audiobook,
        "render_document",
        fake_render,
    )
    monkeypatch.setattr(
        audiobook,
        "chunk_speech_units",
        fake_chunk,
    )
    monkeypatch.setattr(
        audiobook,
        "generate_audio_chunks",
        fake_generate,
    )
    monkeypatch.setattr(
        audiobook,
        "assemble_audio",
        fake_assemble,
    )

    result = await audiobook.build_audiobook(
        source_path=source_path,
        output_dir=output_dir,
    )

    assert events == [
        "extract",
        "metadata",
        "render",
        "chunk",
        "generate",
        "assemble",
    ]

    assert result.metadata == metadata
    assert result.chunk_paths == chunk_paths
    assert result.output_path == output_dir / "final.mp3"


@pytest.mark.anyio
async def test_build_audiobook_passes_user_options(
    tmp_path,
    monkeypatch,
):
    from src.pipelines import audiobook

    source_path = tmp_path / "book.pdf"
    source_path.write_bytes(b"fake pdf")

    output_dir = tmp_path / "output"

    document = StructuredDocument(elements=())

    metadata = BookMetadata(
        title="Explicit Title",
        author="Explicit Author",
        source_filename="book.pdf",
        title_source=MetadataSource.EXPLICIT,
        author_source=MetadataSource.EXPLICIT,
    )

    speech_units = (
        SpeechUnit(
            type=SpeechUnitType.PARAGRAPH,
            text="Hello.",
        ),
    )

    chunks = (
        SpeechChunk(
            index=0,
            units=speech_units,
            text="Hello.",
        ),
    )

    observed = {}

    monkeypatch.setattr(
        audiobook,
        "extract_structured_document",
        lambda path: document,
    )

    def fake_metadata(**kwargs):
        observed["title"] = kwargs["explicit_title"]
        observed["author"] = kwargs["explicit_author"]
        return metadata

    monkeypatch.setattr(
        audiobook,
        "extract_book_metadata",
        fake_metadata,
    )

    monkeypatch.setattr(
        audiobook,
        "render_document",
        lambda document: speech_units,
    )

    def fake_chunk(units, max_chars):
        observed["max_chars"] = max_chars
        return chunks

    monkeypatch.setattr(
        audiobook,
        "chunk_speech_units",
        fake_chunk,
    )

    async def fake_generate(**kwargs):
        observed["voice"] = kwargs["voice"]

        chunk_path = (
            kwargs["output_dir"] / "0000.mp3"
        )

        return (chunk_path,)

    monkeypatch.setattr(
        audiobook,
        "generate_audio_chunks",
        fake_generate,
    )

    monkeypatch.setattr(
        audiobook,
        "assemble_audio",
        lambda **kwargs: kwargs["output_path"],
    )

    await audiobook.build_audiobook(
        source_path=source_path,
        output_dir=output_dir,
        voice="test-voice",
        explicit_title="Explicit Title",
        explicit_author="Explicit Author",
        max_chars=1500,
    )

    assert observed == {
        "title": "Explicit Title",
        "author": "Explicit Author",
        "max_chars": 1500,
        "voice": "test-voice",
    }


@pytest.mark.anyio
async def test_build_audiobook_rejects_document_with_no_speech(
    tmp_path,
    monkeypatch,
):
    from src.pipelines import audiobook

    source_path = tmp_path / "empty.pdf"
    source_path.write_bytes(b"fake pdf")

    document = StructuredDocument(elements=())

    metadata = BookMetadata(
        title="Empty",
        author=None,
        source_filename="empty.pdf",
        title_source=MetadataSource.FILENAME,
        author_source=None,
    )

    monkeypatch.setattr(
        audiobook,
        "extract_structured_document",
        lambda path: document,
    )

    monkeypatch.setattr(
        audiobook,
        "extract_book_metadata",
        lambda **kwargs: metadata,
    )

    monkeypatch.setattr(
        audiobook,
        "render_document",
        lambda document: (),
    )

    monkeypatch.setattr(
        audiobook,
        "chunk_speech_units",
        lambda units, max_chars: (),
    )

    with pytest.raises(
        ValueError,
        match="Document produced no speech chunks",
    ):
        await audiobook.build_audiobook(
            source_path=source_path,
            output_dir=tmp_path / "output",
        )