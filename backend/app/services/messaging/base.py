from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.config import settings


class SendResult(dict):
    """Typed-like result payload returned by messaging providers."""


MessageResult = SendResult


@dataclass(slots=True)
class OutboundMessage:
    recipient: str
    body: str
    context: dict[str, Any] = field(default_factory=dict)


class MessageProvider(ABC):
    name: str = "GENERIC"

    @abstractmethod
    async def send(self, to: str, body: str, context: dict[str, Any] | None = None) -> SendResult:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> list[str]:
        raise NotImplementedError

    def rate_limit_key(self) -> str:
        return self.name.lower()

    def require_real_transport(self) -> None:
        if not settings.development_mode:
            raise NotImplementedError(f"{self.name}_TRANSPORT_NOT_IMPLEMENTED")
