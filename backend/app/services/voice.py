from __future__ import annotations

import httpx

from app.config import settings
from app.models import VoiceAgentConfig


class LocalVoiceAgentProvider:
    def __init__(self, config: VoiceAgentConfig | None = None):
        self.config = config

    @property
    def status(self) -> str:
        if not self.config or not self.config.enabled or not self.config.base_url:
            return "NOT_CONFIGURED"
        return "UNAVAILABLE"

    async def health_check(self) -> dict:
        if not self.config or not self.config.enabled or not self.config.base_url:
            raise ValueError("VOICE_AGENT_NOT_CONFIGURED")
        url = self.config.base_url.rstrip("/") + "/" + self.config.health_path.lstrip("/")
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
        except (httpx.HTTPError, ValueError) as exc:
            return {"status": "UNAVAILABLE", "base_url": self.config.base_url, "health_path": self.config.health_path, "error": str(exc)}
        return {"status": "CONNECTED", "base_url": self.config.base_url, "health_path": self.config.health_path}

    async def start_call(self, lead_id: int, caller_id: str | None = None) -> dict:
        if not self.config or not self.config.enabled or not self.config.base_url:
            raise ValueError("VOICE_AGENT_NOT_CONFIGURED")
        health = await self.health_check()
        if health.get("status") != "CONNECTED":
            raise ValueError("VOICE_AGENT_UNAVAILABLE")
        payload = {"lead_id": lead_id, "caller_id": caller_id}
        url = self.config.base_url.rstrip("/") + "/" + self.config.call_path.lstrip("/")
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValueError("VOICE_AGENT_UNAVAILABLE") from exc
        return response.json()
