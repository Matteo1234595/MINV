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


def test_latest_health_returns_score(client, monkeypatch):
    fake_score = SimpleNamespace(
        score=82,
        components={"runway_months": {"value": 10, "score": 80}},
        computed_at="2026-01-21T00:00:00Z",
    )

    monkeypatch.setattr("app.routers.health.latest_health_score", lambda *_: fake_score)

    response = client.get("/health/latest", params={"organization_id": "00000000-0000-0000-0000-000000000000"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["score"] == 82
    assert "components" in payload


def test_recompute_insights_returns_summary(client, monkeypatch):
    monkeypatch.setattr("app.routers.health.compute_monthly_kpis", lambda *_: [SimpleNamespace(snapshot_at=1)])
    monkeypatch.setattr("app.routers.health.persist_kpis", lambda *_: 6)
    fake_health = SimpleNamespace(score=70, components={}, computed_at="2026-01-21T00:00:00Z")
    monkeypatch.setattr("app.routers.health.compute_health_score", lambda *_: fake_health)
    monkeypatch.setattr(
        "app.routers.health.persist_health_score",
        lambda *_: SimpleNamespace(score=70, computed_at="2026-01-21T00:00:00Z"),
    )
    monkeypatch.setattr("app.routers.health.generate_insights", lambda *_: [SimpleNamespace()] * 3)

    response = client.post(
        "/insights/recompute",
        params={"organization_id": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["health_score"] == 70
    assert payload["insights_created"] == 3
