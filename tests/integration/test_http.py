from fastapi.testclient import TestClient

from app.interfaces.http import app

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
    assert progress.json()["scores"]["best"] < 4


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
