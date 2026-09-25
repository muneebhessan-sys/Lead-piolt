import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main
from app.database import get_db
from app.models import Account, Base, Call
from app.services.security import secret_store

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = override_get_db
main.app.dependency_overrides[main.require_admin] = lambda: {"username": "admin", "role": "admin"}
client = TestClient(main.app)


def test_meta_account_is_visible_to_instagram_and_facebook_cards():
    db = TestingSessionLocal()
    db.add(Account(
        email="admin",
        name="Meta business",
        provider="META",
        status="ACTIVE",
        access_token_encrypted=secret_store.encrypt("token"),
    ))
    db.commit()
    db.close()

    instagram = client.get("/api/v1/admin/integrations/instagram")
    facebook = client.get("/api/v1/admin/integrations/facebook")
    assert instagram.json()["status"] == "CONNECTED"
    assert facebook.json()["status"] == "CONNECTED"
    assert "instagram" in instagram.json()["capabilities"]


def test_campaign_requires_selection_and_sender():
    response = client.post("/api/v1/campaigns", json={"name": "Test", "sender_account": "sender@example.com", "lead_ids": []})
    assert response.status_code == 422
    assert response.json()["error"] == "Select at least one lead"


def test_whatsapp_verification_challenge_can_be_confirmed():
    saved = client.put("/api/v1/admin/contact-profile", json={"phone_number": "+15551234567"})
    assert saved.status_code == 200
    requested = client.post("/api/v1/admin/contact-profile/whatsapp_phone/verification-request")
    assert requested.status_code == 200
    code = requested.json()["development_code"]
    confirmed = client.post(
        "/api/v1/admin/contact-profile/whatsapp_phone/verification-confirm",
        json={"code": code},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "VERIFIED"
    assert client.get("/api/v1/admin/contact-profile").json()["whatsapp_phone_status"] == "VERIFIED"


def test_voice_callback_persists_real_recording_and_transcript():
    db = TestingSessionLocal()
    call = Call(status="IN_PROGRESS", provider_reference="provider-call-1")
    db.add(call)
    db.commit()
    call_id = call.id
    db.close()

    payload = {"status": "COMPLETED", "recording_url": "https://voice.test/recording.wav", "transcript": "Client asked for pricing.", "duration": 42}
    response = client.post(f"/api/v1/webhooks/voice/{call_id}", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["recording_url"] == payload["recording_url"]
    assert body["transcript"] == payload["transcript"]
    assert body["duration_seconds"] == 42


def test_voice_callback_requires_signature_when_configured():
    original_secret = main.settings.webhook_signing_secret
    main.settings.webhook_signing_secret = "test-secret"
    try:
        response = client.post("/api/v1/webhooks/voice/999", json={"status": "COMPLETED"})
        assert response.status_code == 401
    finally:
        main.settings.webhook_signing_secret = original_secret
