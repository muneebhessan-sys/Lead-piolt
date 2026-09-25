from __future__ import annotations

import random
import time
import asyncio
import inspect
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 0.5
    jitter: float = 0.2


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.open_until = 0.0

    def allow(self) -> bool:
        if time.monotonic() < self.open_until:
            return False
        return True

    def record_success(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.open_until = time.monotonic() + self.reset_timeout


def retry_with_backoff(
    func: Callable[..., T],
    *args: object,
    policy: RetryPolicy | None = None,
    max_retries: int | None = None,
    base_delay: float | None = None,
    **kwargs: object,
) -> T:
    selected_policy = policy or RetryPolicy(
        max_retries=3 if max_retries is None else max_retries,
        base_delay=0.5 if base_delay is None else base_delay,
    )
    last_error: Exception | None = None
    for attempt in range(selected_policy.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - retry boundary
            last_error = exc
            if attempt >= selected_policy.max_retries:
                raise
            delay = selected_policy.base_delay * (2 ** attempt) + random.uniform(0, selected_policy.jitter)
            time.sleep(delay)
    if last_error is not None:
        raise last_error
    raise RuntimeError("retry_with_backoff failed without error")


async def async_retry_with_backoff(
    func: Callable[..., T],
    *args: object,
    policy: RetryPolicy | None = None,
    breaker: CircuitBreaker | None = None,
    **kwargs: object,
) -> T:
    selected_policy = policy or RetryPolicy()
    active_breaker = breaker or CircuitBreaker()
    if not active_breaker.allow():
        raise RuntimeError("CIRCUIT_BREAKER_OPEN")
    for attempt in range(selected_policy.max_retries + 1):
        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            active_breaker.record_success()
            return result
        except Exception:
            active_breaker.record_failure()
            if attempt >= selected_policy.max_retries:
                raise
            delay = selected_policy.base_delay * (2 ** attempt) + random.uniform(0, selected_policy.jitter)
            await asyncio.sleep(delay)
    raise RuntimeError("async_retry_with_backoff failed without error")
