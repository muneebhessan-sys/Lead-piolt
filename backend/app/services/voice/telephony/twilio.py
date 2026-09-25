from __future__ import annotations

from app.config import settings


class TwilioTelephony:
    def __init__(self, account_sid: str = "", auth_token: str = "") -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token

    async def create_call(self, to: str, from_: str, url: str | None = None) -> str:
        if not settings.development_mode:
            raise NotImplementedError("TWILIO_TRANSPORT_NOT_IMPLEMENTED")
        return f"twilio-call-{to}-{from_}"

    async def get_call_status(self, call_id: str) -> str:
        return "queued"

    async def health_check(self) -> bool:
        return True
