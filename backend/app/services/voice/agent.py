from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VoiceTurnResult:
    transcript: str
    response_text: str
    audio_path: str | None = None


class VoiceAgentOrchestrator:
    """Connect local STT, deterministic brain and local TTS for one voice turn."""

    def __init__(self, stt, brain, tts) -> None:
        self.stt = stt
        self.brain = brain
        self.tts = tts

    async def process_turn(self, audio_bytes: bytes, output_path: str | None = None) -> VoiceTurnResult:
        transcript = await self.stt.transcribe(audio_bytes=audio_bytes)
        response_text = await self.brain.respond(transcript)
        audio_path = await self.tts.speak(response_text, output_path=output_path)
        return VoiceTurnResult(
            transcript=transcript,
            response_text=response_text,
            audio_path=audio_path,
        )

    async def health_check(self) -> dict[str, Any]:
        return {
            "stt": await self.stt.health_check(),
            "brain": True,
            "tts": await self.tts.health_check(),
        }
