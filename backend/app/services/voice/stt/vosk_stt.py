from __future__ import annotations

import asyncio
import io
import json
import wave


class VoskSTT:
    def __init__(self, model_path: str = "") -> None:
        self.model_path = model_path

    async def transcribe(self, audio_bytes: bytes | None = None, text: str | None = None) -> str:
        if audio_bytes is None:
            raise ValueError("VOSK_AUDIO_REQUIRED")
        if not self.model_path:
            raise ValueError("VOSK_MODEL_PATH_REQUIRED")

        def recognize() -> str:
            try:
                from vosk import KaldiRecognizer, Model
            except ImportError as exc:
                raise RuntimeError("VOSK_DEPENDENCY_MISSING") from exc
            try:
                with wave.open(io.BytesIO(audio_bytes), "rb") as audio:
                    if audio.getnchannels() != 1 or audio.getsampwidth() != 2:
                        raise ValueError("VOSK_REQUIRES_MONO_PCM16_WAV")
                    recognizer = KaldiRecognizer(Model(self.model_path), audio.getframerate())
                    while chunk := audio.readframes(4000):
                        recognizer.AcceptWaveform(chunk)
                    result = json.loads(recognizer.FinalResult())
                    return str(result.get("text", "")).strip()
            except (wave.Error, OSError) as exc:
                raise ValueError("VOSK_INVALID_WAV_AUDIO") from exc

        return await asyncio.to_thread(recognize)

    async def health_check(self) -> bool:
        if not self.model_path:
            return False
        try:
            from vosk import Model
            await asyncio.to_thread(Model, self.model_path)
            return True
        except (ImportError, OSError, RuntimeError):
            return False
