from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    id: str
    title: str
    score: float | None = None


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class ChatQueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]

