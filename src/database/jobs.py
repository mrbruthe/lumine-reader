from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class Job:
    id: str
    source_path: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None
    output_path: str | None = None