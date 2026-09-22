from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JobPaths:
    """Filesystem paths for one audiobook processing job."""

    root: Path
    structured_document: Path
    speech_units: Path
    speech_chunks: Path
    audio_dir: Path
    final_audio: Path


def get_job_paths(
    job_id: str,
    base_dir: str | Path = "data/jobs",
) -> JobPaths:
    """Return deterministic artifact paths for a processing job."""
    root = Path(base_dir) / job_id

    return JobPaths(
        root=root,
        structured_document=root / "structured_document.json",
        speech_units=root / "speech_units.json",
        speech_chunks=root / "chunks.json",
        audio_dir=root / "audio",
        final_audio=root / "final.mp3",
    )