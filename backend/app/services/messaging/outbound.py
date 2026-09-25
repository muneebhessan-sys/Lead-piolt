from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OutboundMessage, OutboundMessageStatus

from .base import MessageProvider


class OutboundMessageService:
    """Persist outbound attempts and prevent duplicate sends by idempotency key."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(
        self,
        *,
        idempotency_key: str,
        channel: str,
        body: str,
        recipient: str = "",
        subject: str = "",
        lead_id: int | None = None,
        campaign_id: int | None = None,
        account_id: int | None = None,
    ) -> tuple[OutboundMessage, bool]:
        existing = self.db.scalar(
            select(OutboundMessage).where(OutboundMessage.idempotency_key == idempotency_key)
        )
        if existing is not None:
            return existing, False
        message = OutboundMessage(
            idempotency_key=idempotency_key,
            channel=channel,
            body=body,
            recipient=recipient,
            subject=subject,
            lead_id=lead_id,
            campaign_id=campaign_id,
            account_id=account_id,
            status=OutboundMessageStatus.PENDING,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message, True

    async def send_once(
        self,
        provider: MessageProvider,
        *,
        message: OutboundMessage,
        context: dict[str, Any] | None = None,
    ) -> OutboundMessage:
        if message.status in {
            OutboundMessageStatus.SENT,
            OutboundMessageStatus.DELIVERED,
        }:
            return message
        message.status = OutboundMessageStatus.SENDING
        self.db.commit()
        try:
            result = await provider.send(message.recipient, message.body, context)
            message.status = OutboundMessageStatus.SENT
            message.provider_message_id = str(result.get("provider_message_id", result.get("id", "")))
            message.sent_at = datetime.now(timezone.utc)
            message.error = ""
        except Exception as exc:
            message.status = OutboundMessageStatus.FAILED
            message.retry_count += 1
            message.error = str(exc)
        self.db.commit()
        self.db.refresh(message)
        return message
