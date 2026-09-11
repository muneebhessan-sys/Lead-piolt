from __future__ import annotations

from cryptography.fernet import Fernet

from app.config import settings


class SecretStore:
    def __init__(self, key: str | None = None):
        configured_key = (key or settings.token_encryption_key or "").strip()
        if not configured_key:
            configured_key = Fernet.generate_key().decode()
        self._fernet = Fernet(configured_key.encode() if isinstance(configured_key, str) else configured_key)

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
