from __future__ import annotations

from .brain.conversation import ConversationBrain
from .brain.rule_brain import RuleBrain
from .provider import LocalVoiceAgentProvider
from .stt.vosk_stt import VoskSTT
from .tts.pyttsx3_tts import Pyttsx3TTS


class VoiceAgentFactory:
    @staticmethod
    def create_local_provider(
        *,
        stt_backend: str = "vosk",
        tts_backend: str = "pyttsx3",
        conversation_prompt: str | None = None,
        model_path: str = "",
    ) -> LocalVoiceAgentProvider:
        stt = VoskSTT(model_path=model_path) if stt_backend == "vosk" else VoskSTT(model_path=model_path)
        tts = Pyttsx3TTS() if tts_backend == "pyttsx3" else Pyttsx3TTS()
        brain = RuleBrain()
        return LocalVoiceAgentProvider(stt=stt, tts=tts, brain=brain)
