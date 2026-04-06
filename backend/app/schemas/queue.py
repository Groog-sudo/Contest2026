from typing import Literal

from pydantic import BaseModel, Field


class QueueTaskItem(BaseModel):
    task_id: str
    task_type: str
    status: Literal["queued", "processing", "done", "failed"]
    attempts: int
    payload: dict[str, object]
    result: dict[str, object] | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class QueueTaskListResponse(BaseModel):
    items: list[QueueTaskItem]


class QueueTaskProcessRequest(BaseModel):
    task_id: str = Field(..., min_length=1)


class QueueTaskProcessResponse(BaseModel):
    task_id: str
    status: Literal["done", "failed"]
    result: dict[str, object] | None = None
    error_message: str | None = None
    retry_queued: bool = False


class QueueWorkerRunRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)


class QueueWorkerRunResponse(BaseModel):
    requested_limit: int
    processed: int
    succeeded: int
    failed: int
    requeued: int
