import psycopg
import pytest

from src.database.job_repository import (
    create_job,
    get_job,
    update_job_status,
)

from src.database.jobs import JobStatus


DATABASE_URL = "postgresql://lumine:lumine@localhost:5432/lumine"


@pytest.fixture
def db_connection():
    connection = psycopg.connect(DATABASE_URL)

    yield connection

    connection.rollback()

    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM jobs WHERE id = %s",
            ("test-job-001",),
        )

    connection.commit()
    connection.close()


def test_create_job_persists_job(db_connection):
    job = create_job(
        connection=db_connection,
        job_id="test-job-001",
        source_path="data/raw/book.pdf",
    )

    assert job.id == "test-job-001"
    assert job.source_path == "data/raw/book.pdf"
    assert job.status == JobStatus.PENDING
    assert job.error_message is None
    assert job.output_path is None

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, source_path, status
            FROM jobs
            WHERE id = %s
            """,
            ("test-job-001",),
        )

        row = cursor.fetchone()

    assert row == (
        "test-job-001",
        "data/raw/book.pdf",
        "pending",
    )

def test_get_job_returns_persisted_job(db_connection):
    created_job = create_job(
        connection=db_connection,
        job_id="test-job-001",
        source_path="data/raw/book.pdf",
    )

    retrieved_job = get_job(
        connection=db_connection,
        job_id=created_job.id,
    )

    assert retrieved_job == created_job


def test_get_job_returns_none_when_job_does_not_exist(db_connection):
    job = get_job(
        connection=db_connection,
        job_id="missing-job",
    )

    assert job is None

def test_update_job_status_to_processing(db_connection):
    create_job(
        connection=db_connection,
        job_id="test-job-001",
        source_path="data/raw/book.pdf",
    )

    job = update_job_status(
        connection=db_connection,
        job_id="test-job-001",
        status=JobStatus.PROCESSING,
    )

    assert job is not None
    assert job.status == JobStatus.PROCESSING


def test_update_job_status_to_completed(db_connection):
    create_job(
        connection=db_connection,
        job_id="test-job-001",
        source_path="data/raw/book.pdf",
    )

    job = update_job_status(
        connection=db_connection,
        job_id="test-job-001",
        status=JobStatus.COMPLETED,
        output_path="data/jobs/test-job-001/final.mp3",
    )

    assert job is not None
    assert job.status == JobStatus.COMPLETED
    assert job.output_path == "data/jobs/test-job-001/final.mp3"


def test_update_job_status_to_failed(db_connection):
    create_job(
        connection=db_connection,
        job_id="test-job-001",
        source_path="data/raw/book.pdf",
    )

    job = update_job_status(
        connection=db_connection,
        job_id="test-job-001",
        status=JobStatus.FAILED,
        error_message="TTS generation failed",
    )

    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error_message == "TTS generation failed"

def test_update_job_status_returns_none_when_job_does_not_exist(db_connection):
    job = update_job_status(
        connection=db_connection,
        job_id="missing-job",
        status=JobStatus.PROCESSING,
    )

    assert job is None