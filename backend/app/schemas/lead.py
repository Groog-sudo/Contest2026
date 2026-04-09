from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LeadRegistrationRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=50)
    phone_number: str = Field(..., min_length=8, max_length=30)
    order_id: str | None = Field(default=None, max_length=80)
    order_items: list[str] = Field(default_factory=list, max_length=20)
    incident_summary: str = Field(..., min_length=1, max_length=1000)
    requested_resolution: str | None = Field(default=None, max_length=80)
    preferred_contact_time: str | None = Field(default=None, max_length=120)
    consent_to_contact: bool

    @field_validator(
        "customer_name",
        "order_id",
        "incident_summary",
        "requested_resolution",
        "preferred_contact_time",
    )
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("order_items")
    @classmethod
    def trim_items(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        return cleaned[:20]

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        digits = "".join(character for character in normalized if character.isdigit())
        if len(digits) < 8:
            raise ValueError("전화번호는 숫자 기준 8자리 이상이어야 합니다.")
        return normalized

    @field_validator("consent_to_contact")
    @classmethod
    def ensure_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("전화 상담 동의가 필요합니다.")
        return value


class LeadRegistrationResponse(BaseModel):
    lead_id: str
    status: Literal["captured"]
    next_action: str
