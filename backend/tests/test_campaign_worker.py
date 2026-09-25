import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workers.dispatcher import CampaignDispatcher


def _register(campaign_id=1, channel="EMAIL", sender="sender@example.com"):
    dispatcher = CampaignDispatcher()
    dispatcher.register_campaign(campaign_id, "Test Campaign", sender, channel=channel)
    return dispatcher


class CampaignLifecycleTests(unittest.TestCase):
    def test_register_defaults_to_pending(self):
        dispatcher = _register()
        campaign = dispatcher.get_campaign(1)
        self.assertEqual("PENDING", campaign["status"])
        self.assertEqual("EMAIL", campaign["channel"])
        self.assertIsNone(campaign["started_at"])

    def test_get_missing_campaign_returns_none(self):
        dispatcher = CampaignDispatcher()
        self.assertIsNone(dispatcher.get_campaign(999))

    def test_list_campaigns_returns_all(self):
        dispatcher = _register(1)
        dispatcher.register_campaign(2, "Second", "sender@example.com")
        self.assertEqual(2, len(dispatcher.list_campaigns()))


class CampaignDispatchTests(unittest.TestCase):
    def _success_send(self, *args, **kwargs):
        return {"success": True, "status": "SENT", "provider_reference": "ref-1"}

    def _fail_send(self, *args, **kwargs):
        return {"success": False, "error": "GMAIL_SEND_FAILED"}

    def test_dispatch_all_success(self):
        dispatcher = _register()
        items = [
            {"recipient": "a@x.com", "subject": "Hi", "content": "Hello"},
            {"recipient": "b@x.com", "subject": "Hi", "content": "Hello"},
        ]
        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=self._success_send):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(2, result["sent"])
        self.assertEqual(0, result["failed"])

    def test_dispatch_partial_failure_still_completes(self):
        dispatcher = _register()
        items = [
            {"recipient": "a@x.com", "subject": "Hi", "content": "Hello"},
            {"recipient": "b@x.com", "subject": "Hi", "content": "Hello"},
        ]
        calls = {"count": 0}

        def alternating(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                return self._success_send()
            return self._fail_send()

        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=alternating):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(1, result["sent"])
        self.assertEqual(1, result["failed"])

    def test_dispatch_cannot_run_when_completed(self):
        dispatcher = _register()
        dispatcher.get_campaign(1)["status"] = "COMPLETED"
        with self.assertRaises(ValueError):
            dispatcher.dispatch(1, [{"recipient": "a@x.com", "subject": "Hi", "content": "Hello"}])

    def test_dispatch_cannot_run_when_failed(self):
        dispatcher = _register()
        dispatcher.get_campaign(1)["status"] = "FAILED"
        with self.assertRaises(ValueError):
            dispatcher.dispatch(1, [{"recipient": "a@x.com", "subject": "Hi", "content": "Hello"}])

    def test_dispatch_unsupported_channel_fails_item(self):
        dispatcher = _register(channel="SMS")
        items = [{"recipient": "a@x.com", "subject": "Hi", "content": "Hello"}]
        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=self._success_send):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(0, result["sent"])
        self.assertEqual(1, result["failed"])
        self.assertTrue(any("Unsupported channel" in f.get("error", "") for f in result["failures"]))


