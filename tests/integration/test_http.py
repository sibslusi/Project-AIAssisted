from fastapi.testclient import TestClient

from app.interfaces.http import app


client = TestClient(app)


def test_health_is_available():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_module_endpoints_require_login():
    assert client.get("/api/modules").status_code == 401
    assert client.post("/api/modules/module-einwohnerdienste/rounds").status_code == 401
    assert client.get("/api/modules/module-einwohnerdienste/progress").status_code == 401
