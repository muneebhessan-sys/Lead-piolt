from __future__ import annotations

import httpx
from typing import Any

from app.config import settings
from app.services.oauth.providers import OAuthProvider, get_provider


_SAFE_PROFILE_FIELDS: dict[str, list[str]] = {
    "GMAIL": ["id", "email", "verified_email", "name", "given_name", "family_name", "picture"],
    "GOOGLE": ["id", "email", "verified_email", "name", "given_name", "family_name", "picture"],
    "META": ["id", "name", "email"],
    "LINKEDIN": ["id", "firstName", "lastName", "email"],
    "X": ["id", "name", "username", "email"],
    "TIKTOK": ["id", "displayName", "email"],
}


class SafeProfileFetcher:
    """Fetches OAuth provider profiles with only safe, non-sensitive fields returned."""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def fetch(
        self,
        provider_name: str,
        access_token: str,
    ) -> dict[str, Any]:
        """Retrieve a user's profile from a provider, filtering to safe fields only. No tokens or secrets are included."""
        provider = get_provider(provider_name)
        if provider is None:
            raise ValueError(f"UNKNOWN_PROVIDER: {provider_name}")
        raw = self._fetch_raw_profile(provider, access_token)
        safe_fields = _SAFE_PROFILE_FIELDS.get(provider_name, [])
        safe_profile = {key: raw.get(key) for key in safe_fields if key in raw}
        safe_profile["provider"] = provider_name
        return safe_profile

    def invalidate(self, provider_name: str) -> None:
        """Clear cached profile data for a provider."""
        self._cache.pop(provider_name, None)

    def _fetch_raw_profile(self, provider: OAuthProvider, access_token: str) -> dict[str, Any]:
        """Fetch the raw profile from the provider's user info endpoint, using cache."""
        cached = self._cache.get(provider.name)
        if cached is not None:
            return cached
        with httpx.Client(timeout=settings.request_timeout) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get(provider.user_info_url, headers=headers)
        if response.status_code >= 400:
            raise ValueError(f"PROFILE_FETCH_FAILED: HTTP {response.status_code}")
        raw = response.json()
        self._cache[provider.name] = raw
        return raw
