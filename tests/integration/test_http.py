from fastapi.testclient import TestClient
from itsdangerous import URLSafeTimedSerializer
import pytest

from app.main import app

client = TestClient(app, base_url="https://testserver")


def login(email):
    login_page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "email": email,
            "password": "demo-password",
            "csrf_token": login_page.json()["csrf_token"],
        },
    )
    assert response.status_code == 200


def csrf_headers():
    return {"X-CSRF-Token": client.cookies["csrf_token"]}


def test_health_is_available():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_module_endpoints_require_login():
    assert client.get("/api/modules").status_code == 401
    assert client.post("/api/modules/module-einwohnerdienste/rounds").status_code == 401
    assert (
        client.get("/api/modules/module-einwohnerdienste/progress").status_code == 401
    )


def test_employee_can_start_resume_answer_and_complete_round():
    login("marek.dalenor@grenchen.example")

    modules = client.get("/api/modules")
    assert modules.status_code == 200
    assert [item["module_id"] for item in modules.json()] == ["module-einwohnerdienste"]

    started = client.post(
        "/api/modules/module-einwohnerdienste/rounds", headers=csrf_headers()
    )
    assert started.status_code == 201
    round_data = started.json()
    assert len(round_data["scenario_ids"]) == 5
    round_id = round_data["id"]

    resumed = client.post(
        "/api/modules/module-einwohnerdienste/rounds", headers=csrf_headers()
    )
    assert resumed.status_code == 200
    assert resumed.json()["id"] == round_id

    invalid = client.post(
        f"/api/rounds/{round_id}/answers",
        json={"position": 1, "option_id": "not-an-option"},
        headers=csrf_headers(),
    )
    assert invalid.status_code == 422

    for position in range(1, 6):
        answer = client.post(
            f"/api/rounds/{round_id}/answers",
            json={"position": position, "option_id": "a"},
            headers=csrf_headers(),
        )
        assert answer.status_code == 201
        assert "explanation" in answer.json()
        assert "legal_basis" in answer.json()

    progress = client.get("/api/modules/module-einwohnerdienste/progress")
    assert progress.status_code == 200
    assert 0 <= progress.json()["scores"]["best"] <= 5
    assert progress.json()["status"] in {"offen", "erledigt"}


def test_employee_cannot_start_foreign_module_or_lead_rounds():
    login("marek.dalenor@grenchen.example")
    foreign = client.post(
        "/api/modules/module-soziale-dienste/rounds", headers=csrf_headers()
    )
    assert foreign.status_code == 404

    login("liora.veylan@grenchen.example")
    forbidden = client.post(
        "/api/modules/module-einwohnerdienste/rounds", headers=csrf_headers()
    )
    assert forbidden.status_code == 403


def test_duplicate_answer_is_conflict_and_data_protection_officer_sees_all_modules():
    login("elina.norveth@grenchen.example")
    started = client.post(
        "/api/modules/module-einwohnerdienste/rounds", headers=csrf_headers()
    )
    assert started.status_code == 201
    round_id = started.json()["id"]
    first = client.post(
        f"/api/rounds/{round_id}/answers",
        json={"position": 1, "option_id": "a"},
        headers=csrf_headers(),
    )
    assert first.status_code == 201
    duplicate = client.post(
        f"/api/rounds/{round_id}/answers",
        json={"position": 1, "option_id": "a"},
        headers=csrf_headers(),
    )
    assert duplicate.status_code == 409

    login("yara.merovan@grenchen.example")
    modules = client.get("/api/modules")
    assert modules.status_code == 200
    assert len(modules.json()) == 3


def test_logout_and_writing_without_csrf_are_rejected():
    login("marek.dalenor@grenchen.example")
    missing_csrf = client.post("/logout")
    assert missing_csrf.status_code == 403
    logged_out = client.post("/logout", headers=csrf_headers())
    assert logged_out.status_code == 200
    assert client.get("/api/modules").status_code == 401


def test_expired_session_cookie_is_rejected(monkeypatch):
    issued_at = 1_000_000
    monkeypatch.setattr("itsdangerous.timed.time.time", lambda: issued_at)
    token = URLSafeTimedSerializer(
        "test-session-secret", salt="session"
    ).dumps(
        {
            "id": "user-einwohnerdienste-01",
            "role": "employee",
            "department_id": "department-einwohnerdienste",
        }
    )
    monkeypatch.setattr(
        "itsdangerous.timed.time.time", lambda: issued_at + 8 * 60 * 60 + 1
    )
    client.cookies.set("session", token)

    assert client.get("/api/modules").status_code == 401


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"json": {"option_id": "a"}},
        {"json": {"position": 1}},
        {"content": b"not-json"},
    ],
)
def test_invalid_answer_payload_returns_unprocessable_entity(request_kwargs):
    login("marek.dalenor@grenchen.example")
    started = client.post(
        "/api/modules/module-einwohnerdienste/rounds", headers=csrf_headers()
    )
    assert started.status_code in {200, 201}

    response = client.post(
        f"/api/rounds/{started.json()['id']}/answers",
        headers=csrf_headers(),
        **request_kwargs,
    )

    assert response.status_code == 422
