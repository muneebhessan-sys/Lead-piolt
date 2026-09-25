from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CallResult(dict):
    pass


class CallStatus(dict):
    pass


class HealthStatus(dict):
    pass


class VoiceAgent(ABC):
    @abstractmethod
    async def start_call(self, to: str, from_: str, context: dict[str, Any] | None = None) -> CallResult:
        raise NotImplementedError

    @abstractmethod
    async def get_call_status(self, call_id: str) -> CallStatus:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> list[str]:
        raise NotImplementedError
