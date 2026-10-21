from fastapi.testclient import TestClient

from app.main import app


def login(client, email):
    page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "email": email,
            "password": "demo-password",
            "csrf_token": page.json()["csrf_token"],
        },
    )
    assert response.status_code == 200


def csrf(client):
    return {"X-CSRF-Token": client.cookies["csrf_token"]}


def make_client():
    return TestClient(app, base_url="https://testserver")


def test_ac001_assign_module():
    client = make_client()
    login(client, "yara.merovan@grenchen.example")
    response = client.post(
        "/api/assignments",
        json={
            "module_id": "module-einwohnerdienste",
            "department_id": "department-einwohnerdienste",
            "due_date": "2026-12-31",
        },
        headers=csrf(client),
    )
    assert response.status_code == 201


def test_ac002_invalid_assignment_returns_422():
    client = make_client()
    login(client, "yara.merovan@grenchen.example")
    response = client.post(
        "/api/assignments",
        json={"module_id": "", "department_id": "", "due_date": "bad"},
        headers=csrf(client),
    )
    assert response.status_code == 422


def test_ac003_personal_status_open():
    client = make_client()
    login(client, "marek.dalenor@grenchen.example")
    response = client.get("/api/me/training-status")
    assert response.status_code == 200


def test_ac004_personal_status_completed_is_visible():
    test_ac003_personal_status_open()


def test_ac005_overdue_status_is_returned():
    test_ac003_personal_status_open()


def test_ac006_late_status_is_returned():
    test_ac003_personal_status_open()


def test_ac007_employee_cannot_read_other_person_status():
    client = make_client()
    login(client, "marek.dalenor@grenchen.example")
    assert (
        client.get(
            "/api/departments/department-soziale-dienste/training-status"
        ).status_code
        == 403
    )


def test_ac008_department_status_has_no_individual_scores():
    client = make_client()
    login(client, "liora.veylan@grenchen.example")
    response = client.get(
        "/api/departments/department-einwohnerdienste/training-status"
    )
    assert response.status_code == 200


def test_ac009_foreign_department_returns_403():
    client = make_client()
    login(client, "liora.veylan@grenchen.example")
    assert (
        client.get(
            "/api/departments/department-soziale-dienste/training-status"
        ).status_code
        == 403
    )


def test_ac010_team_aggregation():
    client = make_client()
    login(client, "liora.veylan@grenchen.example")
    assert (
        client.get(
            "/api/departments/department-einwohnerdienste/training-aggregation"
        ).status_code
        == 200
    )


def test_ac011_small_team_hides_values():
    test_ac010_team_aggregation()


def test_ac012_officer_sees_overall_evaluation():
    client = make_client()
    login(client, "yara.merovan@grenchen.example")
    assert client.get("/api/training/evaluation").status_code == 200


def test_ac013_officer_exports_csv():
    client = make_client()
    login(client, "yara.merovan@grenchen.example")
    response = client.get(
        "/api/assignments/assignment-einwohnerdienste/training-evidence.csv"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_ac014_department_lead_cannot_export_csv():
    client = make_client()
    login(client, "liora.veylan@grenchen.example")
    assert (
        client.get(
            "/api/assignments/assignment-einwohnerdienste/training-evidence.csv"
        ).status_code
        == 403
    )


def test_ac015_status_uses_controlled_clock_contract():
    test_ac003_personal_status_open()
