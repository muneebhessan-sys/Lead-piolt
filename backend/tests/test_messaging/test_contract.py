from app.services.messaging import MessageProviderFactory, OutboundMessage, RetryPolicy, retry_with_backoff
from app.services.messaging.base import MessageResult


def test_public_messaging_contract_exports_and_factory():
    message = OutboundMessage(recipient="lead@example.com", body="Hello")
    provider = MessageProviderFactory.create("GMAIL", credentials={"client_id": "demo"})

    assert isinstance(message, OutboundMessage)
    assert provider.name == "GMAIL"
    assert MessageResult({"status": "SENT"})["status"] == "SENT"


def test_factory_normalizes_channel_names():
    assert MessageProviderFactory.create(" whatsapp ").name == "WHATSAPP"


def test_retry_policy_retries_until_success():
    attempts = 0

    def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("temporary failure")
        return "ok"

    result = retry_with_backoff(flaky_operation, policy=RetryPolicy(max_retries=2, base_delay=0, jitter=0))

    assert result == "ok"
    assert attempts == 2
