from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


PrimaryCategory = Literal[
    "merchant_issue",
    "delivery_issue",
    "platform_issue",
    "multi_party_issue",
    "needs_review",
]
ResponsibleParty = Literal["merchant", "delivery_provider", "platform", "internal_review"]
Severity = Literal["low", "medium", "high", "critical"]
CustomerEmotion = Literal["calm", "upset", "angry", "distressed"]
EvidenceType = Literal["photo", "video", "none", "unknown"]
ResolutionType = Literal["refund", "redelivery", "recook", "apology", "investigation"]


class IncidentAnalysisRequest(BaseModel):
    lead_id: str = Field(..., min_length=1)
    call_id: str | None = Field(default=None, max_length=80)
    customer_message: str | None = Field(default=None, max_length=3000)
    transcript_text: str | None = Field(default=None, max_length=6000)
    order_id: str | None = Field(default=None, max_length=80)
    ordered_at: str | None = Field(default=None, max_length=80)
    delivered_at: str | None = Field(default=None, max_length=80)
    order_items: list[str] = Field(default_factory=list, max_length=20)
    evidence_available: EvidenceType = "unknown"
    requested_resolution: list[ResolutionType] = Field(default_factory=list, max_length=5)

    @field_validator("lead_id", "call_id", "customer_message", "transcript_text", "order_id", "ordered_at", "delivered_at")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("order_items")
    @classmethod
    def trim_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()][:20]

    @model_validator(mode="after")
    def ensure_message_exists(self) -> "IncidentAnalysisRequest":
        if self.customer_message or self.transcript_text:
            return self
        raise ValueError("customer_message 또는 transcript_text 중 하나 이상이 필요합니다.")


class OrderInfo(BaseModel):
    order_id: str | None
    items: list[str]
    ordered_at: str | None
    delivered_at: str | None


class IssueDetails(BaseModel):
    reported_problem: str
    evidence_available: EvidenceType
    missing_items: list[str]
    wrong_items: list[str]
    foreign_object_reported: bool
    allergy_or_health_risk: bool
    delivery_delay_minutes: int | None
    package_damage: bool


class FeedbackMessage(BaseModel):
    send: bool
    message: str


class IncidentAnalysisResponse(BaseModel):
    summary_for_customer: str
    incident_overview: str
    primary_category: PrimaryCategory
    subcategories: list[str]
    responsible_parties: list[ResponsibleParty]
    severity: Severity
    safety_flag: bool
    refund_request: bool
    redelivery_request: bool
    recook_request: bool
    customer_emotion: CustomerEmotion
    order_info: OrderInfo
    issue_details: IssueDetails
    customer_requested_resolution: list[ResolutionType]
    follow_up_questions_needed: list[str]
    merchant_feedback: FeedbackMessage
    delivery_feedback: FeedbackMessage
    platform_feedback: FeedbackMessage
    internal_review_note: str
