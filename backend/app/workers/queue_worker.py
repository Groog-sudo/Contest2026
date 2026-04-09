from app.core.config import Settings
from app.schemas.queue import QueueWorkerRunResponse
from app.services.delivery_issue_service import DeliveryIssueService


def run_queue_worker_once(settings: Settings, limit: int = 10) -> QueueWorkerRunResponse:
    service = DeliveryIssueService(settings)
    return service.process_pending_queue_tasks(limit=limit)

