import asyncio
from pathlib import Path
from unittest.mock import patch

from app.services.voice.stt.vosk_stt import VoskSTT
from app.services.voice.tts.pyttsx3_tts import Pyttsx3TTS


def test_vosk_requires_model_path():
    try:
        asyncio.run(VoskSTT().transcribe(b"audio"))
    except ValueError as exc:
        assert str(exc) == "VOSK_MODEL_PATH_REQUIRED"
    else:
        raise AssertionError("missing Vosk model path must fail")


def test_pyttsx3_requires_text():
    try:
        asyncio.run(Pyttsx3TTS().speak(""))
    except ValueError as exc:
        assert str(exc) == "TTS_TEXT_REQUIRED"
    else:
        raise AssertionError("empty TTS text must fail")


def test_pyttsx3_writes_output_file_with_mock_engine(tmp_path: Path):
    class Engine:
        def setProperty(self, name, value):
            pass

        def save_to_file(self, text, path):
            Path(path).write_bytes(b"wav")

        def runAndWait(self):
            pass

    with patch("pyttsx3.init", return_value=Engine()):
        output = asyncio.run(Pyttsx3TTS().speak("hello", str(tmp_path / "voice.wav")))
    assert Path(output).read_bytes() == b"wav"
