import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.oauth.service import OAuthService
from app.services.oauth.state import StateManager


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class _FakeClient:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, data=None, json=None, headers=None):
        self.calls.append({"url": url, "data": data, "json": json, "headers": headers})
        return self._response


def _patch_httpx_client(fake_client):
    return mock.patch("httpx.Client", return_value=fake_client)


class OAuthServiceTests(unittest.TestCase):
    def setUp(self):
        StateManager._states.clear()
        OAuthService._token_cache.clear() if hasattr(OAuthService, "_token_cache") else None
        os.environ["GMAIL_CLIENT_ID"] = "test-gmail-id"
        os.environ["GMAIL_CLIENT_SECRET"] = "test-gmail-secret"
        self.service = OAuthService()

    def test_begin_authorization_generates_state_and_pkce(self):
        result = self.service.begin_authorization(
            "GMAIL",
            redirect_uri="https://example.com/cb",
        )
        self.assertIn("auth_url", result)
        self.assertIn("state", result)
        self.assertTrue(result["auth_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth"))
        self.assertIn("code_challenge=", result["auth_url"])
        self.assertIn("code_challenge_method=S256", result["auth_url"])
        self.assertIn("state=" + result["state"], result["auth_url"])
        self.assertIn("client_id=test-gmail-id", result["auth_url"])
        # state is stored
        stored = StateManager.validate(result["state"])
        self.assertIsNotNone(stored)
        self.assertEqual("GMAIL", stored["provider"])
        self.assertIn("code_verifier", stored)

    def test_begin_authorization_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            self.service.begin_authorization("UNKNOWN", redirect_uri="https://example.com/cb")

    def test_exchange_code_invalid_state_raises(self):
        with self.assertRaises(ValueError):
            self.service.exchange_code("GMAIL", "the-code", "bogus-state")

    def test_exchange_code_provider_mismatch_raises(self):
        state = StateManager.generate_state()
        StateManager.store(state, {"provider": "GOOGLE", "code_verifier": "v", "redirect_uri": "https://example.com/cb"})
        with self.assertRaises(ValueError):
            self.service.exchange_code("GMAIL", "the-code", state)

    def test_exchange_code_success(self):
        state = StateManager.generate_state()
        StateManager.store(state, {
            "provider": "GMAIL",
            "code_verifier": "the-verifier",
            "redirect_uri": "https://example.com/cb",
        })
        fake_response = _FakeResponse(200, {
            "access_token": "access-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh-456",
            "scope": "openid email",
        })
        fake_client = _FakeClient(fake_response)
        with _patch_httpx_client(fake_client):
            tokens = self.service.exchange_code("GMAIL", "the-code", state)

        self.assertEqual("access-123", tokens["access_token"])
        self.assertEqual("Bearer", tokens["token_type"])
        self.assertEqual(3600, tokens["expires_in"])
        self.assertEqual("refresh-456", tokens["refresh_token"])
        self.assertEqual("openid email", tokens["scope"])
        # verify request shape
        self.assertEqual(1, len(fake_client.calls))
        call = fake_client.calls[0]
        self.assertEqual("https://oauth2.googleapis.com/token", call["url"])
        self.assertEqual("the-code", call["data"]["code"])
        self.assertEqual("the-verifier", call["data"]["code_verifier"])
        self.assertEqual("test-gmail-id", call["data"]["client_id"])
        self.assertEqual("test-gmail-secret", call["data"]["client_secret"])

    def test_exchange_code_http_failure_raises(self):
        state = StateManager.generate_state()
        StateManager.store(state, {
            "provider": "GMAIL",
            "code_verifier": "the-verifier",
            "redirect_uri": "https://example.com/cb",
        })
        fake_response = _FakeResponse(500, {"error": "server_error"})
        fake_client = _FakeClient(fake_response)
        with _patch_httpx_client(fake_client):
            with self.assertRaises(ValueError):
                self.service.exchange_code("GMAIL", "the-code", state)

    def test_refresh_tokens_success(self):
        fake_response = _FakeResponse(200, {
            "access_token": "refreshed-access",
            "token_type": "Bearer",
            "expires_in": 3600,
        })
        fake_client = _FakeClient(fake_response)
        with _patch_httpx_client(fake_client):
            tokens = self.service.refresh_tokens("GMAIL", "old-refresh")

        self.assertEqual("refreshed-access", tokens["access_token"])
        self.assertEqual("old-refresh", tokens["refresh_token"])
        self.assertEqual("refresh_token", fake_client.calls[0]["data"]["grant_type"])

    def test_refresh_tokens_failure_raises(self):
        fake_client = _FakeClient(_FakeResponse(401, {"error": "invalid_grant"}))
        with _patch_httpx_client(fake_client):
            with self.assertRaises(ValueError):
                self.service.refresh_tokens("GMAIL", "old-refresh")

    def test_exchange_code_missing_fields_raises(self):
        state = StateManager.generate_state()
        StateManager.store(state, {
            "provider": "GMAIL",
            "code_verifier": "the-verifier",
            "redirect_uri": "https://example.com/cb",
        })
        fake_response = _FakeResponse(200, {"token_type": "Bearer"})
        fake_client = _FakeClient(fake_response)
        with _patch_httpx_client(fake_client):
            with self.assertRaises(ValueError):
                self.service.exchange_code("GMAIL", "the-code", state)

    def test_store_and_get_tokens_round_trip(self):
        tokens = {"access_token": "abc", "token_type": "Bearer", "refresh_token": "xyz"}
        self.service.store_tokens("user-1", "GMAIL", tokens)
        self.assertEqual(tokens, self.service.get_tokens("user-1", "GMAIL"))

    def test_get_tokens_missing_returns_none(self):
        self.assertIsNone(self.service.get_tokens("ghost", "GMAIL"))

    def test_get_provider_info(self):
        info = self.service.get_provider_info("GMAIL")
        self.assertEqual("GMAIL", info["name"])
        self.assertIn("openid", info["scopes"])
        self.assertTrue(info["pkce_required"])

    def test_list_providers(self):
        names = [p["name"] for p in self.service.list_providers()]
        self.assertIn("GMAIL", names)
        self.assertIn("GOOGLE", names)
        self.assertIn("META", names)
        self.assertIn("LINKEDIN", names)
        self.assertIn("X", names)
        self.assertIn("TIKTOK", names)


class TokenEncryptionTests(unittest.TestCase):
    def test_encrypted_token_round_trip(self):
        from cryptography.fernet import Fernet
        from app.services.security import SecretStore

        key = Fernet.generate_key().decode()
        store = SecretStore(key)
        payload = {"access_token": "secret-value", "refresh_token": "r"}
        import json
        encrypted = store.encrypt(json.dumps(payload))
        self.assertNotIn("secret-value", encrypted)
        decrypted = json.loads(store.decrypt(encrypted))
        self.assertEqual(payload, decrypted)

    def test_encrypted_token_is_not_plaintext(self):
        from cryptography.fernet import Fernet
        from app.services.security import SecretStore

        key = Fernet.generate_key().decode()
        store = SecretStore(key)
        encrypted = store.encrypt("my-secret-access-token")
        self.assertNotIn("my-secret-access-token", encrypted)
        self.assertEqual("my-secret-access-token", store.decrypt(encrypted))


if __name__ == "__main__":
    unittest.main()