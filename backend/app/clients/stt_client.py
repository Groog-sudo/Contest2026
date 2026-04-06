from __future__ import annotations

from app.core.config import Settings


class STTClient:
    def __init__(self, settings: Settings) -> None:
        self.provider_name = settings.stt_provider_name
        self.api_key = settings.stt_provider_api_key

    def transcribe(self, *, recording_url: str) -> str:
        if self.provider_name == "mock":
            return (
                "student: 안녕하세요. 비전공자인데 AI 과정을 어디서부터 시작하면 될까요?\n"
                "ai: 현재 학습 목표와 주당 학습 시간을 먼저 확인하고 맞춤 과정을 제안드릴게요."
            )

        # Real provider integration can be added here.
        return (
            "student: STT provider response placeholder.\n"
            f"ai: recording_url={recording_url}"
        )
