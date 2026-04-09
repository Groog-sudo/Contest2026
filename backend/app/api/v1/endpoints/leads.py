from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.lead import LeadRegistrationRequest, LeadRegistrationResponse
from app.services.delivery_issue_service import DeliveryIssueService

router = APIRouter()


@router.post("/register", response_model=LeadRegistrationResponse)
async def register_lead(
    payload: LeadRegistrationRequest,
    settings: Settings = Depends(get_settings),
) -> LeadRegistrationResponse:
    service = DeliveryIssueService(settings)
    return service.register_lead(payload)

