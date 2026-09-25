import asyncio

from app.services.messaging.retry import CircuitBreaker, RetryPolicy, async_retry_with_backoff


def test_async_retry_retries_and_records_success():
    attempts = 0
    breaker = CircuitBreaker(failure_threshold=3)

    async def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("temporary")
        return "ok"

    result = asyncio.run(async_retry_with_backoff(
        operation,
        policy=RetryPolicy(max_retries=2, base_delay=0, jitter=0),
        breaker=breaker,
    ))
    assert result == "ok"
    assert attempts == 2
    assert breaker.failures == 0


def test_async_retry_rejects_open_circuit():
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=60)
    breaker.record_failure()

    async def operation():
        return "not-called"

    try:
        asyncio.run(async_retry_with_backoff(operation, breaker=breaker))
    except RuntimeError as exc:
        assert str(exc) == "CIRCUIT_BREAKER_OPEN"
    else:
        raise AssertionError("open circuit must reject work")
