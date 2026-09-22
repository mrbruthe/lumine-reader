from pathlib import Path
from typing import Any

import psycopg

from src.database.job_repository import update_job_status
from src.database.jobs import JobStatus
from src.pipelines.audiobook import AudiobookResult, build_audiobook
from src.tts.generate import DEFAULT_VOICE


async def run_audiobook_job(
    connection: psycopg.Connection[Any],
    job_id: str,
    source_path: str | Path,
    output_dir: str | Path,
    voice: str = DEFAULT_VOICE,
    explicit_title: str | None = None,
    explicit_author: str | None = None,
    max_chars: int = 3000,
) -> AudiobookResult:
    """Run an audiobook build while tracking its job state."""

    job = update_job_status(
        connection=connection,
        job_id=job_id,
        status=JobStatus.PROCESSING,
    )

    if job is None:
        raise ValueError(f"Job does not exist: {job_id}")


    try:
        result = await build_audiobook(
            source_path=source_path,
            output_dir=output_dir,
            voice=voice,
            explicit_title=explicit_title,
            explicit_author=explicit_author,
            max_chars=max_chars,
        )
    except Exception as exc:
        update_job_status(
            connection=connection,
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message=str(exc),
        )
        raise

    update_job_status(
        connection=connection,
        job_id=job_id,
        status=JobStatus.COMPLETED,
        output_path=str(result.output_path),
    )

    return result