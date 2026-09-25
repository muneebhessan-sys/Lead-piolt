import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.message_engine.guardrails import (
    DEFAULT_CONFIG,
    GuardrailConfig,
    count_emojis,
    count_exclamations,
    count_links,
    sanitize_draft,
    validate_draft,
)
from app.services.message_engine.synonyms import (
    SYNONYM_GROUPS,
    get_available_keys,
    rewrite_with_synonyms,
    select_synonym,
    select_synonyms,
)

EMOJI_SAMPLE = "\U0001f44d"  # thumbs up
CELEBRATION_EMOJI = "\U0001f389"  # party popper


class SynonymDeterminismTests(unittest.TestCase):
    def test_select_synonym_is_deterministic_for_same_lead(self):
        first = select_synonym(lead_id=42, key="opportunity")
        second = select_synonym(lead_id=42, key="opportunity")
        self.assertEqual(first, second)

    def test_select_synonym_returns_known_option(self):
        word = select_synonym(lead_id=7, key="reach out")
        self.assertIn(word, [opt[0] for opt in SYNONYM_GROUPS["reach out"]])

    def test_select_synonym_unknown_key_returns_key(self):
        self.assertEqual("nonsense", select_synonym(lead_id=1, key="nonsense"))

    def test_select_synonyms_batch_is_deterministic(self):
        keys = ["opportunity", "business", "reach out", "interested"]
        first = select_synonyms(lead_id=99, keys=keys)
        second = select_synonyms(lead_id=99, keys=keys)
        self.assertEqual(first, second)
        self.assertEqual(set(keys), set(first.keys()))

    def test_rewrite_with_synonyms_preserves_structure(self):
        text = "I want to reach out about this opportunity for your business."
        rewritten = rewrite_with_synonyms(lead_id=5, text=text)
        self.assertIsInstance(rewritten, str)
        self.assertGreater(len(rewritten), 0)

    def test_rewrite_with_synonyms_is_deterministic(self):
        text = "quick strategy to improve lead results"
        self.assertEqual(rewrite_with_synonyms(1, text), rewrite_with_synonyms(1, text))

    def test_get_available_keys_lists_all_groups(self):
        keys = get_available_keys()
        self.assertEqual(sorted(SYNONYM_GROUPS.keys()), keys)
        self.assertIn("opportunity", keys)
        self.assertIn("reach out", keys)


class GuardrailValidationTests(unittest.TestCase):
    def test_valid_draft_passes(self):
        body = "Hi there, I noticed your business and wanted to reach out about a focused opportunity. Best regards."
        result = validate_draft("Professional outreach", body)
        self.assertTrue(result.is_valid)
        self.assertEqual([], result.violations)

    def test_banned_phrase_rejected(self):
        body = "This is a guaranteed result for your business and we promise success."
        result = validate_draft("Subject", body)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("guaranteed" in v for v in result.violations))
        self.assertTrue(any("guarantee" in v for v in result.violations))

    def test_spam_keyword_rejected(self):
        body = "Make money fast with our bitcoin investment scheme today."
        result = validate_draft("Subject", body)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("bitcoin investment" in v for v in result.violations))

    def test_do_not_say_violation(self):
        body = "We will exaggerate your results beyond belief."
        result = validate_draft("Subject", body, do_not_say="exaggerate, lie")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("exaggerate" in v for v in result.violations))

    def test_subject_length_violation(self):
        subject = "X" * (DEFAULT_CONFIG.max_subject_length + 10)
        result = validate_draft(subject, "A" * 200)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Subject exceeds" in v for v in result.violations))

    def test_body_too_short_violation(self):
        result = validate_draft("OK", "short")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("below minimum" in v for v in result.violations))

    def test_emoji_limit_violation(self):
        body = "Hello" + EMOJI_SAMPLE * (DEFAULT_CONFIG.max_emoji_count + 5) + " world"
        result = validate_draft("Subject", body)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Emoji count" in v for v in result.violations))

    def test_link_limit_violation(self):
        body = "See http://a.com and http://b.com and http://c.com please"
        result = validate_draft("Subject", body)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Link count" in v for v in result.violations))

    def test_exclamation_limit_violation(self):
        body = "Wow!!! Amazing!!! Great!!!"
        result = validate_draft("Subject", body)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("exclamation" in v for v in result.violations))

    def test_capitalization_violation(self):
        body = "THIS IS ALL CAPS WORDS AND MORE ALL CAPS HERE"
        result = validate_draft("Subject", body)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("capitalization" in v for v in result.violations))

    def test_custom_guardrail_config(self):
        cfg = GuardrailConfig(max_subject_length=5, max_body_length=10)
        result = validate_draft("Too long subject", "Also too long body text", config=cfg)
        self.assertFalse(result.is_valid)

    def test_warning_for_approaching_limit(self):
        long_subject = "subject line " * int((DEFAULT_CONFIG.max_subject_length * 0.9) / 13)
        result = validate_draft(long_subject, "a" * 200)
        self.assertTrue(result.is_valid)
        self.assertTrue(any("approaching" in w for w in result.warnings))

    def test_helpers_count_correctly(self):
        self.assertEqual(3, count_emojis("a " + EMOJI_SAMPLE + " b " + CELEBRATION_EMOJI + " c " + EMOJI_SAMPLE))
        self.assertEqual(3, count_exclamations("Wow!! Yes!"))
        self.assertEqual(2, count_links("see http://a.com and www.b.com"))


class SanitizeDraftTests(unittest.TestCase):
    def test_strips_emojis_and_truncates(self):
        subject, body = sanitize_draft(
            "X" * 200 + EMOJI_SAMPLE,
            "Y" * 4000 + CELEBRATION_EMOJI,
        )
        self.assertLessEqual(len(subject), DEFAULT_CONFIG.max_subject_length)
        self.assertLessEqual(len(body), DEFAULT_CONFIG.max_body_length)
        self.assertNotIn(EMOJI_SAMPLE, subject)
        self.assertNotIn(CELEBRATION_EMOJI, body)

    def test_does_not_mutate_within_limits(self):
        subject, body = sanitize_draft("Short subject", "A" * 200)
        self.assertEqual("Short subject", subject)
        self.assertEqual("A" * 200, body)


if __name__ == "__main__":
    unittest.main()