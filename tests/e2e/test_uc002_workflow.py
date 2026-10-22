from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.models import (
    AssignmentModel,
    GameRoundModel,
    GameRoundScenarioModel,
    RoundAnswerModel,
)
from app.main import app

ZURICH = ZoneInfo("Europe/Zurich")
SEED_ASSIGNMENTS = (
    "assignment-einwohnerdienste",
    "assignment-soziale-dienste",
    "assignment-finanzen-informatik",
)


@pytest.fixture(autouse=True)
def isolate_database():
    original_services = app.state.services
    yield
    with app.state.engine.begin() as connection:
        connection.execute(delete(RoundAnswerModel))
        connection.execute(delete(GameRoundScenarioModel))
        connection.execute(delete(GameRoundModel))
        connection.execute(
            delete(AssignmentModel).where(
                AssignmentModel.id.not_in(
                    (
                        "assignment-einwohnerdienste",
                        "assignment-soziale-dienste",
                        "assignment-finanzen-informatik",
                    )
                )
            )
        )
    app.state.services = original_services


def set_clock(value):
    app.state.services = replace(app.state.services, clock=FixedClock(value))


class FixedClock:
    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


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


def assign(
    client,
    module_id,
    department_id="department-einwohnerdienste",
    due_date="2026-12-31",
):
    login(client, "ds@mail.ch")
    response = client.post(
        "/api/assignments",
        json={
            "module_id": module_id,
            "department_id": department_id,
            "due_date": due_date,
        },
        headers=csrf(client),
    )
    assert response.status_code == 201
    return response.json()


def complete_round(client, email, module_id, score=5):
    login(client, email)
    started = client.post(f"/api/modules/{module_id}/rounds", headers=csrf(client))
    assert started.status_code == 201
    options = {
        "module-einwohnerdienste": ("a", "b", "c", "d", "a"),
        "module-soziale-dienste": ("b", "c", "d", "a", "b"),
    }[module_id]
    for position, option in enumerate(options, 1):
        if position > score:
            option = "b" if option != "b" else "a"
        response = client.post(
            f"/api/rounds/{started.json()['id']}/answers",
            json={"position": position, "option_id": option},
            headers=csrf(client),
        )
        assert response.status_code == 201


def test_ac001_assign_module():
    client = make_client()
    response = assign(client, "module-soziale-dienste")
    assert response["module_id"] == "module-soziale-dienste"
    assert response["department_id"] == "department-einwohnerdienste"
    assert response["due_date"] == "2026-12-31"


def test_ac002_invalid_assignment_returns_422():
    client = make_client()
    login(client, "ds@mail.ch")
    before = len(client.get("/api/modules").json())
    payloads = (
        {"department_id": "department-einwohnerdienste", "due_date": "2026-12-31"},
        {"module_id": "module-soziale-dienste", "due_date": "2026-12-31"},
        {
            "module_id": "module-soziale-dienste",
            "department_id": "department-einwohnerdienste",
        },
        {
            "module_id": "module-soziale-dienste",
            "department_id": "department-einwohnerdienste",
            "due_date": "bad",
        },
    )
    for payload in payloads:
        assert (
            client.post(
                "/api/assignments", json=payload, headers=csrf(client)
            ).status_code
            == 422
        )
    assert len(client.get("/api/modules").json()) == before


def test_ac003_personal_status_open():
    client = make_client()
    assignment = assign(client, "module-soziale-dienste")
    login(client, "ma@mail.ch")
    for current in (
        datetime(2026, 12, 31, 12, tzinfo=ZURICH),
        datetime(2026, 12, 31, 23, 59, 59, tzinfo=ZURICH),
    ):
        set_clock(current)
        statuses = client.get("/api/me/training-status").json()
        item = next(
            value for value in statuses if value["assignment_id"] == assignment["id"]
        )
        assert item["status"] == "offen"


def test_ac004_personal_status_completed_is_visible():
    client = make_client()
    assignment = assign(client, "module-soziale-dienste")
    complete_round(client, "ma@mail.ch", "module-soziale-dienste")
    set_clock(datetime(2026, 12, 31, 23, 59, 59, tzinfo=ZURICH))
    status = next(
        item
        for item in client.get("/api/me/training-status").json()
        if item["assignment_id"] == assignment["id"]
    )
    assert status["status"] == "erledigt"


