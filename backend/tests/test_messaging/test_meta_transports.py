import asyncio
from unittest.mock import AsyncMock, patch

import httpx

from app.services.messaging.facebook import FacebookProvider
from app.services.messaging.instagram import InstagramProvider


def _client(payload):
    client = AsyncMock()
    client.post.return_value = httpx.Response(
        200,
        json=payload,
        request=httpx.Request("POST", "https://graph.test/messages"),
    )
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    return client


def test_instagram_real_transport_returns_message_id():
    client = _client({"message_id": "ig-message-1"})
    provider = InstagramProvider("token", "ig-account", base_url="https://graph.test")
    with patch("httpx.AsyncClient", return_value=client):
        result = asyncio.run(provider.send("recipient", "hello"))
    assert result["provider_message_id"] == "ig-message-1"
    client.post.assert_awaited_once()


def test_facebook_real_transport_returns_message_id():
    client = _client({"message_id": "fb-message-1"})
    provider = FacebookProvider("token", base_url="https://graph.test")
    with patch("httpx.AsyncClient", return_value=client):
        result = asyncio.run(provider.send("recipient", "hello"))
    assert result["provider_message_id"] == "fb-message-1"
    client.post.assert_awaited_once()
