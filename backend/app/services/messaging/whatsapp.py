from __future__ import annotations

import httpx
from typing import Any

from .base import MessageProvider, SendResult


class WhatsAppProvider(MessageProvider):
    name = "WHATSAPP"

    def __init__(
        self,
        token: str = "",
        phone_number_id: str = "",
        business_account_id: str = "",
        api_version: str = "v20.0",
        base_url: str = "https://graph.facebook.com",
    ) -> None:
        self.token = token
        self.phone_number_id = phone_number_id
        self.business_account_id = business_account_id
        self.api_version = api_version
        self.base_url = base_url.rstrip("/")

    def _build_success_result(self, to: str, body: str, metadata: dict[str, Any] | None = None) -> SendResult:
        return SendResult({
            "status": "SENT",
            "channel": self.name,
            "recipient": to,
            "body": body,
            "provider": "WHATSAPP",
            "metadata": metadata or {},
        })

    async def send(self, to: str, body: str, context: dict[str, Any] | None = None) -> SendResult:
        if not self.token or not self.phone_number_id:
            raise ValueError("WHATSAPP_NOT_CONFIGURED")
        if not to.strip() or not body.strip():
            raise ValueError("WHATSAPP_RECIPIENT_AND_BODY_REQUIRED")
        url = f"{self.base_url}/{self.api_version}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.is_error:
            raise ValueError(f"WHATSAPP_SEND_FAILED: HTTP_{response.status_code}")
        data = response.json()
        messages = data.get("messages") or []
        if not messages or not messages[0].get("id"):
            raise ValueError("WHATSAPP_SEND_FAILED: PROVIDER_ID_MISSING")
        return SendResult({
            "status": "SENT",
            "channel": self.name,
            "recipient": to,
            "provider": "WHATSAPP",
            "provider_message_id": messages[0]["id"],
            "metadata": context or {},
        })

    async def health_check(self) -> bool:
        if not self.token or not self.phone_number_id:
            return False
        url = f"{self.base_url}/{self.api_version}/{self.phone_number_id}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    url,
                    params={"fields": "id,display_phone_number"},
                    headers={"Authorization": f"Bearer {self.token}"},
                )
            return response.is_success
        except httpx.HTTPError:
            return False

    def capabilities(self) -> list[str]:
        return ["whatsapp", "message", "business"]