def test_personal_status_shows_only_own_attempts():
    client = make_client()
    assignment = assign(client, "module-soziale-dienste")
    complete_round(client, "ma@mail.ch", "module-soziale-dienste")
    login(client, "elina.norveth@grenchen.example")
    status = next(
        item
        for item in client.get("/api/me/training-status").json()
        if item["assignment_id"] == assignment["id"]
    )
    assert status["status"] == "offen"
    assert status["score"] is None


def test_ac005_overdue_status_is_returned():
    client = make_client()
    assignment = assign(client, "module-soziale-dienste", due_date="2026-10-20")
    login(client, "ma@mail.ch")
    set_clock(datetime(2026, 10, 21, 0, 0, tzinfo=ZURICH))
    status = next(
        item
        for item in client.get("/api/me/training-status").json()
        if item["assignment_id"] == assignment["id"]
    )
    assert status["status"] == "Frist überschritten"
    client.post("/api/modules/module-soziale-dienste/rounds", headers=csrf(client))
    status = next(
        item
        for item in client.get("/api/me/training-status").json()
        if item["assignment_id"] == assignment["id"]
    )
    assert status["status"] == "Frist überschritten"


def test_ac006_late_status_is_returned():
    client = make_client()
    assignment = assign(client, "module-soziale-dienste", due_date="2026-10-20")
    set_clock(datetime(2026, 10, 21, 12, tzinfo=ZURICH))
    complete_round(client, "ma@mail.ch", "module-soziale-dienste")
    status = next(
        item
        for item in client.get("/api/me/training-status").json()
        if item["assignment_id"] == assignment["id"]
    )
    assert status["status"] == "verspätet erledigt"


def test_ac007_employee_cannot_read_other_person_status():
    client = make_client()
    login(client, "ma@mail.ch")
    assert (
        client.get(
            "/api/me/training-status?employee_id=user-einwohnerdienste-02"
        ).status_code
        == 403
    )
    client.post("/logout", headers=csrf(client))
    assert client.get("/api/me/training-status").status_code == 401


def test_ac008_department_status_has_no_individual_scores():
    client = make_client()
    login(client, "chef@mail.ch")
    response = client.get(
        "/api/departments/department-einwohnerdienste/training-status"
    )
    assert response.status_code == 200
    allowed = {"offen", "erledigt", "verspätet erledigt", "Frist überschritten"}
    for person in response.json()["persons"]:
        assert set(person) <= {"employee_id", "status", "assignment_id", "module_id"}
        assert person["status"] in allowed
        assert "score" not in person and "errors" not in person


def test_ac009_foreign_department_returns_403():
    client = make_client()
    login(client, "chef@mail.ch")
    assert (
        client.get(
            "/api/departments/department-soziale-dienste/training-status"
        ).status_code
        == 403
    )


def test_ac010_team_aggregation():
    client = make_client()
    for email in (
        "ma@mail.ch",
        "elina.norveth@grenchen.example",
        "tarin.belmar@grenchen.example",
    ):
        complete_round(client, email, "module-einwohnerdienste", score=4)
    login(client, "chef@mail.ch")
    aggregations = client.get(
        "/api/departments/department-einwohnerdienste/training-aggregation"
    ).json()
    aggregation = next(
        item
        for item in aggregations
        if item["assignment_id"] == "assignment-einwohnerdienste"
    )
    assert aggregation["participant_count"] == 3
    assert aggregation["total_score"] == 12
    assert aggregation["total_errors"] == 3
    assert all("employee_id" not in item for item in aggregations)


def test_ac011_small_team_hides_values():
    client = make_client()
    complete_round(
        client, "ma@mail.ch", "module-einwohnerdienste", score=4
    )
    complete_round(
        client, "elina.norveth@grenchen.example", "module-einwohnerdienste", score=4
    )
    login(client, "chef@mail.ch")
    aggregation = client.get(
        "/api/departments/department-einwohnerdienste/training-aggregation"
    ).json()[0]
    assert aggregation["available"] is False
    assert aggregation["message"] == "zu wenige Teilnehmende"
    assert aggregation["total_score"] is None and aggregation["total_errors"] is None
    with app.state.engine.begin() as connection:
        connection.execute(delete(RoundAnswerModel))
        connection.execute(delete(GameRoundScenarioModel))
        connection.execute(delete(GameRoundModel))
    aggregation = client.get(
        "/api/departments/department-einwohnerdienste/training-aggregation"
    ).json()[0]
    assert aggregation["message"] == "zu wenige Teilnehmende"


def test_ac012_officer_sees_overall_evaluation():
    client = make_client()
    login(client, "ds@mail.ch")
    departments = client.get("/api/training/evaluation").json()["departments"]
    assert {item["department_id"] for item in departments} == {
        "department-einwohnerdienste",
        "department-soziale-dienste",
        "department-finanzen-informatik",
    }


