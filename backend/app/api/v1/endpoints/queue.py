from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.queue import (
    QueueTaskListResponse,
    QueueTaskProcessRequest,
    QueueTaskProcessResponse,
    QueueWorkerRunRequest,
    QueueWorkerRunResponse,
)
from app.services.delivery_issue_service import DeliveryIssueService

router = APIRouter()


@router.get("/tasks", response_model=QueueTaskListResponse)
async def list_queue_tasks(
    settings: Settings = Depends(get_settings),
) -> QueueTaskListResponse:
    service = DeliveryIssueService(settings)
    return service.list_queue_tasks()


@router.post("/process", response_model=QueueTaskProcessResponse)
async def process_queue_task(
    payload: QueueTaskProcessRequest,
    settings: Settings = Depends(get_settings),
) -> QueueTaskProcessResponse:
    service = DeliveryIssueService(settings)
    return service.process_queue_task(payload.task_id)


@router.post("/workers/run", response_model=QueueWorkerRunResponse)
async def run_queue_worker(
    payload: QueueWorkerRunRequest,
    settings: Settings = Depends(get_settings),
) -> QueueWorkerRunResponse:
    service = DeliveryIssueService(settings)
    return service.process_pending_queue_tasks(limit=payload.limit)

