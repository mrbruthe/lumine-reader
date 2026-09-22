from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.database.jobs import JobStatus
from src.pipelines.audiobook import AudiobookResult
from src.pipelines.job_runner import run_audiobook_job


@pytest.mark.asyncio
async def test_run_audiobook_job_marks_job_completed():
    connection = Mock()

    result = AudiobookResult(
        metadata=Mock(),
        output_path=Path("data/jobs/job-001/final.mp3"),
        chunk_paths=(Path("data/jobs/job-001/audio/chunk_0000.mp3"),),
    )

    with (
        patch(
            "src.pipelines.job_runner.build_audiobook",
            new=AsyncMock(return_value=result),
        ),
        patch("src.pipelines.job_runner.update_job_status") as update_status,
    ):
        returned = await run_audiobook_job(
            connection=connection,
            job_id="job-001",
            source_path="data/raw/book.pdf",
            output_dir="data/jobs/job-001",
        )

    assert returned == result

    assert update_status.call_count == 2

    assert update_status.call_args_list[0].kwargs == {
        "connection": connection,
        "job_id": "job-001",
        "status": JobStatus.PROCESSING,
    }

    assert update_status.call_args_list[1].kwargs == {
        "connection": connection,
        "job_id": "job-001",
        "status": JobStatus.COMPLETED,
        "output_path": "data/jobs/job-001/final.mp3",
    }


@pytest.mark.asyncio
async def test_run_audiobook_job_marks_job_failed():
    connection = Mock()

    with (
        patch(
            "src.pipelines.job_runner.build_audiobook",
            new=AsyncMock(side_effect=RuntimeError("TTS generation failed")),
        ),
        patch("src.pipelines.job_runner.update_job_status") as update_status,
    ):
        with pytest.raises(RuntimeError, match="TTS generation failed"):
            await run_audiobook_job(
                connection=connection,
                job_id="job-001",
                source_path="data/raw/book.pdf",
                output_dir="data/jobs/job-001",
            )

    assert update_status.call_count == 2

    assert update_status.call_args_list[0].kwargs == {
        "connection": connection,
        "job_id": "job-001",
        "status": JobStatus.PROCESSING,
    }

    assert update_status.call_args_list[1].kwargs == {
        "connection": connection,
        "job_id": "job-001",
        "status": JobStatus.FAILED,
        "error_message": "TTS generation failed",
    }

@pytest.mark.asyncio
async def test_run_audiobook_job_rejects_missing_job():
    connection = Mock()

    with (
        patch(
            "src.pipelines.job_runner.update_job_status",
            return_value=None,
        ),
        patch(
            "src.pipelines.job_runner.build_audiobook",
            new=AsyncMock(),
        ) as build_audiobook,
    ):
        with pytest.raises(ValueError, match="Job does not exist: missing-job"):
            await run_audiobook_job(
                connection=connection,
                job_id="missing-job",
                source_path="data/raw/book.pdf",
                output_dir="data/jobs/missing-job",
            )

    build_audiobook.assert_not_awaited()