from app.core.config import Settings
from app.schemas.queue import QueueWorkerRunResponse
from app.services.mentoring_service import MentoringService


def run_queue_worker_once(settings: Settings, limit: int = 10) -> QueueWorkerRunResponse:
    service = MentoringService(settings)
    return service.process_pending_queue_tasks(limit=limit)
