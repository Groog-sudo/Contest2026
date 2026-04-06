from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import Settings, get_settings
from app.schemas.document import UploadDocumentResponse
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/upload", response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> UploadDocumentResponse:
    service = RAGService(settings)
    return await service.ingest(file)

