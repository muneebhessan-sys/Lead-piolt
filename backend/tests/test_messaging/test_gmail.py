from app.services.messaging.gmail import GmailProvider


def test_gmail_provider_capabilities():
    provider = GmailProvider(credentials={"client_id": "demo"})
    assert "gmail" in provider.capabilities()
    assert provider.name == "GMAIL"
