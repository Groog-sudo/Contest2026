from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.assessment import LevelAssessmentRequest, LevelAssessmentResponse
from app.services.mentoring_service import MentoringService

router = APIRouter()


@router.post("/level-test", response_model=LevelAssessmentResponse)
async def evaluate_level_test(
    payload: LevelAssessmentRequest,
    settings: Settings = Depends(get_settings),
) -> LevelAssessmentResponse:
    service = MentoringService(settings)
    return service.evaluate_level(payload)
