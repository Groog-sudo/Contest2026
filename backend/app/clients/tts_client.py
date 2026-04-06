from __future__ import annotations

from urllib.parse import quote

from app.core.config import Settings


class TTSClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider_name = settings.tts_provider_name
        self.api_key = settings.tts_provider_api_key

    def synthesize(self, *, script: str, voice: str) -> tuple[bytes, str]:
        if self.provider_name == "mock":
            preview = quote(script[:80]).encode("utf-8")
            payload = b"MOCK_TTS_PREVIEW:" + preview
            return payload, "audio/mpeg"

        if self.provider_name == "openai":
            return self._synthesize_with_openai(script=script, voice=voice)

        payload = f"TTS provider placeholder: {self.provider_name}".encode("utf-8")
        return payload, "audio/mpeg"

    def _synthesize_with_openai(self, *, script: str, voice: str) -> tuple[bytes, str]:
        api_key = self.api_key or self.settings.openai_api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY or TTS_PROVIDER_API_KEY is required for OpenAI TTS.")

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.audio.speech.create(
            model=self.settings.openai_tts_model,
            voice=voice,
            input=script,
            response_format="mp3",
        )

        if hasattr(response, "content"):
            return response.content, "audio/mpeg"

        if hasattr(response, "read"):
            return response.read(), "audio/mpeg"

        raise RuntimeError("Unexpected OpenAI TTS response type.")
