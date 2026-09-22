from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProcessingEvent:
    id: int
    job_id: str
    event_type: str
    created_at: datetime
    message: str | None = None