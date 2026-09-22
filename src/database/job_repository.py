from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.database.jobs import Job, JobStatus


def create_job(
    connection: psycopg.Connection[Any],
    job_id: str,
    source_path: str,
) -> Job:
    """Create and persist a new processing job."""

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            INSERT INTO jobs (id, source_path, status)
            VALUES (%s, %s, %s)
            RETURNING
                id,
                source_path,
                status,
                created_at,
                updated_at,
                error_message,
                output_path
            """,
            (
                job_id,
                source_path,
                JobStatus.PENDING.value,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Job insert did not return a row")

    connection.commit()

    return Job(
        id=row["id"],
        source_path=row["source_path"],
        status=JobStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        error_message=row["error_message"],
        output_path=row["output_path"],
    )

def get_job(
    connection: psycopg.Connection[Any],
    job_id: str,
) -> Job | None:
    """Retrieve a processing job by ID."""

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT
                id,
                source_path,
                status,
                created_at,
                updated_at,
                error_message,
                output_path
            FROM jobs
            WHERE id = %s
            """,
            (job_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return Job(
        id=row["id"],
        source_path=row["source_path"],
        status=JobStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        error_message=row["error_message"],
        output_path=row["output_path"],
    )

def update_job_status(
    connection: psycopg.Connection[Any],
    job_id: str,
    status: JobStatus,
    *,
    error_message: str | None = None,
    output_path: str | None = None,
) -> Job | None:
    """Update the state of an existing processing job."""

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            UPDATE jobs
            SET
                status = %s,
                updated_at = NOW(),
                error_message = %s,
                output_path = %s
            WHERE id = %s
            RETURNING
                id,
                source_path,
                status,
                created_at,
                updated_at,
                error_message,
                output_path
            """,
            (
                status.value,
                error_message,
                output_path,
                job_id,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    connection.commit()

    return Job(
        id=row["id"],
        source_path=row["source_path"],
        status=JobStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        error_message=row["error_message"],
        output_path=row["output_path"],
    )