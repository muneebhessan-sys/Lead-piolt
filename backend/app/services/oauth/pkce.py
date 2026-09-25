from __future__ import annotations

import hashlib
import secrets
import base64


def generate_code_verifier(length: int = 64) -> str:
    """Generate a cryptographically random PKCE code verifier (43-128 characters)."""
    if length < 43 or length > 128:
        raise ValueError("code_verifier length must be between 43 and 128 characters")
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode("ascii").rstrip("=")


def generate_code_challenge(verifier: str) -> str:
    """Derive a PKCE S256 code challenge from a code verifier."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
