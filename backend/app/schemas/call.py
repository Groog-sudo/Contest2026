from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class CallSourceItem(BaseModel):
    id: str
    title: str
    score: float | None = None


class CallRequest(BaseModel):
    lead_id: str = Field(..., min_length=1)
    student_name: str = Field(..., min_length=1, max_length=50)
    phone_number: str = Field(..., min_length=8, max_length=30)
    course_interest: str = Field(..., min_length=1, max_length=120)
    student_question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)

    @field_validator("lead_id", "student_name", "course_interest", "student_question")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        digits = "".join(character for character in normalized if character.isdigit())
        if len(digits) < 8:
            raise ValueError("전화번호는 숫자 기준 8자리 이상이어야 합니다.")
        return normalized


class CallRequestResponse(BaseModel):
    call_id: str
    status: Literal["drafted", "script_ready", "queued"]
    script_preview: str
    sources: list[CallSourceItem]
    next_step: str


class CallTranscriptTurn(BaseModel):
    speaker: Literal["student", "ai", "counselor"] = "student"
    utterance: str = Field(..., min_length=1, max_length=2000)

    @field_validator("utterance")
    @classmethod
    def trim_utterance(cls, value: str) -> str:
        return value.strip()


class CallTranscriptIngestRequest(BaseModel):
    call_id: str = Field(..., min_length=1)
    lead_id: str = Field(..., min_length=1)
    recording_url: str | None = Field(default=None, max_length=1000)
    transcript_text: str | None = Field(default=None, max_length=6000)
    turns: list[CallTranscriptTurn] | None = None

    @field_validator("call_id", "lead_id")
    @classmethod
    def trim_identity(cls, value: str) -> str:
        return value.strip()

    @field_validator("recording_url", "transcript_text")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @model_validator(mode="after")
    def validate_sources(self) -> "CallTranscriptIngestRequest":
        if self.turns or self.transcript_text or self.recording_url:
            return self
        raise ValueError("turns, transcript_text, recording_url 중 하나 이상이 필요합니다.")


class CallTranscriptIngestResponse(BaseModel):
    transcript_id: str
    status: Literal["stored"]
    saved_turns: int
    summary: str


class TTSPreviewRequest(BaseModel):
    script: str = Field(..., min_length=1, max_length=2000)
    voice: str = Field(default="mentor-ko", min_length=1, max_length=40)

    @field_validator("script", "voice")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()


class TTSPreviewResponse(BaseModel):
    status: Literal["generated"]
    provider: str
    voice: str
    audio_url: str
    mime_type: str


class RecordingUploadResponse(BaseModel):
    recording_id: str
    status: Literal["queued"]
    object_key: str
    storage_url: str
    queue_task_id: str
