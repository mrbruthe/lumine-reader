from pathlib import Path
from unittest.mock import AsyncMock, Mock, call, patch

import pytest

from src.database.jobs import Job, JobStatus
from src.pipelines.audiobook import AudiobookResult
from src.pipelines.job_runner import run_audiobook_job


@pytest.mark.asyncio
async def test_run_audiobook_job_completes():
    connection = Mock()

    processing_job = Mock(spec=Job)

    result = AudiobookResult(
        metadata=Mock(),
        output_path=Path("data/jobs/job-001/final.mp3"),
        chunk_paths=(),
    )

    with (
        patch(
            "src.pipelines.job_runner.update_job_status",
            side_effect=[processing_job, Mock(spec=Job)],
        ) as update_status,
        patch(
            "src.pipelines.job_runner.create_processing_event"
        ) as create_event,
        patch(
            "src.pipelines.job_runner.build_audiobook",
            new_callable=AsyncMock,
            return_value=result,
        ) as build,
    ):
        returned = await run_audiobook_job(
            connection=connection,
            job_id="job-001",
            source_path="data/raw/book.pdf",
            output_dir="data/jobs/job-001",
        )

    assert returned == result

    build.assert_awaited_once()

    assert update_status.call_args_list == [
        call(
            connection=connection,
            job_id="job-001",
            status=JobStatus.PROCESSING,
        ),
        call(
            connection=connection,
            job_id="job-001",
            status=JobStatus.COMPLETED,
            output_path="data/jobs/job-001/final.mp3",
        ),
    ]

    assert create_event.call_args_list == [
        call(
            connection=connection,
            job_id="job-001",
            event_type="processing_started",
            message="Audiobook processing started",
        ),
        call(
            connection=connection,
            job_id="job-001",
            event_type="processing_completed",
            message="Audiobook processing completed",
        ),
    ]


@pytest.mark.asyncio
async def test_run_audiobook_job_marks_failure():
    connection = Mock()

    processing_job = Mock(spec=Job)

    with (
        patch(
            "src.pipelines.job_runner.update_job_status",
            side_effect=[processing_job, Mock(spec=Job)],
        ) as update_status,
        patch(
            "src.pipelines.job_runner.create_processing_event"
        ) as create_event,
        patch(
            "src.pipelines.job_runner.build_audiobook",
            new_callable=AsyncMock,
            side_effect=RuntimeError("TTS failed"),
        ),
    ):
        with pytest.raises(RuntimeError, match="TTS failed"):
            await run_audiobook_job(
                connection=connection,
                job_id="job-001",
                source_path="data/raw/book.pdf",
                output_dir="data/jobs/job-001",
            )

    assert update_status.call_args_list == [
        call(
            connection=connection,
            job_id="job-001",
            status=JobStatus.PROCESSING,
        ),
        call(
            connection=connection,
            job_id="job-001",
            status=JobStatus.FAILED,
            error_message="TTS failed",
        ),
    ]

    assert create_event.call_args_list == [
        call(
            connection=connection,
            job_id="job-001",
            event_type="processing_started",
            message="Audiobook processing started",
        ),
        call(
            connection=connection,
            job_id="job-001",
            event_type="processing_failed",
            message="TTS failed",
        ),
    ]


@pytest.mark.asyncio
async def test_run_audiobook_job_rejects_missing_job():
    connection = Mock()

    with (
        patch(
            "src.pipelines.job_runner.update_job_status",
            return_value=None,
        ),
        patch(
            "src.pipelines.job_runner.create_processing_event"
        ) as create_event,
        patch(
            "src.pipelines.job_runner.build_audiobook",
            new_callable=AsyncMock,
        ) as build,
    ):
        with pytest.raises(
            ValueError,
            match="Job does not exist: missing-job",
        ):
            await run_audiobook_job(
                connection=connection,
                job_id="missing-job",
                source_path="data/raw/book.pdf",
                output_dir="data/jobs/missing-job",
            )

    build.assert_not_awaited()
    create_event.assert_not_called()