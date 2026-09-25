from __future__ import annotations

import httpx
from typing import Any

from .base import MessageProvider, SendResult


class InstagramProvider(MessageProvider):
    name = "INSTAGRAM"

    def __init__(self, access_token: str = "", business_account_id: str = "", api_version: str = "v20.0", base_url: str = "https://graph.facebook.com") -> None:
        self.access_token = access_token
        self.business_account_id = business_account_id
        self.api_version = api_version
        self.base_url = base_url.rstrip("/")

    async def send(self, to: str, body: str, context: dict[str, Any] | None = None) -> SendResult:
        if not self.access_token or not self.business_account_id:
            raise ValueError("INSTAGRAM_NOT_CONFIGURED")
        if not to.strip() or not body.strip():
            raise ValueError("INSTAGRAM_RECIPIENT_AND_BODY_REQUIRED")
        url = f"{self.base_url}/{self.api_version}/{self.business_account_id}/messages"
        payload = {
            "recipient": {"id": to},
            "message": {"text": body},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, params={"access_token": self.access_token})
        if response.is_error:
            raise ValueError(f"INSTAGRAM_SEND_FAILED: HTTP_{response.status_code}")
        data = response.json()
        provider_id = data.get("message_id") or data.get("id")
        if not provider_id:
            raise ValueError("INSTAGRAM_SEND_FAILED: PROVIDER_ID_MISSING")
        return SendResult({
            "status": "SENT",
            "channel": self.name,
            "recipient": to,
            "provider": "INSTAGRAM",
            "provider_message_id": provider_id,
            "metadata": context or {},
        })

    async def health_check(self) -> bool:
        if not self.access_token or not self.business_account_id:
            return False
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.base_url}/{self.api_version}/{self.business_account_id}",
                    params={"fields": "id,username", "access_token": self.access_token},
                )
            return response.is_success
        except httpx.HTTPError:
            return False

    def capabilities(self) -> list[str]:
        return ["instagram", "dm"]
