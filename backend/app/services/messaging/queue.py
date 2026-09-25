from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import OutboundMessage, OutboundMessageStatus

from .factory import MessageProviderFactory
from .outbound import OutboundMessageService
from .retry import RetryPolicy, async_retry_with_backoff


@dataclass(slots=True)
class QueueItem:
    message_id: int
    context: dict[str, Any] = field(default_factory=dict)


class MessageQueue:
    """In-process queue with durable outbound state in SQLite/PostgreSQL."""

    def __init__(self, session_factory: sessionmaker[Session], maxsize: int = 1000) -> None:
        self._session_factory = session_factory
        self._queue: asyncio.Queue[QueueItem] = asyncio.Queue(maxsize=maxsize)
        self._worker_task: asyncio.Task[None] | None = None
        self._stopping = asyncio.Event()

    async def enqueue(self, message: OutboundMessage, context: dict[str, Any] | None = None) -> None:
        db = self._session_factory()
        try:
            message.status = OutboundMessageStatus.QUEUED
            db.commit()
        finally:
            db.close()
        await self._queue.put(QueueItem(message_id=message.id, context=context or {}))

    async def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._stopping.clear()
            self._worker_task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopping.set()
        if self._worker_task is not None:
            await self._worker_task
            self._worker_task = None

    async def drain_once(self) -> bool:
        try:
            item = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return False
        await self._deliver(item)
        self._queue.task_done()
        return True

    async def _run(self) -> None:
        while not self._stopping.is_set():
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            try:
                await self._deliver(item)
            finally:
                self._queue.task_done()

    async def _deliver(self, item: QueueItem) -> None:
        db = self._session_factory()
        try:
            message = db.scalar(select(OutboundMessage).where(OutboundMessage.id == item.message_id))
            if message is None or message.status in {
                OutboundMessageStatus.SENT,
                OutboundMessageStatus.DELIVERED,
            }:
                return
            provider = MessageProviderFactory.create(message.channel, **item.context.pop("provider_kwargs", {}))
            service = OutboundMessageService(db)

            async def deliver():
                result = await service.send_once(provider, message=message, context=item.context)
                if result.status == OutboundMessageStatus.FAILED:
                    raise RuntimeError(result.error or "MESSAGE_DELIVERY_FAILED")
                return result

            await async_retry_with_backoff(deliver, policy=RetryPolicy(max_retries=3, base_delay=1.0))
        finally:
            db.close()

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()


def create_message_queue(session_factory: sessionmaker[Session]) -> MessageQueue:
    return MessageQueue(session_factory)
