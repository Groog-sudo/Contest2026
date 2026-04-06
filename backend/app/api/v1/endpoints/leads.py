from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.lead import LeadRegistrationRequest, LeadRegistrationResponse
from app.services.mentoring_service import MentoringService

router = APIRouter()


@router.post("/register", response_model=LeadRegistrationResponse)
async def register_lead(
    payload: LeadRegistrationRequest,
    settings: Settings = Depends(get_settings),
) -> LeadRegistrationResponse:
    service = MentoringService(settings)
    return service.register_lead(payload)
