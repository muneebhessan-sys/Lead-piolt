from __future__ import annotations

import httpx
from typing import Any

from .base import MessageProvider, SendResult


class SMSProvider(MessageProvider):
    name = "SMS"

    def __init__(self, provider_name: str = "twilio", api_key: str = "", account_sid: str = "", from_number: str = "", base_url: str = "https://api.twilio.com") -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self.account_sid = account_sid
        self.from_number = from_number
        self.base_url = base_url.rstrip("/")

    async def send(self, to: str, body: str, context: dict[str, Any] | None = None) -> SendResult:
        if self.provider_name.lower() != "twilio":
            raise ValueError("SMS_PROVIDER_UNSUPPORTED")
        if not self.account_sid or not self.api_key or not self.from_number:
            raise ValueError("SMS_NOT_CONFIGURED")
        if not to.strip() or not body.strip():
            raise ValueError("SMS_RECIPIENT_AND_BODY_REQUIRED")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                data={"To": to, "From": self.from_number, "Body": body},
                auth=(self.account_sid, self.api_key),
            )
        if response.is_error:
            raise ValueError(f"SMS_SEND_FAILED: HTTP_{response.status_code}")
        data = response.json()
        provider_id = data.get("sid")
        if not provider_id:
            raise ValueError("SMS_SEND_FAILED: PROVIDER_ID_MISSING")
        return SendResult({
            "status": "SENT",
            "channel": self.name,
            "recipient": to,
            "provider": self.provider_name,
            "provider_message_id": provider_id,
            "metadata": context or {},
        })

    async def health_check(self) -> bool:
        return bool(self.provider_name.lower() == "twilio" and self.account_sid and self.api_key and self.from_number)

    def capabilities(self) -> list[str]:
        return ["sms", "text"]
