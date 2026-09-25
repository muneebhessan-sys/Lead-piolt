import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import app.main as main
from app.database import get_db
from app.models import Base

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


def test_theme_defaults():
    response = client.get("/api/v1/admin/theme")
    assert response.status_code == 200
    payload = response.json()
    assert payload["theme"] in {"OBSIDIAN", "AURORA"}
    assert payload["reduced_motion"] in {True, False}
    assert "available_themes" in payload


def test_theme_updates_and_persists():
    response = client.put(
        "/api/v1/admin/theme",
        json={"theme": "AURORA", "reduced_motion": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["theme"] == "AURORA"
    assert payload["reduced_motion"] is True

    follow_up = client.get("/api/v1/admin/theme")
    assert follow_up.status_code == 200
    assert follow_up.json()["theme"] == "AURORA"
