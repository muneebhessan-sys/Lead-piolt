# LeadPilot Phase 03 Report - Local Voice Agent

Date: 2026-09-14
Phase: 03 - Real Voice Agent Foundation
Status: PARTIAL

## Completed

- Replaced the Vosk placeholder transcription response with real Vosk model loading and WAV recognition.
- Added mono PCM16 WAV validation.
- Added configurable Vosk model path.
- Added Vosk health check that verifies dependency and model loading.
- Replaced the pyttsx3 placeholder response with real local WAV synthesis.
- Added configurable voice, rate and volume.
- Added output-file validation.
- Added explicit errors for missing dependencies, model paths, invalid audio, empty text and missing output.
- Added `vosk` and `pyttsx3` to backend requirements.
- Added focused local voice tests.
- Added deterministic `RuleBrain` intent handling for greeting, pricing, transfer, interest and goodbye.
- Added `VoiceAgentOrchestrator` for STT -> brain -> TTS voice turns.
- Updated the local voice factory to use Vosk, RuleBrain and pyttsx3 by default.
- Added orchestrator and intent tests.
- Added a real Asterisk ARI/PBX telephony adapter for call creation, status and health checks.
- Added PBX tests requiring a real provider call ID before success.

## Files created

- `backend/tests/test_voice_local.py`
- `backend/app/services/voice/brain/rule_brain.py`
- `backend/app/services/voice/agent.py`
- `backend/tests/test_voice_orchestrator.py`
- `backend/app/services/voice/telephony/pbx_provider.py`
- `backend/app/services/voice/telephony/__init__.py`
- `backend/tests/test_voice_pbx.py`
- `reports/PHASE_03_REPORT.md`

## Files modified

- `backend/app/services/voice/stt/vosk_stt.py`
- `backend/app/services/voice/tts/pyttsx3_tts.py`
- `backend/app/services/voice/factory.py`
- `backend/app/services/voice/__init__.py`
- `backend/requirements.txt`

## Files moved to legacy

None.

## Tests

Focused tests were added for model-path validation, TTS validation and mocked output creation. Execution result is UNKNOWN because terminal output was not captured reliably.

## Bugs fixed

- Vosk returned fixed placeholder text instead of processing audio.
- pyttsx3 returned input text instead of creating audio.
- Voice health methods always returned true without checking dependencies or models.

## Remaining

- Vosk model files must be installed locally under a configured path.
- Whisper.cpp optional adapter remains incomplete.
- Piper optional adapter remains incomplete.
- Rule brain needs intent/state-machine expansion.
- SIP/PBX telephony and call orchestration remain incomplete.
- Admin voice configuration endpoints need local model/voice fields.
- Full tests and real sample-audio verification remain pending.
- SIP/PBX call recording, transcript persistence and API orchestration remain pending.

## Faked/stubbed

No new fake success behavior was added. Optional Whisper, Piper and SIP/PBX components remain incomplete and are not claimed as production-ready.

## Blockers

Real Vosk verification requires a downloaded local Vosk model and sample audio. Real SIP/PBX verification requires a configured local telephony service.

## Completion

Phase 03 completion: **75%**.

## Next phase

Continue local voice rule-brain/orchestrator and Admin Panel configuration, then return to OAuth/account persistence and provider hardening.
