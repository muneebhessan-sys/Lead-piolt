import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.oauth.pkce import generate_code_challenge, generate_code_verifier
from app.services.oauth.state import StateManager


class PkceTests(unittest.TestCase):
    def test_code_verifier_length_bounds(self):
        for length in (43, 64, 128):
            verifier = generate_code_verifier(length)
            # base64url-encoding expands bytes; the underlying byte length must match
            import base64
            raw = base64.urlsafe_b64decode(verifier + "=" * (-len(verifier) % 4))
            self.assertEqual(length, len(raw))
            self.assertGreaterEqual(len(verifier), 43)

    def test_code_verifier_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            generate_code_verifier(10)
        with self.assertRaises(ValueError):
            generate_code_verifier(200)

    def test_code_verifier_is_urlsafe_base64_without_padding(self):
        verifier = generate_code_verifier(64)
        self.assertNotIn("=", verifier)
        self.assertNotIn("+", verifier)
        self.assertNotIn("/", verifier)

    def test_code_challenge_is_sha256_of_verifier(self):
        import base64
        import hashlib

        verifier = generate_code_verifier(64)
        challenge = generate_code_challenge(verifier)
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")
        self.assertEqual(challenge, expected)

    def test_code_challenge_changes_with_verifier(self):
        v1 = generate_code_verifier(64)
        v2 = generate_code_verifier(64)
        self.assertNotEqual(v1, v2)
        self.assertNotEqual(generate_code_challenge(v1), generate_code_challenge(v2))


class StateManagerTests(unittest.TestCase):
    def setUp(self):
        StateManager._states.clear()

    def test_generate_state_is_random_and_long(self):
        s1 = StateManager.generate_state()
        s2 = StateManager.generate_state()
        self.assertNotEqual(s1, s2)
        self.assertGreaterEqual(len(s1), 32)

    def test_store_and_validate_round_trip(self):
        StateManager.store("state-1", {"provider": "GMAIL", "code_verifier": "abc"})
        data = StateManager.validate("state-1")
        self.assertEqual({"provider": "GMAIL", "code_verifier": "abc"}, data)

    def test_validate_unknown_state_returns_none(self):
        self.assertIsNone(StateManager.validate("does-not-exist"))

    def test_validate_is_single_use(self):
        StateManager.store("state-2", {"foo": "bar"})
        first = StateManager.validate("state-2")
        second = StateManager.validate("state-2")
        self.assertEqual({"foo": "bar"}, first)
        self.assertIsNone(second)

    def test_expired_state_returns_none(self):
        StateManager._ttl_seconds = 0.0
        self.addCleanup(setattr, StateManager, "_ttl_seconds", 600.0)
        StateManager.store("state-3", {"x": 1})
        import time
        time.sleep(0.01)
        self.assertIsNone(StateManager.validate("state-3"))

    def test_cleanup_expired_removes_only_expired(self):
        StateManager._ttl_seconds = 0.0
        self.addCleanup(setattr, StateManager, "_ttl_seconds", 600.0)
        StateManager.store("expired-1", {"a": 1})
        StateManager.store("expired-2", {"b": 2})
        import time
        time.sleep(0.01)
        removed = StateManager.cleanup_expired()
        self.assertEqual(2, removed)
        self.assertEqual(0, len(StateManager._states))


if __name__ == "__main__":
    unittest.main()