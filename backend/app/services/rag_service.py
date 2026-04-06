from __future__ import annotations

from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.schemas.chat import ChatQueryResponse, SourceItem


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def query(self, question: str, top_k: int) -> ChatQueryResponse | None:
        if not self.settings.rag_configured:
            return None

        return ChatQueryResponse(
            answer=(
                "RAG pipeline placeholder response. Replace this with retrieval and generation logic "
                "when OpenAI and Pinecone credentials are configured."
            ),
            sources=[
                SourceItem(
                    id="placeholder-source-1",
                    title=f"Configured retrieval result for: {question[:40]}",
                    score=max(0.1, 1 - (top_k * 0.05)),
                )
            ],
        )

    async def ingest(self, file: UploadFile) -> dict[str, str]:
        document_id = str(uuid4())
        await file.read()
        await file.close()

        status = "accepted" if self.settings.rag_configured else "unconfigured"
        return {"document_id": document_id, "status": status}

