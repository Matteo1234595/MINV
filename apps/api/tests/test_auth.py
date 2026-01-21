from datetime import datetime
from types import SimpleNamespace
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.routers.auth import get_current_user
from app.services.auth import TokenPair


@pytest.fixture()
def client():
    def _override_db():
        yield SimpleNamespace()

    app.dependency_overrides[get_db] = _override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_login_returns_tokens(client, monkeypatch):
    user = SimpleNamespace(id=uuid.uuid4(), organization_id=uuid.uuid4())
    tokens = TokenPair(
        access_token="access",
        refresh_token="refresh",
        access_expires_at=datetime(2026, 1, 21),
        refresh_expires_at=datetime(2026, 2, 21),
    )
    monkeypatch.setattr("app.routers.auth.authenticate_user", lambda *_: user)
    monkeypatch.setattr("app.routers.auth.issue_tokens", lambda *_: tokens)

    response = client.post("/auth/login", json={"email": "user@example.com", "password": "pass"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "access"
    assert payload["refresh_token"] == "refresh"


def test_me_returns_current_user(client):
    user = SimpleNamespace(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="user@example.com",
        full_name="Test User",
    )
    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/auth/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "user@example.com"

    app.dependency_overrides.pop(get_current_user, None)
