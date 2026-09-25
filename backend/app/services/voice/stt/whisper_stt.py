from __future__ import annotations

from app.config import settings


class WhisperSTT:
    def __init__(self, model_path: str = "") -> None:
        self.model_path = model_path

    async def transcribe(self, audio_bytes: bytes | None = None, text: str | None = None) -> str:
        if not settings.development_mode:
            raise NotImplementedError("WHISPER_TRANSPORT_NOT_IMPLEMENTED")
        if text is not None:
            return text
        if audio_bytes is None:
            return ""
        return "transcribed whisper audio"

    async def health_check(self) -> bool:
        return True
