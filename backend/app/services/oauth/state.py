from __future__ import annotations

import secrets
import time
from typing import Any


class StateManager:
    """In-memory OAuth state token store with TTL-based expiry for CSRF protection."""

    _states: dict[str, dict[str, Any]] = {}
    _ttl_seconds: float = 600.0

    @classmethod
    def generate_state(cls) -> str:
        """Generate a cryptographically secure random state token."""
        return secrets.token_urlsafe(32)

    @classmethod
    def store(cls, state: str, data: dict[str, Any]) -> None:
        """Store a state token with its associated data and expiry time."""
        ttl = max(0.0, cls._ttl_seconds)
        cls._states[state] = {"data": data, "expires_at": time.monotonic() + ttl}

    @classmethod
    def validate(cls, state: str) -> dict[str, Any] | None:
        """Validate and consume a state token; returns data if valid and not expired, None otherwise."""
        entry = cls._states.pop(state, None)
        if entry is None:
            return None
        if time.monotonic() >= entry["expires_at"]:
            return None
        return entry["data"]

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired state tokens and return the count removed."""
        now = time.monotonic()
        expired = [k for k, v in cls._states.items() if now >= v["expires_at"]]
        for key in expired:
            del cls._states[key]
        return len(expired)
