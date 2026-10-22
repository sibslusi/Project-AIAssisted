import re

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import AssignmentModel
from app.main import app

HTML_HEADERS = {"accept": "text/html"}
ROUND_PAGE = "/mitarbeitende/module/module-einwohnerdienste"
CORRECT_OPTIONS = {
    "scenario-einwohnerdienste-01": "a",
    "scenario-einwohnerdienste-02": "b",
    "scenario-einwohnerdienste-03": "c",
    "scenario-einwohnerdienste-04": "d",
    "scenario-einwohnerdienste-05": "a",
}


def client() -> TestClient:
    return TestClient(app, base_url="https://testserver")


def hidden(html: str, name: str) -> str | None:
    match = re.search(rf'name="{name}" value="([^"]+)"', html)
    return match.group(1) if match else None


def login(test_client: TestClient, email: str) -> None:
    test_client.get("/", headers=HTML_HEADERS)
    response = test_client.post(
        "/login",
        data={
            "email": email,
            "password": "demo-password",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
    )
    assert response.status_code == 200


def logout(test_client: TestClient) -> None:
    response = test_client.post(
        "/logout",
        data={"csrf_token": test_client.cookies["csrf_token"]},
        headers=HTML_HEADERS,
    )
    assert response.status_code == 200
    assert 'action="/login"' in response.text


def play_round(test_client: TestClient, html: str) -> str:
    while hidden(html, "round_id") is not None:
        response = test_client.post(
            f"/mitarbeitende/runden/{hidden(html, 'round_id')}/antworten",
            data={
                "position": hidden(html, "position"),
                "option_id": CORRECT_OPTIONS[hidden(html, "scenario_id")],
                "csrf_token": test_client.cookies["csrf_token"],
            },
            headers=HTML_HEADERS,
        )
        assert response.status_code == 200
        html = response.text
    return html


def start_round(test_client: TestClient) -> str:
    response = test_client.post(
        f"{ROUND_PAGE}/runden",
        data={"csrf_token": test_client.cookies["csrf_token"]},
        headers=HTML_HEADERS,
    )
    assert response.status_code == 200
    return response.text


def test_employee_plays_round_sees_badge_and_logs_out():
    test_client = client()
    login(test_client, "ma@mail.ch")
    play_round(test_client, start_round(test_client))

    result = play_round(test_client, start_round(test_client))

    assert "Punktzahl: 5/5" in result
    assert "Ergebnis: bestanden" in result
    assert "Abzeichen" in result
    logout(test_client)
    modules = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)
    assert modules.status_code == 401


def test_department_lead_sees_no_individual_scores():
    test_client = client()
    login(test_client, "chef@mail.ch")

    response = test_client.get("/abteilungsleitung/auswertung", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert "Abteilungsstatus" in response.text
    assert "Bester Versuch" not in response.text
    assert "/5" not in response.text
    logout(test_client)


def test_data_protection_officer_assigns_module_and_downloads_csv():
    test_client = client()
    login(test_client, "ds@mail.ch")
    test_client.get("/datenschutz/zuweisungen", headers=HTML_HEADERS)

    try:
        created = test_client.post(
            "/datenschutz/zuweisungen",
            data={
                "module_id": "module-soziale-dienste",
                "department_id": "department-finanzen-informatik",
                "due_date": "2026-12-31",
                "csrf_token": test_client.cookies["csrf_token"],
            },
            headers=HTML_HEADERS,
        )
        links = re.findall(r'href="(/api/assignments/[^"]+\.csv)"', created.text)
        evidence = test_client.get(links[-1])
    finally:
        with Session(app.state.engine) as session:
            for assignment in session.scalars(
                select(AssignmentModel).where(
                    AssignmentModel.module_id == "module-soziale-dienste",
                    AssignmentModel.department_id == "department-finanzen-informatik",
                )
            ):
                session.delete(assignment)
            session.commit()

    assert created.status_code == 200
    assert "Zuweisungen" in created.text
    assert evidence.status_code == 200
    assert evidence.headers["content-type"].startswith("text/csv")
    logout(test_client)


def test_every_html_post_without_csrf_returns_403():
    test_client = client()
    login(test_client, "ma@mail.ch")
    round_page = start_round(test_client)
    posts = {
        "/login": {"email": "x@grenchen.example", "password": "x"},
        "/logout": {},
        f"{ROUND_PAGE}/runden": {},
        f"/mitarbeitende/runden/{hidden(round_page, 'round_id')}/antworten": {
            "position": hidden(round_page, "position"),
            "option_id": "a",
        },
        "/datenschutz/zuweisungen": {
            "module_id": "module-einwohnerdienste",
            "department_id": "department-einwohnerdienste",
            "due_date": "2026-12-31",
        },
    }

    statuses = {
        url: test_client.post(url, data=data, headers=HTML_HEADERS).status_code
        for url, data in posts.items()
    }
    play_round(test_client, round_page)

    assert statuses == dict.fromkeys(posts, 403)
