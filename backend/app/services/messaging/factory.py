from __future__ import annotations

from .base import MessageProvider
from .email import EmailProvider
from .facebook import FacebookProvider
from .gmail import GmailProvider
from .instagram import InstagramProvider
from .linkedin import LinkedInProvider
from .sms import SMSProvider
from .whatsapp import WhatsAppProvider


class MessageProviderFactory:
    provider_map = {
        "WHATSAPP": WhatsAppProvider,
        "INSTAGRAM": InstagramProvider,
        "FACEBOOK": FacebookProvider,
        "LINKEDIN": LinkedInProvider,
        "GMAIL": GmailProvider,
        "EMAIL": EmailProvider,
        "SMS": SMSProvider,
    }

    @classmethod
    def create(cls, channel: str, **kwargs: object) -> MessageProvider:
        normalized = (channel or "").strip().upper()
        if normalized not in cls.provider_map:
            raise ValueError(f"UNSUPPORTED_MESSAGE_CHANNEL: {channel}")
        provider_cls = cls.provider_map[normalized]
        return provider_cls(**kwargs)


def get_provider(channel: str, **kwargs: object) -> MessageProvider:
    return MessageProviderFactory.create(channel, **kwargs)
