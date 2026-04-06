from __future__ import annotations

from urllib.parse import quote

from app.core.config import Settings


class TTSClient:
    def __init__(self, settings: Settings) -> None:
        self.provider_name = settings.tts_provider_name
        self.api_key = settings.tts_provider_api_key

    def synthesize(self, *, script: str, voice: str) -> tuple[str, str]:
        if self.provider_name == "mock":
            preview = quote(script[:80])
            audio_url = f"https://mock-tts.local/preview?voice={quote(voice)}&q={preview}"
            return audio_url, "mock/mp3"

        # Real provider integration can be added here.
        audio_url = f"https://{self.provider_name}.local/tts-placeholder"
        return audio_url, "audio/mpeg"
