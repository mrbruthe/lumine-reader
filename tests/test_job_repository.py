import psycopg
import pytest

from src.database.job_repository import create_job, get_job
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