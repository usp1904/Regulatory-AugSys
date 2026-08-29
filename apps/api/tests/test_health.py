from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "regulatory-augsys-api"
    assert body["version"] == "0.1.0"
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body
