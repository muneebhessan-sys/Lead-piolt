from __future__ import annotations

import json
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.services.oauth.providers import OAuthProvider, ProviderRegistry, get_provider
from app.services.oauth.pkce import generate_code_challenge, generate_code_verifier
from app.services.oauth.state import StateManager
from app.services.security import secret_store
from app.models import Account, AccountStatus


class OAuthService:
    """Generic OAuth service handling authorization flows, token exchange, and encrypted persistence."""

    def __init__(self) -> None:
        self._token_cache: dict[str, dict[str, Any]] = {}

    def begin_authorization(
        self,
        provider_name: str,
        redirect_uri: str,
        extra_scopes: list[str] | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Start an OAuth flow by generating state, PKCE challenge, and authorization URL."""
        provider = self._require_provider(provider_name)
        state = StateManager.generate_state()
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        StateManager.store(state, {
            "provider": provider_name.upper(),
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
            "target_provider": (extra_params or {}).get("leadpilot_target", provider_name.upper()),
        })
        target = str((extra_params or {}).get("leadpilot_target", provider_name)).upper()
        if provider.name == "META":
            meta_scopes = {
                "WHATSAPP": ["business_management", "whatsapp_business_management", "whatsapp_business_messaging"],
                "INSTAGRAM": ["instagram_basic", "instagram_manage_messages", "pages_show_list"],
                "FACEBOOK": ["pages_show_list", "pages_read_engagement", "pages_manage_metadata", "pages_messaging"],
            }
            extra_scopes = list(dict.fromkeys((extra_scopes or []) + meta_scopes.get(target, [])))
        client_id = self._resolve_client_id(provider)
        auth_url = provider.authorize_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            extra_scopes=extra_scopes,
            extra_params=extra_params,
        )
        return {"auth_url": auth_url, "state": state}

    def exchange_code(
        self,
        provider_name: str,
        code: str,
        state: str,
        validated_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Exchange an authorization code for access and refresh tokens."""
        provider = self._require_provider(provider_name)
        stored = validated_state if validated_state is not None else StateManager.validate(state)
        if stored is None:
            raise ValueError("INVALID_OR_EXPIRED_STATE")
        if stored.get("provider") != provider_name:
            raise ValueError("STATE_PROVIDER_MISMATCH")
        code_verifier = stored["code_verifier"]
        redirect_uri = stored["redirect_uri"]
        client_id = self._resolve_client_id(provider)
        client_secret = self._resolve_client_secret(provider)
        token_response = self._fetch_token(provider, client_id, client_secret, code, redirect_uri, code_verifier)
        token_data = self._parse_token_response(token_response, provider_name)
        self._token_cache[f"{provider_name}:{client_id}"] = token_data
        return token_data

    def refresh_tokens(self, provider_name: str, refresh_token: str) -> dict[str, Any]:
        """Refresh an access token through the registered provider's real token endpoint."""
        if not refresh_token:
            raise ValueError("REFRESH_TOKEN_REQUIRED")
        provider = self._require_provider(provider_name)
        client_id = self._resolve_client_id(provider)
        client_secret = self._resolve_client_secret(provider)
        response = self._fetch_refresh_token(provider, client_id, client_secret, refresh_token)
        token_data = self._parse_token_response(response, provider_name)
        token_data["refresh_token"] = token_data.get("refresh_token") or refresh_token
        self._token_cache[f"{provider_name}:{client_id}"] = token_data
        return token_data

    def store_tokens(
        self,
        user_id: str,
        provider_name: str,
        tokens: dict[str, Any],
        db: Session | None = None,
        account_name: str | None = None,
        provider_user_id: str = "",
    ) -> None:
        """Encrypt OAuth tokens and persist them when a database session is supplied."""
        key = f"oauth_tokens:{user_id}:{provider_name}"
        self._token_cache[key] = tokens
        if db is None:
            return
        access_token = secret_store.encrypt(str(tokens.get("access_token", "")))
        refresh_token = secret_store.encrypt(str(tokens.get("refresh_token", "")))
        account_key = f"oauth:{provider_name.upper()}:{user_id}"
        account = db.scalar(select(Account).where(Account.email == account_key))
        if account is None:
            account = Account(
                email=account_key,
                name=account_name or user_id,
                provider=provider_name.upper(),
            )
            db.add(account)
        account.name = account_name or account.name
        account.provider = provider_name.upper()
        account.provider_user_id = provider_user_id
        account.access_token_encrypted = access_token
        account.refresh_token_encrypted = refresh_token
        account.status = AccountStatus.ACTIVE
        expires_in = tokens.get("expires_in")
        if expires_in is not None:
            from datetime import datetime, timedelta, timezone
            account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        db.commit()

    def get_tokens(self, user_id: str, provider_name: str, db: Session | None = None) -> dict[str, Any] | None:
        """Retrieve OAuth tokens from cache or decrypt them from the account database row."""
        key = f"oauth_tokens:{user_id}:{provider_name}"
        cached = self._token_cache.get(key)
        if cached is not None:
            return cached
        if db is None:
            return None
        account = db.scalar(select(Account).where(Account.email == f"oauth:{provider_name.upper()}:{user_id}"))
        if account is None or not account.access_token_encrypted:
            return None
        tokens = {
            "access_token": secret_store.decrypt(account.access_token_encrypted),
            "refresh_token": secret_store.decrypt(account.refresh_token_encrypted),
            "token_type": "Bearer",
        }
        self._token_cache[key] = tokens
        return tokens

    def get_provider_info(self, provider_name: str) -> dict[str, Any]:
        """Return configuration metadata for a registered provider."""
        provider = self._require_provider(provider_name)
        return {
            "name": provider.name,
            "scopes": provider.scopes,
            "pkce_required": provider.pkce_required,
            "auth_url": provider.auth_url,
            "token_url": provider.token_url,
        }

    def list_providers(self) -> list[dict[str, Any]]:
        """List all registered providers with their configuration metadata."""
        return [self.get_provider_info(name) for name in ProviderRegistry.list_names()]

    def _require_provider(self, provider_name: str) -> OAuthProvider:
        """Return the provider or raise if not registered."""
        provider = get_provider(provider_name)
        if provider is None:
            raise ValueError(f"UNKNOWN_PROVIDER: {provider_name}")
        return provider

    def _resolve_client_id(self, provider: OAuthProvider) -> str:
        """Resolve the OAuth client ID from the provider's configured environment variable."""
        env_var = provider.client_id_env
        if not env_var:
            raise ValueError(f"No client_id_env configured for {provider.name}")
        import os
        setting_name = env_var.lower()
        value = os.environ.get(env_var, "") or str(getattr(settings, setting_name, ""))
        if not value:
            raise ValueError(f"Missing required env var {env_var} for provider {provider.name}")
        return value

    def _resolve_client_secret(self, provider: OAuthProvider) -> str:
        """Resolve the OAuth client secret from the corresponding environment variable."""
        env_var = provider.client_secret_env
        if not env_var:
            raise ValueError(f"No client_secret_env configured for {provider.name}")
        import os
        setting_name = env_var.lower()
        value = os.environ.get(env_var, "") or str(getattr(settings, setting_name, ""))
        return value

    def _fetch_token(
        self,
        provider: OAuthProvider,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        """Perform the token exchange HTTP POST against the provider's token endpoint."""
        body = provider.token_exchange_params(client_id, client_secret, code, redirect_uri, code_verifier)
        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.post(provider.token_url, data=body)
        if response.status_code >= 400:
            raise ValueError(f"TOKEN_EXCHANGE_FAILED: HTTP {response.status_code}")
        return response.json()

    def _fetch_refresh_token(
        self,
        provider: OAuthProvider,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        body = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.post(provider.token_url, data=body)
        if response.status_code >= 400:
            raise ValueError(f"TOKEN_REFRESH_FAILED: HTTP {response.status_code}")
        return response.json()

    def _parse_token_response(self, token_response: dict[str, Any], provider_name: str) -> dict[str, Any]:
        """Validate and normalize the token exchange response."""
        required_keys = {"access_token", "token_type"}
        missing = required_keys - set(token_response.keys())
        if missing:
            raise ValueError(f"MISSING_TOKEN_FIELDS: {', '.join(sorted(missing))}")
        return {
            "access_token": token_response["access_token"],
            "token_type": token_response["token_type"],
            "expires_in": token_response.get("expires_in"),
            "refresh_token": token_response.get("refresh_token"),
            "scope": token_response.get("scope", ""),
        }

