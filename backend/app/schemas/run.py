from datetime import datetime

from pydantic import BaseModel


class RunResponse(BaseModel):
    id: int
    scheduled_job_id: int | None
    llm_model_id: str | None
    benchmark_name: str | None
    status: str
    progress: str | None = None
    result: dict | None
    log_path: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
