import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cryptography.fernet import Fernet

from app.models import VoiceAgentConfig
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
        self.assertEqual("CONNECTED", LocalVoiceAgentProvider(config).status)


if __name__ == "__main__":
    unittest.main()
