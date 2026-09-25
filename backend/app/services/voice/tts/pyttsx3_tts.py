from __future__ import annotations

import asyncio
import importlib
import tempfile
from pathlib import Path


class Pyttsx3TTS:
    def __init__(self, voice: str = "default", rate: int = 170, volume: float = 1.0) -> None:
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def speak(self, text: str, output_path: str | None = None) -> str:
        if not text.strip():
            raise ValueError("TTS_TEXT_REQUIRED")
        destination = Path(output_path or tempfile.mktemp(prefix="leadpilot-voice-", suffix=".wav"))

        def synthesize() -> None:
            try:
                pyttsx3 = importlib.import_module("pyttsx3")
            except ImportError as exc:
                raise RuntimeError("PYTTSX3_DEPENDENCY_MISSING") from exc
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice != "default":
                voices = engine.getProperty("voices") or []
                match = next((item for item in voices if self.voice.lower() in str(item.id).lower()), None)
                if match is None:
                    raise ValueError("PYTTSX3_VOICE_NOT_FOUND")
                engine.setProperty("voice", match.id)
            engine.save_to_file(text, str(destination))
            engine.runAndWait()

        await asyncio.to_thread(synthesize)
        if not destination.exists():
            raise RuntimeError("PYTTSX3_OUTPUT_NOT_CREATED")
        return str(destination)

    async def health_check(self) -> bool:
        try:
            pyttsx3 = importlib.import_module("pyttsx3")
            engine = await asyncio.to_thread(pyttsx3.init)
            engine.stop()
            return True
        except (ImportError, RuntimeError):
            return False
