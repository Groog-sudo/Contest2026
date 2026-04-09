from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.assessment import IncidentAnalysisRequest, IncidentAnalysisResponse
from app.services.delivery_issue_service import DeliveryIssueService

router = APIRouter()


@router.post("/analyze", response_model=IncidentAnalysisResponse)
async def analyze_incident(
    payload: IncidentAnalysisRequest,
    settings: Settings = Depends(get_settings),
) -> IncidentAnalysisResponse:
    service = DeliveryIssueService(settings)
    return service.analyze_incident(payload)

