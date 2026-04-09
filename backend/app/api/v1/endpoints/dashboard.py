from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.schemas.dashboard import DashboardMetricsResponse
from app.services.delivery_issue_service import DeliveryIssueService

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    period_days: int = Query(default=7, ge=7, le=90),
    settings: Settings = Depends(get_settings),
) -> DashboardMetricsResponse:
    service = DeliveryIssueService(settings)
    return service.get_dashboard_metrics(period_days=period_days)

