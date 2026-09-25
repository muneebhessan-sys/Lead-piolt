import asyncio
from unittest.mock import AsyncMock, patch

import httpx

from app.services.messaging.gmail import GmailProvider
from app.services.messaging.linkedin import LinkedInProvider
from app.services.messaging.sms import SMSProvider


def _client(payload=None, headers=None):
    client = AsyncMock()
    client.post.return_value = httpx.Response(
        200,
        json=payload or {},
        headers=headers or {},
        request=httpx.Request("POST", "https://provider.test/send"),
    )
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    return client


def test_gmail_real_transport():
    client = _client({"id": "gmail-message-1"})
    provider = GmailProvider(access_token="token", base_url="https://gmail.test")
    with patch("httpx.AsyncClient", return_value=client):
        result = asyncio.run(provider.send("lead@example.com", "Hello"))
    assert result["provider_message_id"] == "gmail-message-1"


def test_linkedin_real_transport():
    client = _client(headers={"x-restli-id": "linkedin-message-1"})
    provider = LinkedInProvider("token", base_url="https://linkedin.test", sender_urn="urn:li:person:sender")
    with patch("httpx.AsyncClient", return_value=client):
        result = asyncio.run(provider.send("urn:li:person:recipient", "Hello"))
    assert result["provider_message_id"] == "linkedin-message-1"


def test_sms_real_transport():
    client = _client({"sid": "SM123"})
    provider = SMSProvider("twilio", "auth-token", "AC123", "+15550000000", "https://twilio.test")
    with patch("httpx.AsyncClient", return_value=client):
        result = asyncio.run(provider.send("+15551111111", "Hello"))
    assert result["provider_message_id"] == "SM123"
