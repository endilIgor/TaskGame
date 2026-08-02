from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "TaskGame"}


def test_cors_rejects_loopback_ip_origin(monkeypatch):
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "http://localhost:8000")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://127.0.0.1:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.headers.get("access-control-allow-origin") is None
