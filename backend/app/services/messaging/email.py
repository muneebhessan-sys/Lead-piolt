from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any

from .base import MessageProvider, SendResult


class EmailProvider(MessageProvider):
    name = "EMAIL"

    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 25, username: str = "", password: str = "") -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    async def send(self, to: str, body: str, context: dict[str, Any] | None = None) -> SendResult:
        context = context or {}
        subject = str(context.get("subject", "LeadPilot message"))
        sender = str(context.get("from", self.username))
        message = EmailMessage()
        message["From"] = sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        def deliver() -> None:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as client:
                client.ehlo()
                if context.get("starttls", True):
                    client.starttls()
                    client.ehlo()
                if self.username:
                    client.login(self.username, self.password)
                client.send_message(message)

        await asyncio.to_thread(deliver)
        return SendResult({
            "status": "SENT",
            "channel": self.name,
            "recipient": to,
            "provider": "SMTP",
            "metadata": {"subject": subject},
        })

    async def health_check(self) -> bool:
        def check() -> bool:
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as client:
                    client.noop()
                return True
            except (OSError, smtplib.SMTPException):
                return False

        return await asyncio.to_thread(check)

    def capabilities(self) -> list[str]:
        return ["email", "smtp"]
