from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LeadRegistrationRequest(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=50)
    phone_number: str = Field(..., min_length=8, max_length=30)
    course_interest: str = Field(..., min_length=1, max_length=120)
    learning_goal: str = Field(..., min_length=1, max_length=500)
    preferred_call_time: str | None = Field(default=None, max_length=120)
    consent_to_call: bool

    @field_validator("student_name", "course_interest", "learning_goal", "preferred_call_time")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        digits = "".join(character for character in normalized if character.isdigit())
        if len(digits) < 8:
            raise ValueError("전화번호는 숫자 기준 8자리 이상이어야 합니다.")
        return normalized

    @field_validator("consent_to_call")
    @classmethod
    def ensure_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("전화 상담 동의가 필요합니다.")
        return value


class LeadRegistrationResponse(BaseModel):
    lead_id: str
    status: Literal["captured"]
    next_action: str
