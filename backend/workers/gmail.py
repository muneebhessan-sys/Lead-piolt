from __future__ import annotations

import base64
from typing import Any

import httpx

from app.config import settings
from app.services.security import secret_store


def _get_gmail_token() -> str:
    """Retrieve the decrypted Gmail OAuth token from the database via SecretStore."""
    import os
    from app.database import SessionLocal
    from app.models import Integration

    db = SessionLocal()
    try:
        item = db.query(Integration).filter_by(provider="GMAIL").first()
        if not item or not item.secret_value:
            raise ValueError("GMAIL_NOT_CONFIGURED")
        return secret_store.decrypt(item.secret_value)
    finally:
        db.close()


def _is_retryable(status_code: int) -> bool:
    """Determine whether an HTTP status code warrants a retry."""
    return status_code in {429, 500, 502, 503, 504}


def send_gmail_safe(
    sender_account: str,
    recipient: str,
    subject: str,
    content: str,
) -> dict[str, Any]:
    """Send an email via Gmail API with retry/backoff, dry-run support, and safe error handling. Never fabricates success."""
    if settings.dry_run:
        return {
            "success": True,
            "status": "DRY_RUN",
            "provider_reference": f"dry_run_{sender_account}_{recipient}",
            "message": "Dry run: message not actually sent",
        }

    raw_message = f"To: {recipient}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{content}"
    encoded = base64.urlsafe_b64encode(raw_message.encode("utf-8")).decode("ascii")
    token = _get_gmail_token()

    max_retries = 3
    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            response = _post_gmail(token, encoded)
            if response.status_code == 401 or response.status_code == 403:
                return {"success": False, "error": "GMAIL_AUTHENTICATION_FAILED", "status_code": response.status_code}
            if _is_retryable(response.status_code):
                last_error = f"GMAIL_TRANSIENT_ERROR_HTTP_{response.status_code}"
                wait = 2 ** attempt
                import time
                time.sleep(min(wait, 60.0))
                continue
            response.raise_for_status()
            data = response.json()
            return {"success": True, "status": "SENT", "provider_reference": data.get("id", ""), "message": data}
        except httpx.HTTPError as exc:
            last_error = str(exc)
            if attempt < max_retries:
                wait = 2 ** attempt
                import time
                time.sleep(min(wait, 60.0))
                continue
        except Exception as exc:
            last_error = str(exc)
            if attempt < max_retries:
                wait = 2 ** attempt
                import time
                time.sleep(min(wait, 60.0))
                continue

    return {"success": False, "error": last_error or "GMAIL_SEND_FAILED", "retries": max_retries}


def _post_gmail(token: str, encoded_message: str) -> httpx.Response:
    """POST an encoded raw message to the Gmail send endpoint."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {"raw": encoded_message}
    client = httpx.Client(timeout=settings.request_timeout)
    try:
        response = client.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers=headers, json=body)
        return response
    finally:
        client.close()
