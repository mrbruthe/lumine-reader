from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.database.events import ProcessingEvent


def create_processing_event(
    connection: psycopg.Connection[Any],
    job_id: str,
    event_type: str,
    message: str | None = None,
) -> ProcessingEvent:
    """Record an event for a processing job."""

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            INSERT INTO processing_events (
                job_id,
                event_type,
                message
            )
            VALUES (%s, %s, %s)
            RETURNING
                id,
                job_id,
                event_type,
                message,
                created_at
            """,
            (
                job_id,
                event_type,
                message,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Processing event insert did not return a row")

    connection.commit()

    return ProcessingEvent(
        id=row["id"],
        job_id=row["job_id"],
        event_type=row["event_type"],
        message=row["message"],
        created_at=row["created_at"],
    )