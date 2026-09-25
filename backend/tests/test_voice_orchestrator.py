import asyncio
from pathlib import Path

from app.services.voice.agent import VoiceAgentOrchestrator
from app.services.voice.brain.rule_brain import RuleBrain


class FakeSTT:
    async def transcribe(self, audio_bytes):
        assert audio_bytes == b"audio"
        return "I want pricing"

    async def health_check(self):
        return True


class FakeTTS:
    async def speak(self, text, output_path=None):
        assert "pricing" in text.lower()
        path = Path(output_path or "voice.wav")
        path.write_bytes(b"wav")
        return str(path)

    async def health_check(self):
        return True


def test_rule_brain_intents():
    brain = RuleBrain()
    assert "pricing" in asyncio.run(brain.respond("How much does it cost?"))
    assert "team member" in asyncio.run(brain.respond("I want a human"))
    assert "Goodbye" in asyncio.run(brain.respond("goodbye"))


def test_orchestrator_connects_stt_brain_tts(tmp_path):
    result = asyncio.run(
        VoiceAgentOrchestrator(FakeSTT(), RuleBrain(), FakeTTS()).process_turn(
            b"audio", output_path=str(tmp_path / "turn.wav")
        )
    )
    assert result.transcript == "I want pricing"
    assert "pricing" in result.response_text.lower()
    assert Path(result.audio_path).exists()
