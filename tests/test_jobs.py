from datetime import datetime, timezone

from src.database.jobs import Job, JobStatus


def test_job_can_be_created():
    now = datetime.now(timezone.utc)

    job = Job(
        id="job-001",
        source_path="data/raw/book.pdf",
        status=JobStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

    assert job.id == "job-001"
    assert job.source_path == "data/raw/book.pdf"
    assert job.status == JobStatus.PENDING
    assert job.created_at == now
    assert job.updated_at == now
    assert job.error_message is None
    assert job.output_path is None


def test_job_status_values():
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.PROCESSING.value == "processing"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"