from __future__ import annotations

import base64
import httpx
from typing import Any

from .base import MessageProvider, SendResult


class GmailProvider(MessageProvider):
    name = "GMAIL"

    def __init__(self, credentials: dict[str, Any] | None = None, access_token: str = "", base_url: str = "https://gmail.googleapis.com") -> None:
        self.credentials = credentials or {}
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")

    async def send(self, to: str, body: str, context: dict[str, Any] | None = None) -> SendResult:
        if not self.access_token:
            raise ValueError("GMAIL_NOT_CONFIGURED")
        if not to.strip() or not body.strip():
            raise ValueError("GMAIL_RECIPIENT_AND_BODY_REQUIRED")
        context = context or {}
        headers_text = [f"To: {to}", f"Subject: {context.get('subject', 'LeadPilot message')}", "Content-Type: text/plain; charset=utf-8", "", body]
        raw = base64.urlsafe_b64encode("\r\n".join(headers_text).encode()).decode()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/gmail/v1/users/me/messages/send",
                json={"raw": raw},
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
        if response.is_error:
            raise ValueError(f"GMAIL_SEND_FAILED: HTTP_{response.status_code}")
        data = response.json()
        provider_id = data.get("id")
        if not provider_id:
            raise ValueError("GMAIL_SEND_FAILED: PROVIDER_ID_MISSING")
        return SendResult({
            "status": "SENT",
            "channel": self.name,
            "recipient": to,
            "provider": "GMAIL",
            "provider_message_id": provider_id,
            "metadata": context,
        })

    async def health_check(self) -> bool:
        if not self.access_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.base_url}/gmail/v1/users/me/profile",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
            return response.is_success
        except httpx.HTTPError:
            return False

    def capabilities(self) -> list[str]:
        return ["gmail", "email"]
