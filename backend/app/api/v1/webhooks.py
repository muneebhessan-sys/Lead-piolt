from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import OutboundMessage, OutboundMessageStatus

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


def _message_update(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    candidates = [payload.get("provider_message_id"), payload.get("message_id"), payload.get("id"), payload.get("sid")]
    status = str(payload.get("status") or payload.get("event") or "").upper()
    if not status:
        status = str(payload.get("message", {}).get("status", "")).upper()
    statuses = {
        "SENT": OutboundMessageStatus.SENT,
        "SENDING": OutboundMessageStatus.SENDING,
        "DELIVERED": OutboundMessageStatus.DELIVERED,
        "DELIVERY": OutboundMessageStatus.DELIVERED,
        "READ": OutboundMessageStatus.DELIVERED,
        "FAILED": OutboundMessageStatus.FAILED,
        "FAILURE": OutboundMessageStatus.FAILED,
        "BOUNCED": OutboundMessageStatus.BOUNCED,
    }
    normalized = statuses.get(status)
    return next((str(value) for value in candidates if value), None), normalized.value if normalized else None


@router.post("/{provider}")
async def messaging_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "") or request.headers.get("X-LeadPilot-Signature", "")
    if settings.webhook_signing_secret:
        expected = "sha256=" + hmac.new(settings.webhook_signing_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="INVALID_WEBHOOK_SIGNATURE")
    elif not settings.development_mode:
        raise HTTPException(status_code=503, detail="WEBHOOK_SIGNING_SECRET_NOT_CONFIGURED")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="INVALID_WEBHOOK_JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="WEBHOOK_PAYLOAD_MUST_BE_OBJECT")
    provider_message_id, status = _message_update(payload)
    if not provider_message_id or not status:
        raise HTTPException(status_code=422, detail="WEBHOOK_MESSAGE_ID_AND_STATUS_REQUIRED")
    message = db.query(OutboundMessage).filter(
        OutboundMessage.provider_message_id == provider_message_id,
        OutboundMessage.channel == provider.strip().upper(),
    ).one_or_none()
    if message is None:
        raise HTTPException(status_code=404, detail="OUTBOUND_MESSAGE_NOT_FOUND")
    message.status = OutboundMessageStatus(status)
    if status == OutboundMessageStatus.DELIVERED.value:
        message.delivered_at = datetime.now(timezone.utc)
    db.commit()
    return {"provider": provider.upper(), "message_id": message.id, "status": message.status.value}
