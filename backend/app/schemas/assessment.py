from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SkillAnswer(BaseModel):
    area: str = Field(..., min_length=1, max_length=50)
    score: int = Field(..., ge=1, le=5)

    @field_validator("area")
    @classmethod
    def trim_area(cls, value: str) -> str:
        return value.strip()


class LevelAssessmentRequest(BaseModel):
    lead_id: str = Field(..., min_length=1)
    answers: list[SkillAnswer] = Field(..., min_length=1, max_length=20)
    additional_context: str | None = Field(default=None, max_length=1000)

    @field_validator("lead_id", "additional_context")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class LevelAssessmentResponse(BaseModel):
    assessment_id: str
    level: Literal["beginner", "intermediate", "advanced"]
    score: int
    recommended_course: str
    mentoring_plan: str
    rag_context_ids: list[str]
