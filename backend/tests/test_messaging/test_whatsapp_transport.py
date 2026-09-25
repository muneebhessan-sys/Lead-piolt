import asyncio
from unittest.mock import AsyncMock, patch

import httpx

from app.services.messaging.whatsapp import WhatsAppProvider


def test_whatsapp_sends_real_graph_request_and_returns_provider_id():
    response = httpx.Response(
        200,
        json={"messages": [{"id": "wamid.test"}]},
        request=httpx.Request("POST", "https://graph.test/v20.0/phone/messages"),
    )
    client = AsyncMock()
    client.post.return_value = response
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False

    provider = WhatsAppProvider(
        token="secret",
        phone_number_id="phone",
        base_url="https://graph.test",
    )
    with patch("httpx.AsyncClient", return_value=client):
        result = asyncio.run(provider.send("15550000000", "Hello"))

    assert result["status"] == "SENT"
    assert result["provider_message_id"] == "wamid.test"
    client.post.assert_awaited_once()


def test_whatsapp_rejects_provider_response_without_message_id():
    response = httpx.Response(
        200,
        json={"messages": []},
        request=httpx.Request("POST", "https://graph.test/messages"),
    )
    client = AsyncMock()
    client.post.return_value = response
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False

    provider = WhatsAppProvider(token="secret", phone_number_id="phone", base_url="https://graph.test")
    with patch("httpx.AsyncClient", return_value=client):
        try:
            asyncio.run(provider.send("15550000000", "Hello"))
        except ValueError as exc:
            assert "PROVIDER_ID_MISSING" in str(exc)
        else:
            raise AssertionError("missing provider ID must fail")
