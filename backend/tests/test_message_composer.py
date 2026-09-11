import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.message_composer import MessageComposerEngine


class MessageComposerTests(unittest.TestCase):
    def test_compose_uses_profile_context(self):
        profile = SimpleNamespace(
            offer="SEO and lead generation",
            services="Local growth experiments",
            tone="Direct",
            cta="Book a 15-minute call",
            niche="home services",
            rules="Keep it specific and short.",
            do_not_say="Do not exaggerate claims.",
            personalization_rules="Reference the business niche and the offer.",
        )
        draft = MessageComposerEngine().compose(
            profile=profile,
            business_name="Acme Plumbing",
            evidence=["Public listing reviewed", "Website inspected"],
            service_summary="Localized lead generation strategy",
        )
        self.assertIn("Acme Plumbing", draft.subject)
        self.assertIn("Book a 15-minute call", draft.body)
        self.assertIn("home services", draft.body)
        self.assertIn("Public listing reviewed", draft.body)


if __name__ == "__main__":
    unittest.main()
