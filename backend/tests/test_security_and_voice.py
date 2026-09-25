import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from cryptography.fernet import Fernet

from app.config import Settings, settings
from app.main import create_admin_token, normalize_provider_name, require_admin
from app.models import VoiceAgentConfig
from app.services.google_places import GooglePlacesError, GooglePlacesProvider
from app.services.security import SecretStore
from app.services.voice import LocalVoiceAgentProvider


class SecretStoreTests(unittest.TestCase):
    def test_secret_round_trip(self):
        key = Fernet.generate_key().decode()
        store = SecretStore(key)
        secret = "token-value-123"
        encrypted = store.encrypt(secret)
        self.assertNotEqual(secret, encrypted)
        self.assertEqual(secret, store.decrypt(encrypted))
        self.assertIn("...", store.mask("super-long-secret-value"))

    def test_secret_key_is_stable_without_env(self):
        first = SecretStore("test-key")
        second = SecretStore("test-key")
        secret = "abc-123"
        self.assertEqual(secret, second.decrypt(first.encrypt(secret)))

    def test_voice_provider_status(self):
        config = VoiceAgentConfig(name="Local agent", base_url="http://localhost:9000", enabled=True)
        self.assertEqual("UNAVAILABLE", LocalVoiceAgentProvider(config).status)

    def test_admin_token_requires_valid_bearer(self):
        previous = settings.admin_auth_enabled
        settings.admin_auth_enabled = True
        self.addCleanup(setattr, settings, "admin_auth_enabled", previous)

        token = create_admin_token("admin")
        self.assertEqual("admin", require_admin(f"Bearer {token}")["username"])
        with self.assertRaises(HTTPException):
            require_admin("Bearer invalid-token")

    def test_provider_names_are_standardized(self):
        self.assertEqual("GOOGLE_PLACES", normalize_provider_name("google-places"))
        self.assertEqual("GMAIL", normalize_provider_name(" gmail "))

    def test_google_places_rejects_blank_queries(self):
        provider = GooglePlacesProvider("test-key")
        with self.assertRaises(GooglePlacesError):
            import asyncio
            asyncio.run(provider.search("   ", 3))

    def test_postgres_ready_settings_are_supported(self):
        cfg = Settings(
            database_url="postgresql://user:pass@localhost:5432/leadpilot",
            database_pool_size=8,
            database_max_overflow=20,
            database_pool_timeout=45,
        )
        self.assertEqual("postgresql://user:pass@localhost:5432/leadpilot", cfg.database_url)
        self.assertEqual(8, cfg.database_pool_size)
        self.assertEqual(20, cfg.database_max_overflow)
        self.assertEqual(45, cfg.database_pool_timeout)


if __name__ == "__main__":
    unittest.main()
