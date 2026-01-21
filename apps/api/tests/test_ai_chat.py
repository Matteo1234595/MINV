from types import SimpleNamespace

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


def test_ai_chat_returns_response(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    fake_result = SimpleNamespace(content="Hello", model="test-model", tool_calls=[])
    monkeypatch.setattr("app.ai.router.chat_with_tools", lambda *_: fake_result)

    response = client.post(
        "/ai/chat",
        json={"organization_id": "00000000-0000-0000-0000-000000000000", "message": "Hello"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "Hello"
