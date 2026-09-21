import os
from collections.abc import Awaitable, Callable
from pathlib import Path

import edge_tts

from src.tts.chunk import SpeechChunk


MALE_VOICE = "en-US-ChristopherNeural"
FEMALE_VOICE = "en-US-EmmaNeural"
DEFAULT_VOICE = MALE_VOICE

Synthesizer = Callable[[str, str, Path], Awaitable[None]]


async def _edge_synthesizer(
    text: str,
    voice: str,
    output_path: Path,
) -> None:
    """Generate speech audio using Edge TTS."""

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
    )

    await communicate.save(str(output_path))


def chunk_filename(chunk: SpeechChunk) -> str:
    """Return the deterministic filename for a speech chunk."""

    return f"{chunk.index:04d}.mp3"


async def generate_audio_chunk(
    chunk: SpeechChunk,
    output_dir: str | Path,
    voice: str = DEFAULT_VOICE,
    synthesizer: Synthesizer = _edge_synthesizer,
) -> Path:
    """Generate one speech chunk safely and return its final path."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    final_path = output_dir / chunk_filename(chunk)

    # A non-empty final file represents completed work.
    # This allows retries to skip chunks already generated.
    if final_path.exists() and final_path.stat().st_size > 0:
        return final_path

    temp_path = final_path.with_suffix(".mp3.part")

    # Remove any incomplete output left by an interrupted run.
    temp_path.unlink(missing_ok=True)

    try:
        await synthesizer(
            chunk.text,
            voice,
            temp_path,
        )

        if not temp_path.exists():
            raise RuntimeError(
                f"TTS generation produced no file for chunk {chunk.index}"
            )

        if temp_path.stat().st_size == 0:
            raise RuntimeError(
                f"TTS generation produced an empty file for chunk {chunk.index}"
            )

        # Only expose the final filename after generation succeeds.
        os.replace(temp_path, final_path)

    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return final_path

async def generate_audio_chunks(
    chunks: tuple[SpeechChunk, ...],
    output_dir: str | Path,
    voice: str = DEFAULT_VOICE,
    synthesizer: Synthesizer = _edge_synthesizer,
) -> tuple[Path, ...]:
    """Generate speech chunks in order and return their audio paths."""

    paths: list[Path] = []

    for chunk in chunks:
        path = await generate_audio_chunk(
            chunk=chunk,
            output_dir=output_dir,
            voice=voice,
            synthesizer=synthesizer,
        )

        paths.append(path)

    return tuple(paths)