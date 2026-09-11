from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


class SecretStore:
    def __init__(self, key: str | None = None):
        configured_key = (key or settings.token_encryption_key or "leadpilot-local-dev-key-please-set-env-token_encryption_key").strip()
        digest = hashlib.sha256(configured_key.encode("utf-8")).digest()
        fernet_key = base64.urlsafe_b64encode(digest)
        self._fernet = Fernet(fernet_key)

    def encrypt(self, value: str) -> str:
        if not value:
            return ""
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        if not value:
            return ""
        return self._fernet.decrypt(value.encode()).decode()

    def mask(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 4:
            return "****"
        return f"{value[:2]}...{value[-2:]}"


secret_store = SecretStore()
