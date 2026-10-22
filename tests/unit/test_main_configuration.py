import pytest
from fastapi.testclient import TestClient

from app.infrastructure.auth import authenticate
from app.infrastructure.clock import SystemClock
from app.main import create_app


def configured_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("DEMO_PASSWORD", "test-demo-password")


@pytest.mark.parametrize("missing", ["DATABASE_URL", "SESSION_SECRET", "DEMO_PASSWORD"])
def test_create_app_requires_security_and_database_environment(monkeypatch, missing):
    configured_environment(monkeypatch)
    monkeypatch.delenv(missing)

    with pytest.raises(RuntimeError, match=missing):
        create_app()


def test_create_app_builds_from_environment_without_seed_import_side_effect(
    monkeypatch,
):
    configured_environment(monkeypatch)

    application = create_app()

    assert application is not None


def test_clock_and_authentication_adapters_live_in_infrastructure():
    assert SystemClock().now() is not None
    assert callable(authenticate)


def test_health_reports_app_version_from_environment(monkeypatch):
    configured_environment(monkeypatch)
    monkeypatch.setenv("APP_VERSION", "v9.9.9")

    response = TestClient(create_app()).get("/health")

    assert response.json() == {"status": "ok", "version": "v9.9.9"}
