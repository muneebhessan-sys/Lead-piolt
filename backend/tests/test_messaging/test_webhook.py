from app.api.v1.webhooks import _message_update
from app.models import OutboundMessageStatus


def test_webhook_normalizes_delivery_status():
    message_id, status = _message_update({"message_id": "provider-1", "status": "delivered"})
    assert message_id == "provider-1"
    assert status == OutboundMessageStatus.DELIVERED.value


def test_webhook_rejects_unknown_status():
    message_id, status = _message_update({"id": "provider-1", "status": "unknown"})
    assert message_id == "provider-1"
    assert status is None
