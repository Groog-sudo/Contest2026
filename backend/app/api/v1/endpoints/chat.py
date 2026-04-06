from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/query", response_model=ChatQueryResponse)
async def query_chat(
    payload: ChatQueryRequest,
    settings: Settings = Depends(get_settings),
) -> ChatQueryResponse:
    service = RAGService(settings)
    result = service.query(question=payload.question, top_k=payload.top_k)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "RAG service is not configured yet. "
                "Set OPENAI_API_KEY, PINECONE_API_KEY, and PINECONE_INDEX_NAME to enable it."
            ),
        )

    return result

