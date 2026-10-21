from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.infrastructure.models import AssignmentModel, ScenarioModel
from app.interfaces.http import app, engine


def login(client: TestClient, email: str) -> None:
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


def csrf(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies["csrf_token"]}


def client() -> TestClient:
    return TestClient(app, base_url="https://testserver")


def start_round(test_client: TestClient, module_id: str) -> dict:
    response = test_client.post(
        f"/api/modules/{module_id}/rounds", headers=csrf(test_client)
    )
    assert response.status_code in (200, 201)
    return response.json()


def answer_all(test_client: TestClient, round_id: str, options: list[str]) -> dict:
    result = {}
    for position, option_id in enumerate(options, 1):
        response = test_client.post(
            f"/api/rounds/{round_id}/answers",
            json={"position": position, "option_id": option_id},
            headers=csrf(test_client),
        )
        assert response.status_code == 201
        result = response.json()
    return result


def test_ac001_full_workflow_login_start_five_answers_status_logout():
    """AC-001: Login, Start, fünf Antworten, Abschluss, Status und Logout."""
    test_client = client()
    login(test_client, "marek.dalenor@grenchen.example")
    round_data = start_round(test_client, "module-einwohnerdienste")

    assert round_data["attempt_number"] >= 1
    assert len(round_data["scenario_ids"]) == 5
    result = answer_all(test_client, round_data["id"], ["a", "b", "c", "d", "a"])

    assert result["score"] == 5
    assert result["passed"] is True
    progress = test_client.get("/api/modules/module-einwohnerdienste/progress")
    assert progress.json()["status"] == "bestanden"

    logged_out = test_client.post("/logout", headers=csrf(test_client))
    assert logged_out.status_code == 200
    assert test_client.get("/api/modules").status_code == 401


def test_ac002_employee_sees_only_own_department_modules():
    """AC-002: Module bleiben auf die eigene Abteilung beschränkt."""
    test_client = client()
    login(test_client, "marek.dalenor@grenchen.example")

    response = test_client.get("/api/modules")

    assert response.status_code == 200
    assert [item["module_id"] for item in response.json()] == [
        "module-einwohnerdienste"
    ]


def test_ac003_valid_answer_is_saved_and_position_advances():
    """AC-003: Eine gültige Antwort wird gespeichert und die Position erledigt."""
    test_client = client()
    login(test_client, "elina.norveth@grenchen.example")
    round_data = start_round(test_client, "module-einwohnerdienste")

    response = test_client.post(
        f"/api/rounds/{round_data['id']}/answers",
        json={"position": 1, "option_id": "a"},
        headers=csrf(test_client),
    )
    resumed = test_client.post(
        "/api/modules/module-einwohnerdienste/rounds", headers=csrf(test_client)
    )

    assert response.status_code == 201
    assert resumed.json()["next_position"] == 2


def test_ac004_answer_contains_immediate_feedback():
    """AC-004: Feedback enthält Korrektheit, Erklärung und Rechtsgrundlage."""
    test_client = client()
    login(test_client, "tarin.belmar@grenchen.example")
    round_data = start_round(test_client, "module-einwohnerdienste")

    response = test_client.post(
        f"/api/rounds/{round_data['id']}/answers",
        json={"position": 1, "option_id": "a"},
        headers=csrf(test_client),
    )

    assert response.status_code == 201
    assert set(response.json()) >= {"correct", "explanation", "legal_basis"}


def test_ac005_four_correct_answers_pass_round():
    """AC-005: Vier richtige Antworten führen zu bestanden."""
    test_client = client()
    login(test_client, "nerina.solvek@grenchen.example")
    round_data = start_round(test_client, "module-einwohnerdienste")

    result = answer_all(test_client, round_data["id"], ["a", "b", "c", "d", "a"])

    assert result["score"] == 5
    assert result["passed"] is True


def test_ac006_three_or_fewer_correct_answers_are_not_passed():
    """AC-006: Drei oder weniger richtige Antworten bestehen nicht."""
    test_client = client()
    login(test_client, "jorin.mavero@grenchen.example")
    round_data = start_round(test_client, "module-soziale-dienste")

    result = answer_all(test_client, round_data["id"], ["a", "a", "a", "a", "a"])

    assert result["score"] <= 3
    assert result["passed"] is False


