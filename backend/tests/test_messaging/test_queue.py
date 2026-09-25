import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, OutboundMessage, OutboundMessageStatus
from app.services.messaging.queue import MessageQueue


def test_queue_persists_queued_state():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    db = sessions()
    message = OutboundMessage(
        idempotency_key="queue-test-1",
        channel="EMAIL",
        recipient="lead@example.com",
        body="Hello",
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    async def run():
        queue = MessageQueue(sessions)
        await queue.enqueue(message)
        return queue.pending_count

    assert asyncio.run(run()) == 1
    refreshed = db.get(OutboundMessage, message.id)
    assert refreshed.status == OutboundMessageStatus.QUEUED
    db.close()
