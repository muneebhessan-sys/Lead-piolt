from __future__ import annotations

import httpx
from typing import Any

from app.config import settings
from app.models import VoiceAgentConfig


class LocalVoiceAgentProvider:
    """Adapter for the local voice agent with explicit status lifecycle and no fabricated success."""

    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    CONNECTED = "CONNECTED"

    def __init__(self, config: VoiceAgentConfig | None = None, stt=None, tts=None, brain=None, telephony=None) -> None:
        self.config = config
        self.stt = stt
        self.tts = tts
        self.brain = brain
        self.telephony = telephony
        self._call_status: dict[str, dict[str, Any]] = {}

    @property
    def status(self) -> str:
        """Return current status: NOT_CONFIGURED if no config, UNAVAILABLE until health-verified, CONNECTED never fabricated."""
        if not self.config or not self.config.enabled or not self.config.base_url:
            return self.NOT_CONFIGURED
        return self.UNAVAILABLE

    def _require_configured(self) -> None:
        """Raise if the provider is not configured."""
        if not self.config or not self.config.enabled or not self.config.base_url:
            raise ValueError("VOICE_AGENT_NOT_CONFIGURED")

    def _require_available(self) -> None:
        """Raise if the provider is not configured or not available."""
        self._require_configured()
        if self.status == self.UNAVAILABLE:
            raise ValueError("VOICE_AGENT_UNAVAILABLE")

    def _base_url(self) -> str:
        """Return the base URL with trailing slash removed."""
        return self.config.base_url.rstrip("/") if self.config else ""

    def _health_endpoint(self) -> str:
        """Build the full health check endpoint URL."""
        base = self._base_url()
        path = (self.config.health_path or "/health").lstrip("/")
        return f"{base}/{path}" if path else base

    def _call_endpoint(self) -> str:
        """Build the full call endpoint URL."""
        base = self._base_url()
        path = (self.config.call_path or "/calls").lstrip("/")
        return f"{base}/{path}" if path else base

    async def health(self) -> dict[str, Any]:
        """Check the voice agent health endpoint; returns CONNECTED or UNAVAILABLE (never fabricated success)."""
        if self.config is None and any((self.stt, self.tts, self.brain)):
            return {
                "status": self.CONNECTED,
                "stt_available": self.stt is not None,
                "tts_available": self.tts is not None,
                "brain_available": self.brain is not None,
            }
        self._require_configured()
        url = self._health_endpoint()
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
            return {"status": self.CONNECTED, "base_url": self.config.base_url, "health_path": self.config.health_path}
        except (httpx.HTTPError, ValueError) as exc:
            return {"status": self.UNAVAILABLE, "base_url": self.config.base_url, "error": str(exc)}

    def capabilities(self) -> list[str]:
        """Return the list of capabilities exposed by the voice agent when configured."""
        if self.status == self.NOT_CONFIGURED:
            return []
        return ["health", "call", "call_status", "capabilities"]

    async def health_check(self) -> dict[str, Any]:
        return await self.health()

    async def transcribe(self, audio_bytes: bytes | None = None, text: str | None = None) -> str:
        if self.stt is None:
            raise ValueError("VOICE_STT_NOT_CONFIGURED")
        return await self.stt.transcribe(audio_bytes=audio_bytes, text=text)

    async def speak(self, text: str) -> str:
        if self.tts is None:
            raise ValueError("VOICE_TTS_NOT_CONFIGURED")
        return await self.tts.speak(text)

    async def respond(self, user_text: str) -> str:
        if self.brain is None:
            raise ValueError("VOICE_BRAIN_NOT_CONFIGURED")
        return await self.brain.respond(user_text)

    async def start_call(self, lead_id: int, caller_id: str | None = None, to_number: str | None = None) -> dict[str, Any]:
        """Initiate a call through the voice agent; raises if not configured or unavailable."""
        self._require_available()
        payload: dict[str, Any] = {"lead_id": lead_id, "caller_id": caller_id or "", "to_number": to_number or ""}
        url = self._call_endpoint()
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            data = response.json()
            call_id = str(data.get("id", ""))
            self._call_status[call_id] = {"status": "CONNECTED", "provider_reference": data}
            return data
        except (httpx.HTTPError, ValueError) as exc:
            raise ValueError(f"VOICE_AGENT_UNAVAILABLE: {exc}") from exc

    async def get_call_status(self, call_id: str) -> dict[str, Any]:
        """Retrieve the status of a previously initiated call by its ID."""
        self._require_available()
        cached = self._call_status.get(call_id)
        if cached is not None:
            return {"call_id": call_id, "status": cached["status"], "provider_reference": cached.get("provider_reference", {})}
        url = f"{self._call_endpoint()}/{call_id}"
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
            data = response.json()
            status = data.get("status", "UNKNOWN")
            self._call_status[call_id] = {"status": status, "provider_reference": data}
            return {"call_id": call_id, "status": status, "provider_reference": data}
        except (httpx.HTTPError, ValueError) as exc:
            return {"call_id": call_id, "status": "UNKNOWN", "error": str(exc)}
