from __future__ import annotations

import io

import httpx

from app.core.config import Settings


class STTClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider_name = settings.stt_provider_name
        self.api_key = settings.stt_provider_api_key

    def transcribe(
        self,
        *,
        recording_url: str | None = None,
        audio_bytes: bytes | None = None,
        filename: str = "recording.wav",
    ) -> str:
        if self.provider_name == "mock":
            return (
                "customer: 배달이 너무 늦었고 음식도 많이 식었습니다.\n"
                "ai: 불편을 드려 죄송합니다. 주문번호와 원하시는 조치를 먼저 확인하겠습니다."
            )

        if self.provider_name == "openai":
            blob = audio_bytes
            if blob is None and recording_url:
                blob = self._download_audio(recording_url)

            if not blob:
                raise RuntimeError("STT transcription requires recording_url or audio_bytes.")

            return self._transcribe_with_openai(blob=blob, filename=filename)

        return (
            "customer: STT provider response placeholder.\n"
            f"ai: recording_url={recording_url}"
        )

    def _download_audio(self, recording_url: str) -> bytes:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(recording_url)
            response.raise_for_status()
            return response.content

    def _transcribe_with_openai(self, *, blob: bytes, filename: str) -> str:
        api_key = self.api_key or self.settings.openai_api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY or STT_PROVIDER_API_KEY is required for OpenAI STT.")

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        file_obj = io.BytesIO(blob)
        file_obj.name = filename

        response = client.audio.transcriptions.create(
            model=self.settings.openai_stt_model,
            file=file_obj,
        )
        return response.text
