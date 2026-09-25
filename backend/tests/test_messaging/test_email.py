import asyncio
from unittest.mock import patch

from app.services.messaging.email import EmailProvider


class FakeSMTP:
    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sent = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def ehlo(self):
        return None

    def starttls(self):
        return None

    def login(self, username, password):
        return None

    def send_message(self, message):
        self.sent = True
        assert message["To"] == "lead@example.com"

    def noop(self):
        return (250, b"ok")


def test_email_provider_sends_through_smtp():
    with patch("smtplib.SMTP", FakeSMTP):
        result = asyncio.run(
            EmailProvider("smtp.example.test", 587, "sender@example.com", "secret").send(
                "lead@example.com", "Hello", {"subject": "Test"}
            )
        )
    assert result["status"] == "SENT"
    assert result["provider"] == "SMTP"
