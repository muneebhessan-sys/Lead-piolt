import os
import sys
import unittest
from unittest import mock

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import VoiceAgentConfig
from app.services.voice.provider import LocalVoiceAgentProvider


class _FakeAsyncResponse:
    def __init__(self, status_code, payload=None, raise_exc=None):
        self.status_code = status_code
        self._payload = payload or {}
        self._raise_exc = raise_exc

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self._raise_exc is not None:
            raise self._raise_exc
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request("GET", "http://fake"),
                response=httpx.Response(self.status_code),
            )


class _FakeAsyncClient:
    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, headers=None, params=None):
        self.calls.append({"method": "GET", "url": url, "headers": headers})
        if self._exc:
            raise self._exc
        return self._response

    async def post(self, url, json=None, headers=None):
        self.calls.append({"method": "POST", "url": url, "json": json, "headers": headers})
        if self._exc:
            raise self._exc
        return self._response


def _configured():
    return LocalVoiceAgentProvider(VoiceAgentConfig(name="X", base_url="http://localhost:9000", enabled=True))


class VoiceStatusTests(unittest.TestCase):
    def test_not_configured_when_no_config(self):
        provider = LocalVoiceAgentProvider(None)
        self.assertEqual("NOT_CONFIGURED", provider.status)
        self.assertEqual([], provider.capabilities())

    def test_not_configured_when_disabled(self):
        config = VoiceAgentConfig(name="X", base_url="http://localhost:9000", enabled=False)
        provider = LocalVoiceAgentProvider(config)
        self.assertEqual("NOT_CONFIGURED", provider.status)

    def test_not_configured_when_blank_base_url(self):
        config = VoiceAgentConfig(name="X", base_url="", enabled=True)
        provider = LocalVoiceAgentProvider(config)
        self.assertEqual("NOT_CONFIGURED", provider.status)

    def test_unavailable_until_health_verified(self):
        provider = _configured()
        self.assertEqual("UNAVAILABLE", provider.status)
        self.assertEqual(["health", "call", "call_status", "capabilities"], provider.capabilities())


class VoiceHealthTests(unittest.TestCase):
    def test_health_returns_connected_when_ok(self):
        provider = _configured()
        fake = _FakeAsyncClient(response=_FakeAsyncResponse(200, {"status": "ok"}))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            import asyncio
            result = asyncio.run(provider.health())
        self.assertEqual("CONNECTED", result["status"])
        self.assertEqual("http://localhost:9000", result["base_url"])

    def test_health_returns_unavailable_on_failure(self):
        provider = _configured()
        fake = _FakeAsyncClient(response=_FakeAsyncResponse(503, {}, raise_exc=httpx.HTTPError("down")))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            import asyncio
            result = asyncio.run(provider.health())
        self.assertEqual("UNAVAILABLE", result["status"])
        self.assertIn("error", result)

    def test_health_unavailable_on_connection_error(self):
        provider = _configured()
        fake = _FakeAsyncClient(exc=httpx.ConnectError("connection refused"))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            import asyncio
            result = asyncio.run(provider.health())
        self.assertEqual("UNAVAILABLE", result["status"])

    def test_health_not_configured_raises(self):
        provider = LocalVoiceAgentProvider(None)
        with self.assertRaises(ValueError):
            import asyncio
            asyncio.run(provider.health())


class VoiceCallTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(LocalVoiceAgentProvider, "status",
                                    new_callable=mock.PropertyMock)
        self._status_mock = patcher.start()
        self._status_mock.return_value = LocalVoiceAgentProvider.CONNECTED
        self.addCleanup(patcher.stop)

    def test_start_call_success(self):
        provider = _configured()
        fake = _FakeAsyncClient(response=_FakeAsyncResponse(201, {"id": "call-abc", "status": "CONNECTED"}))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            import asyncio
            data = asyncio.run(provider.start_call(lead_id=42, caller_id="caller-1"))
        self.assertEqual("call-abc", data["id"])
        status = asyncio.run(provider.get_call_status("call-abc"))
        self.assertEqual("CONNECTED", status["status"])
        self.assertEqual("call-abc", status["call_id"])

    def test_start_call_failure_raises(self):
        provider = _configured()
        fake = _FakeAsyncClient(exc=httpx.ConnectError("network down"))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            with self.assertRaises(ValueError):
                import asyncio
                asyncio.run(provider.start_call(lead_id=1))

    def test_get_call_status_unknown_when_not_started(self):
        provider = _configured()
        fake = _FakeAsyncClient(response=_FakeAsyncResponse(200, {"status": "RINGING"}))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            import asyncio
            result = asyncio.run(provider.get_call_status("unknown-id"))
        self.assertEqual("RINGING", result["status"])
        self.assertEqual("unknown-id", result["call_id"])

    def test_get_call_status_http_error_returns_unknown(self):
        provider = _configured()
        fake = _FakeAsyncClient(response=_FakeAsyncResponse(500, {}, raise_exc=httpx.HTTPError("boom")))
        with mock.patch("httpx.AsyncClient", return_value=fake):
            import asyncio
            result = asyncio.run(provider.get_call_status("err-id"))
        self.assertEqual("UNKNOWN", result["status"])
        self.assertIn("error", result)

    def test_call_endpoint_url_uses_config_path(self):
        config = VoiceAgentConfig(name="X", base_url="http://host:8080/", call_path="/api/v1/calls/", enabled=True)
        provider = LocalVoiceAgentProvider(config)
        self.assertEqual("http://host:8080/api/v1/calls/", provider._call_endpoint())

    def test_health_endpoint_url_uses_config_path(self):
        config = VoiceAgentConfig(name="X", base_url="http://host:8080/", health_path="/status", enabled=True)
        provider = LocalVoiceAgentProvider(config)
        self.assertEqual("http://host:8080/status", provider._health_endpoint())


if __name__ == "__main__":
    unittest.main()