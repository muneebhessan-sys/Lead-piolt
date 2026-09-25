from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RateLimitBucket


@dataclass
class TokenBucket:
    capacity: int
    refill_rate: float
    tokens: float = field(init=False)
    updated_at: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)

    def consume(self, amount: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.updated_at = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.RLock()

    def configure(self, provider: str, capacity: int, refill_rate_per_second: float) -> None:
        with self._lock:
            self._buckets[provider] = TokenBucket(capacity=capacity, refill_rate=refill_rate_per_second)

    def allow(self, provider: str, amount: int = 1) -> bool:
        with self._lock:
            bucket = self._buckets.setdefault(provider, TokenBucket(capacity=1, refill_rate=1.0))
            return bucket.consume(amount)

    def allow_persistent(
        self,
        db: Session,
        provider: str,
        capacity: int,
        window_seconds: int,
        amount: int = 1,
    ) -> bool:
        """Consume a DB-backed fixed-window quota that survives process restarts."""
        if amount < 1 or amount > capacity:
            return False
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=now.timestamp() % window_seconds)
        bucket = db.scalar(
            select(RateLimitBucket).where(
                RateLimitBucket.provider == provider,
                RateLimitBucket.window_start == window_start,
            )
        )
        if bucket is None:
            bucket = RateLimitBucket(provider=provider, window_start=window_start, count=0)
            db.add(bucket)
            db.flush()
        if bucket.count + amount > capacity:
            return False
        bucket.count += amount
        db.commit()
        return True


def get_default_rates() -> dict[str, tuple[int, float]]:
    return {
        "WHATSAPP": (1000, 1000 / 86400),
        "INSTAGRAM": (200, 200 / 86400),
        "FACEBOOK": (200, 200 / 86400),
        "LINKEDIN": (100, 100 / 86400),
        "GMAIL": (500, 500 / 86400),
        "SMS": (200, 200 / 86400),
        "EMAIL": (200, 200 / 86400),
    }


rate_limiter = RateLimiter()
for provider, (capacity, refill) in get_default_rates().items():
    rate_limiter.configure(provider, capacity, refill)