class CampaignPauseResumeTests(unittest.TestCase):
    def test_pause_requires_running(self):
        dispatcher = _register()
        with self.assertRaises(ValueError):
            dispatcher.pause(1)

    def test_pause_then_resume(self):
        dispatcher = _register()
        dispatcher.get_campaign(1)["status"] = "RUNNING"
        pause_result = dispatcher.pause(1)
        self.assertEqual("PAUSED", pause_result["status"])
        self.assertIsNotNone(dispatcher.get_campaign(1)["paused_at"])

        resume_result = dispatcher.resume(1)
        self.assertEqual("RUNNING", resume_result["status"])
        self.assertIsNone(dispatcher.get_campaign(1)["paused_at"])

    def test_resume_requires_paused(self):
        dispatcher = _register()
        dispatcher.get_campaign(1)["status"] = "RUNNING"
        with self.assertRaises(ValueError):
            dispatcher.resume(1)

    def test_dispatch_stops_at_pause_boundary(self):
        dispatcher = _register()
        items = [
            {"recipient": "a@x.com", "subject": "Hi", "content": "Hello"},
            {"recipient": "b@x.com", "subject": "Hi", "content": "Hello"},
            {"recipient": "c@x.com", "subject": "Hi", "content": "Hello"},
        ]
        send_calls = {"count": 0}

        def slow_send(*args, **kwargs):
            send_calls["count"] += 1
            if send_calls["count"] == 1:
                dispatcher.pause(1)
            return {"success": True, "status": "SENT", "provider_reference": "ref"}

        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=slow_send):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("PAUSED", result["status"])
        self.assertEqual(1, result["sent"])

    def test_dispatch_stops_at_stop_boundary(self):
        dispatcher = _register()
        items = [
            {"recipient": "a@x.com", "subject": "Hi", "content": "Hello"},
            {"recipient": "b@x.com", "subject": "Hi", "content": "Hello"},
        ]
        send_calls = {"count": 0}

        def slow_send(*args, **kwargs):
            send_calls["count"] += 1
            if send_calls["count"] == 1:
                dispatcher.stop(1)
            return {"success": True, "status": "SENT", "provider_reference": "ref"}

        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=slow_send):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("STOPPED", result["status"])
        self.assertEqual(1, result["sent"])

    def test_stop_allows_pending(self):
        dispatcher = _register()
        result = dispatcher.stop(1)
        self.assertEqual("STOPPED", result["status"])


class CampaignRetryTests(unittest.TestCase):
    def test_retry_succeeds_after_failures(self):
        dispatcher = _register()
        items = [{"recipient": "a@x.com", "subject": "Hi", "content": "Hello"}]
        attempts = {"count": 0}

        def flaky_send(*args, **kwargs):
            attempts["count"] += 1
            if attempts["count"] < 3:
                return {"success": False, "error": f"fail-{attempts['count']}"}
            return {"success": True, "status": "SENT", "provider_reference": "ref"}

        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=flaky_send), \
             mock.patch("time.sleep"):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(1, result["sent"])
        self.assertEqual(3, attempts["count"])

    def test_retry_exhausts_and_item_fails(self):
        dispatcher = _register()
        items = [{"recipient": "a@x.com", "subject": "Hi", "content": "Hello"}]

        def always_fail(*args, **kwargs):
            return {"success": False, "error": "permanent"}

        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=always_fail), \
             mock.patch("time.sleep"):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(0, result["sent"])
        self.assertEqual(1, result["failed"])

    def test_retry_on_exception(self):
        dispatcher = _register()
        items = [{"recipient": "a@x.com", "subject": "Hi", "content": "Hello"}]
        attempts = {"count": 0}

        def raising_send(*args, **kwargs):
            attempts["count"] += 1
            raise RuntimeError("boom")

        with mock.patch("workers.dispatcher.send_gmail_safe", side_effect=raising_send), \
             mock.patch("time.sleep"):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(0, result["sent"])
        self.assertEqual(1, result["failed"])
        self.assertEqual(3, attempts["count"])

    def test_dry_run_skips_network(self):
        dispatcher = _register()
        items = [{"recipient": "a@x.com", "subject": "Hi", "content": "Hello"}]
        with mock.patch("workers.dispatcher.send_gmail_safe", return_value={
            "success": True, "status": "DRY_RUN", "provider_reference": "dry", "message": "dry"
        }):
            result = dispatcher.dispatch(1, items)
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(1, result["sent"])


if __name__ == "__main__":
    unittest.main()