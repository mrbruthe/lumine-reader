from dataclasses import dataclass
from pathlib import Path

from src.audio.assemble import assemble_audio
from src.pipelines.metadata import BookMetadata, extract_book_metadata
from src.pipelines.structured_extract import extract_structured_document
from src.tts.chunk import chunk_speech_units
from src.tts.generate import DEFAULT_VOICE, generate_audio_chunks
from src.tts.render import render_document


@dataclass(frozen=True)
class AudiobookResult:
    """Result of a completed audiobook pipeline run."""

    metadata: BookMetadata
    output_path: Path
    chunk_paths: tuple[Path, ...]


async def build_audiobook(
    source_path: str | Path,
    output_dir: str | Path,
    voice: str = DEFAULT_VOICE,
    explicit_title: str | None = None,
    explicit_author: str | None = None,
    max_chars: int = 3000,
) -> AudiobookResult:
    """Build an audiobook from a source document."""

    source_path = Path(source_path)
    output_dir = Path(output_dir)

    document = extract_structured_document(source_path)

    metadata = extract_book_metadata(
        document=document,
        source_filename=source_path.name,
        explicit_title=explicit_title,
        explicit_author=explicit_author,
    )

    speech_units = render_document(document)

    chunks = chunk_speech_units(
        speech_units,
        max_chars=max_chars,
    )

    if not chunks:
        raise ValueError("Document produced no speech chunks")

    chunk_dir = output_dir / "chunks"

    chunk_paths = await generate_audio_chunks(
        chunks=chunks,
        output_dir=chunk_dir,
        voice=voice,
    )

    final_path = output_dir / "final.mp3"

    assemble_audio(
        chunk_paths=chunk_paths,
        output_path=final_path,
    )

    return AudiobookResult(
        metadata=metadata,
        output_path=final_path,
        chunk_paths=chunk_paths,
    )