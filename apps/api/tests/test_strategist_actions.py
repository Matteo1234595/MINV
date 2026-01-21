from types import SimpleNamespace
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app


@pytest.fixture()
def client():
    def _override_db():
        yield SimpleNamespace()

    app.dependency_overrides[get_db] = _override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_brief(client, monkeypatch):
    org_id = uuid.uuid4()
    brief = SimpleNamespace(
        id=uuid.uuid4(),
        organization_id=org_id,
        content="Strategic brief content",
        context={"snapshot_at": "2026-01-01"},
        created_at="2026-01-21T00:00:00Z",
    )
    monkeypatch.setattr("app.routers.strategist.generate_strategy_brief", lambda *_: brief)

    response = client.post("/strategist/brief", params={"organization_id": str(org_id)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "Strategic brief content"


def test_latest_brief(client, monkeypatch):
    org_id = uuid.uuid4()
    brief = SimpleNamespace(
        id=uuid.uuid4(),
        organization_id=org_id,
        content="Latest brief",
        context={},
        created_at="2026-01-21T00:00:00Z",
    )
    monkeypatch.setattr("app.routers.strategist.latest_strategy_brief", lambda *_: brief)

    response = client.get("/strategist/latest", params={"organization_id": str(org_id)})

    assert response.status_code == 200
    assert response.json()["content"] == "Latest brief"


def test_generate_actions(client, monkeypatch):
    org_id = uuid.uuid4()
    action = SimpleNamespace(
        id=uuid.uuid4(),
        organization_id=org_id,
        insight_id=None,
        title="Action title",
        status="open",
        due_at=None,
        created_at="2026-01-21T00:00:00Z",
    )
    monkeypatch.setattr("app.routers.strategist.generate_actions", lambda *_: [action])

    response = client.post("/actions/generate", params={"organization_id": str(org_id)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["actions"][0]["title"] == "Action title"


def test_open_actions(client, monkeypatch):
    org_id = uuid.uuid4()
    action = SimpleNamespace(
        id=uuid.uuid4(),
        organization_id=org_id,
        insight_id=None,
        title="Open action",
        status="open",
        due_at=None,
        created_at="2026-01-21T00:00:00Z",
    )
    monkeypatch.setattr("app.routers.strategist.open_actions", lambda *_: [action])

    response = client.get("/actions/open", params={"organization_id": str(org_id)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["actions"][0]["title"] == "Open action"
