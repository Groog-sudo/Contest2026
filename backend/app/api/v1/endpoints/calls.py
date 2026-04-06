from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from app.core.config import Settings, get_settings
from app.schemas.call import (
    CallRequest,
    CallRequestResponse,
    CallTranscriptIngestRequest,
    CallTranscriptIngestResponse,
    RecordingUploadResponse,
    TTSPreviewRequest,
    TTSPreviewResponse,
)
from app.services.mentoring_service import MentoringService
from app.workers.queue_worker import run_queue_worker_once

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


@router.post("/recordings/upload", response_model=RecordingUploadResponse)
async def upload_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    call_id: str = Form(...),
    lead_id: str = Form(...),
    settings: Settings = Depends(get_settings),
) -> RecordingUploadResponse:
    service = MentoringService(settings)
    response = await service.upload_recording_and_enqueue(
        file=file,
        call_id=call_id,
        lead_id=lead_id,
    )
    if settings.queue_auto_process:
        background_tasks.add_task(run_queue_worker_once, settings, 1)
    return response