def test_ac007_progress_uses_best_completed_attempt():
    """AC-007: Der Fortschritt verwendet den besten abgeschlossenen Versuch."""
    test_client = client()
    login(test_client, "mirel.tavren@grenchen.example")
    first = start_round(test_client, "module-finanzen-informatik")
    answer_all(test_client, first["id"], ["a", "a", "a", "a", "a"])
    second = start_round(test_client, "module-finanzen-informatik")
    answer_all(test_client, second["id"], ["a", "b", "c", "d", "a"])

    progress = test_client.get("/api/modules/module-finanzen-informatik/progress")

    assert progress.json()["scores"]["best"] >= 4


def test_ac008_invalid_option_is_unprocessable_and_does_not_advance():
    """AC-008: Fremde Optionen ergeben 422 und keine gespeicherte Antwort."""
    test_client = client()
    login(test_client, "aven.solmar@grenchen.example")
    round_data = start_round(test_client, "module-finanzen-informatik")

    invalid = test_client.post(
        f"/api/rounds/{round_data['id']}/answers",
        json={"position": 1, "option_id": "unknown"},
        headers=csrf(test_client),
    )
    resumed = test_client.post(
        "/api/modules/module-finanzen-informatik/rounds", headers=csrf(test_client)
    )

    assert invalid.status_code == 422
    assert resumed.json()["next_position"] == 1


def test_ac009_foreign_department_is_hidden():
    """AC-009: Ein fremdes Modul liefert ohne Inhaltsleck 404."""
    test_client = client()
    login(test_client, "marek.dalenor@grenchen.example")

    response = test_client.post(
        "/api/modules/module-soziale-dienste/rounds", headers=csrf(test_client)
    )

    assert response.status_code == 404
    assert "scenario" not in response.text.lower()


def test_ac010_late_passed_round_gets_late_status():
    """AC-010: Ein bestandener Versuch nach Fristende wird verspätet erledigt."""
    with Session(engine) as session:
        assignment = session.get(AssignmentModel, "assignment-soziale-dienste")
        original_due_date = assignment.due_date
        assignment.due_date = date(2026, 1, 1)
        session.commit()
    try:
        test_client = client()
        login(test_client, "selma.rovelin@grenchen.example")
        round_data = start_round(test_client, "module-soziale-dienste")
        answer_all(test_client, round_data["id"], ["a", "b", "c", "d", "a"])

        progress = test_client.get("/api/modules/module-soziale-dienste/progress")

        assert progress.json()["status"] == "verspätet erledigt"
    finally:
        with Session(engine) as session:
            session.get(
                AssignmentModel, "assignment-soziale-dienste"
            ).due_date = original_due_date
            session.commit()


def test_ac011_open_round_resumes_at_first_unanswered_position():
    """AC-011: Eine offene Runde wird an der ersten offenen Position fortgesetzt."""
    test_client = client()
    login(test_client, "dario.fenvar@grenchen.example")
    round_data = start_round(test_client, "module-soziale-dienste")
    test_client.post(
        f"/api/rounds/{round_data['id']}/answers",
        json={"position": 1, "option_id": "a"},
        headers=csrf(test_client),
    )

    resumed = test_client.post(
        "/api/modules/module-soziale-dienste/rounds", headers=csrf(test_client)
    )

    assert resumed.status_code == 200
    assert resumed.json()["id"] == round_data["id"]
    assert resumed.json()["next_position"] == 2


def test_ac012_incomplete_active_module_is_rejected_without_five_active_cases():
    """AC-012: Ein Modul ohne fünf aktive Fälle startet nicht."""
    with Session(engine) as session:
        scenario = session.get(ScenarioModel, "scenario-soziale-dienste-01")
        scenario.active = False
        session.commit()
    try:
        test_client = client()
        login(test_client, "elara.monveth@grenchen.example")
        response = test_client.post(
            "/api/modules/module-soziale-dienste/rounds", headers=csrf(test_client)
        )
        assert response.status_code == 409
    finally:
        with Session(engine) as session:
            session.get(ScenarioModel, "scenario-soziale-dienste-01").active = True
            session.commit()


def test_ac013_scenario_management_endpoints_are_not_exposed():
    """AC-013: UC-001 bietet keine Änderungs- oder Lösch-API für Szenarien."""
    test_client = client()
    login(test_client, "yara.merovan@grenchen.example")

    assert test_client.patch("/api/scenarios/scenario-1").status_code == 404
    assert test_client.delete("/api/scenarios/scenario-1").status_code == 404
