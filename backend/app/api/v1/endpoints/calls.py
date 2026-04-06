from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.call import (
    CallRequest,
    CallRequestResponse,
    CallTranscriptIngestRequest,
    CallTranscriptIngestResponse,
    TTSPreviewRequest,
    TTSPreviewResponse,
)
from app.services.mentoring_service import MentoringService

router = APIRouter()


@router.post("/request", response_model=CallRequestResponse)
async def request_call(
    payload: CallRequest,
    settings: Settings = Depends(get_settings),
) -> CallRequestResponse:
    service = MentoringService(settings)
    return service.create_call_request(payload)


@router.post("/transcripts/ingest", response_model=CallTranscriptIngestResponse)
async def ingest_call_transcript(
    payload: CallTranscriptIngestRequest,
    settings: Settings = Depends(get_settings),
) -> CallTranscriptIngestResponse:
    service = MentoringService(settings)
    return service.ingest_call_transcript(payload)


@router.post("/tts/preview", response_model=TTSPreviewResponse)
async def preview_tts(
    payload: TTSPreviewRequest,
    settings: Settings = Depends(get_settings),
) -> TTSPreviewResponse:
    service = MentoringService(settings)
    return service.create_tts_preview(payload)