def test_ac013_officer_exports_csv():
    client = make_client()
    set_clock(datetime(2026, 10, 21, 14, 5, tzinfo=ZURICH))
    complete_round(client, "ma@mail.ch", "module-einwohnerdienste")
    complete_round(
        client, "elina.norveth@grenchen.example", "module-einwohnerdienste", score=3
    )
    login(client, "ds@mail.ch")
    response = client.get(
        "/api/assignments/assignment-einwohnerdienste/training-evidence.csv"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.content.decode("utf-8-sig")
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert content.splitlines()[0] == (
        "Person;Abteilung;Modul;Versuch;Status;Punktzahl;Bestanden;"
        "Abgeschlossen am;Szenarien"
    )
    assert content.count("\r\n") == 3
    rows = {line.split(";")[0]: line.split(";") for line in content.splitlines()[1:]}
    marek = rows["Marek Dalenor"]
    assert marek[1:8] == [
        "Einwohnerdienste",
        "Datenschutz in den Einwohnerdiensten",
        "1",
        "abgeschlossen",
        "5",
        "ja",
        "21.10.2026 14:05",
    ]
    assert len(marek[8].split("|")) == 5
    assert "scenario-" not in marek[8]
    assert "Am Schalter beantragt eine Person" in marek[8]
    assert rows["Elina Norveth"][5:7] == ["3", "nein"]


def test_ac014_department_lead_cannot_export_csv():
    client = make_client()
    login(client, "chef@mail.ch")
    assert (
        client.get(
            "/api/assignments/assignment-einwohnerdienste/training-evidence.csv"
        ).status_code
        == 403
    )


def test_ac015_status_uses_controlled_clock_contract():
    client = make_client()
    assignment = assign(client, "module-soziale-dienste", due_date="2026-10-20")
    login(client, "ma@mail.ch")
    for current, expected in (
        (datetime(2026, 10, 20, 23, 59, 59, tzinfo=ZURICH), "offen"),
        (datetime(2026, 10, 21, 0, 0, tzinfo=ZURICH), "Frist überschritten"),
    ):
        set_clock(current)
        status = next(
            item
            for item in client.get("/api/me/training-status").json()
            if item["assignment_id"] == assignment["id"]
        )
        assert status["status"] == expected


def test_equal_score_attempts_use_earlier_completion_and_csv_lists_both():
    client = make_client()
    assignment = assign(client, "module-soziale-dienste")
    set_clock(datetime(2026, 10, 21, 14, 5, tzinfo=ZURICH))
    complete_round(
        client, "ma@mail.ch", "module-soziale-dienste", score=4
    )
    set_clock(datetime(2026, 10, 21, 15, 5, tzinfo=ZURICH))
    complete_round(
        client, "ma@mail.ch", "module-soziale-dienste", score=4
    )
    login(client, "ma@mail.ch")
    assert (
        next(
            item
            for item in client.get("/api/me/training-status").json()
            if item["assignment_id"] == assignment["id"]
        )["status"]
        == "erledigt"
    )
    login(client, "ds@mail.ch")
    csv = client.get(
        f"/api/assignments/{assignment['id']}/training-evidence.csv"
    ).content.decode("utf-8-sig")
    assert "21.10.2026 14:05" in csv
    assert "21.10.2026 15:05" in csv


def test_error_contracts_for_all_uc002_endpoints():
    client = make_client()
    for path in (
        "/api/me/training-status",
        "/api/departments/department-einwohnerdienste/training-status",
        "/api/departments/department-einwohnerdienste/training-aggregation",
        "/api/training/evaluation",
        "/api/assignments/assignment-einwohnerdienste/training-evidence.csv",
    ):
        assert client.get(path).status_code == 401
    assert client.post("/api/assignments", json={}).status_code == 401
    login(client, "ds@mail.ch")
    assert (
        client.post(
            "/api/assignments",
            json={
                "module_id": "missing",
                "department_id": "department-einwohnerdienste",
                "due_date": "2026-12-31",
            },
            headers=csrf(client),
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/assignments",
            json={
                "module_id": "module-einwohnerdienste",
                "department_id": "missing",
                "due_date": "2026-12-31",
            },
            headers=csrf(client),
        ).status_code
        == 404
    )
    assert client.get("/api/departments/missing/training-status").status_code == 404
    assert (
        client.get("/api/assignments/missing/training-evidence.csv").status_code == 404
    )
