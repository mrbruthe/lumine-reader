import psycopg
import pytest

from src.database.event_repository import create_processing_event
from src.database.job_repository import create_job


DATABASE_URL = "postgresql://lumine:lumine@localhost:5432/lumine"


@pytest.fixture
def db_connection():
    connection = psycopg.connect(DATABASE_URL)

    yield connection

    connection.rollback()

    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM jobs WHERE id = %s",
            ("test-event-job",),
        )

    connection.commit()
    connection.close()


def test_create_processing_event_persists_event(db_connection):
    create_job(
        connection=db_connection,
        job_id="test-event-job",
        source_path="data/raw/book.pdf",
    )

    event = create_processing_event(
        connection=db_connection,
        job_id="test-event-job",
        event_type="processing_started",
        message="Audiobook processing started",
    )

    assert event.job_id == "test-event-job"
    assert event.event_type == "processing_started"
    assert event.message == "Audiobook processing started"
    assert event.id > 0

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT job_id, event_type, message
            FROM processing_events
            WHERE id = %s
            """,
            (event.id,),
        )

        row = cursor.fetchone()

    assert row == (
        "test-event-job",
        "processing_started",
        "Audiobook processing started",
    )