from __future__ import annotations

from app.config import settings


class PiperTTS:
    def __init__(self, model_path: str = "") -> None:
        self.model_path = model_path

    async def speak(self, text: str) -> str:
        if not settings.development_mode:
            raise NotImplementedError("PIPER_TRANSPORT_NOT_IMPLEMENTED")
        return text

    async def health_check(self) -> bool:
        return True
