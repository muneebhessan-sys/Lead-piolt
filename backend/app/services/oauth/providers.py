from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OAuthProvider:
    """OAuth provider configuration including authorization and token endpoints."""

    name: str
    auth_url: str
    token_url: str
    user_info_url: str
    scopes: list[str]
    pkce_required: bool = True
    client_id_env: str = ""
    redirect_uri: str = ""
    additional_auth_params: dict[str, str] = field(default_factory=dict)

    def authorize_url(
        self,
        client_id: str,
        redirect_uri: str,
        state: str,
        code_challenge: str,
        extra_scopes: list[str] | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> str:
        """Build the full authorization URL with PKCE challenge and state."""
        from urllib.parse import urlencode, urlparse, urlunparse

        scopes = list(self.scopes)
        if extra_scopes:
            scopes.extend(extra_scopes)
        params: dict[str, str] = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        params.update(self.additional_auth_params)
        if extra_params:
            params.update(extra_params)
        parsed = urlparse(self.auth_url)
        query = urlencode(params)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment))

    def token_exchange_params(
        self,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        """Return the POST body for exchanging an authorization code for tokens."""
        return {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }


class ProviderRegistry:
    """Registry of OAuth providers available in the application."""

    _providers: dict[str, OAuthProvider] = {}

    @classmethod
    def register(cls, provider: OAuthProvider) -> None:
        """Register a provider in the registry using its uppercase name as key."""
        cls._providers[provider.name.upper()] = provider

    @classmethod
    def get(cls, name: str) -> OAuthProvider | None:
        """Retrieve a registered provider by name (case-insensitive)."""
        return cls._providers.get(name.upper())

    @classmethod
    def list_names(cls) -> list[str]:
        """Return sorted list of registered provider names."""
        return sorted(cls._providers.keys())

    @classmethod
    def has(cls, name: str) -> bool:
        """Check whether a provider is registered by name (case-insensitive)."""
        return name.upper() in cls._providers


GITHUB_OAUTH_SCOPES = ["read:user", "user:email"]

GMAIL_PROVIDER = OAuthProvider(
    name="GMAIL",
    auth_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    user_info_url="https://www.googleapis.com/oauth2/v3/userinfo",
    scopes=["openid", "email", "profile", "https://www.googleapis.com/auth/gmail.send"],
    pkce_required=True,
    client_id_env="GMAIL_CLIENT_ID",
    redirect_uri="",
    additional_auth_params={"access_type": "offline", "prompt": "consent"},
)

GOOGLE_PROVIDER = OAuthProvider(
    name="GOOGLE",
    auth_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    user_info_url="https://www.googleapis.com/oauth2/v3/userinfo",
    scopes=["openid", "email", "profile"],
    pkce_required=True,
    client_id_env="GOOGLE_CLIENT_ID",
    redirect_uri="",
    additional_auth_params={"access_type": "offline", "prompt": "consent"},
)

META_PROVIDER = OAuthProvider(
    name="META",
    auth_url="https://www.facebook.com/v22.0/dialog/oauth",
    token_url="https://graph.facebook.com/v22.0/oauth/access_token",
    user_info_url="https://graph.facebook.com/me?fields=id,name,email",
    scopes=["email", "public_profile"],
    pkce_required=False,
    client_id_env="META_APP_ID",
    redirect_uri="",
    additional_auth_params={},
)

LINKEDIN_PROVIDER = OAuthProvider(
    name="LINKEDIN",
    auth_url="https://www.linkedin.com/oauth/v2/authorization",
    token_url="https://www.linkedin.com/oauth/v2/accessToken",
    user_info_url="https://api.linkedin.com/v2/userinfo",
    scopes=["openid", "profile", "email"],
    pkce_required=True,
    client_id_env="LINKEDIN_CLIENT_ID",
    redirect_uri="",
    additional_auth_params={},
)

X_PROVIDER = OAuthProvider(
    name="X",
    auth_url="https://twitter.com/i/oauth2/authorize",
    token_url="https://api.twitter.com/2/oauth2/token",
    user_info_url="https://api.twitter.com/2/users/me",
    scopes=["tweet.read", "users.read", "offline.access"],
    pkce_required=True,
    client_id_env="X_CLIENT_ID",
    redirect_uri="",
    additional_auth_params={"response_type": "code", "response_mode": "query"},
)

TIKTOK_PROVIDER = OAuthProvider(
    name="TIKTOK",
    auth_url="https://business-api.tiktok.com/open_api/v1.3/oauth/connect/",
    token_url="https://business-api.tiktok.com/open_api/v1.3/oauth/access_token/",
    user_info_url="https://business-api.tiktok.com/open_api/v1.3/user/info/",
    scopes=["user.info.basic", "user.info.account"],
    pkce_required=True,
    client_id_env="TIKTOK_CLIENT_ID",
    redirect_uri="",
    additional_auth_params={},
)

BUILT_IN_PROVIDERS = [GMAIL_PROVIDER, GOOGLE_PROVIDER, META_PROVIDER, LINKEDIN_PROVIDER, X_PROVIDER, TIKTOK_PROVIDER]

for _provider in BUILT_IN_PROVIDERS:
    ProviderRegistry.register(_provider)


def get_provider(name: str) -> OAuthProvider | None:
    """Convenience function to retrieve a registered provider by name."""
    return ProviderRegistry.get(name)
