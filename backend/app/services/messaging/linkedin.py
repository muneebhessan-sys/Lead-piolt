from __future__ import annotations

import httpx
from typing import Any

from .base import MessageProvider, SendResult


class LinkedInProvider(MessageProvider):
    name = "LINKEDIN"

    def __init__(self, access_token: str = "", base_url: str = "https://api.linkedin.com", sender_urn: str = "") -> None:
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.sender_urn = sender_urn

    async def send(self, to: str, body: str, context: dict[str, Any] | None = None) -> SendResult:
        if not self.access_token or not self.sender_urn:
            raise ValueError("LINKEDIN_NOT_CONFIGURED")
        if not to.strip() or not body.strip():
            raise ValueError("LINKEDIN_RECIPIENT_AND_BODY_REQUIRED")
        payload = {
            "sender": {"person": self.sender_urn},
            "recipients": [{"person": to}],
            "subject": str((context or {}).get("subject", "LeadPilot message")),
            "content": {"content": {"text": body}},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/v2/messages",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
            )
        if response.is_error:
            raise ValueError(f"LINKEDIN_SEND_FAILED: HTTP_{response.status_code}")
        provider_id = response.headers.get("x-restli-id") or response.json().get("id")
        if not provider_id:
            raise ValueError("LINKEDIN_SEND_FAILED: PROVIDER_ID_MISSING")
        return SendResult({
            "status": "SENT",
            "channel": self.name,
            "recipient": to,
            "provider": "LINKEDIN",
            "provider_message_id": provider_id,
            "metadata": context or {},
        })

    async def health_check(self) -> bool:
        if not self.access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.base_url}/v2/userinfo",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
            return response.is_success
        except httpx.HTTPError:
            return False

    def capabilities(self) -> list[str]:
        return ["linkedin", "messaging"]
