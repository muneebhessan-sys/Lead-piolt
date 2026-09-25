import asyncio
from unittest.mock import AsyncMock, patch

import httpx

from app.services.voice.telephony.pbx_provider import AsteriskPbxProvider


def test_asterisk_call_requires_real_provider_id():
    client = AsyncMock()
    client.post.return_value = httpx.Response(200, json={}, request=httpx.Request("POST", "http://pbx/ari/channels"))
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    provider = AsteriskPbxProvider("http://pbx", "user", "pass")
    with patch("httpx.AsyncClient", return_value=client):
        try:
            asyncio.run(provider.create_call("PJSIP/100", "+1555", "leadpilot"))
        except ValueError as exc:
            assert "CALL_ID_MISSING" in str(exc)
        else:
            raise AssertionError("missing call ID must fail")


def test_asterisk_call_returns_real_id():
    client = AsyncMock()
    client.post.return_value = httpx.Response(200, json={"id": "channel-1"}, request=httpx.Request("POST", "http://pbx/ari/channels"))
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    provider = AsteriskPbxProvider("http://pbx", "user", "pass")
    with patch("httpx.AsyncClient", return_value=client):
        assert asyncio.run(provider.create_call("PJSIP/100", "+1555", "leadpilot")) == "channel-1"
