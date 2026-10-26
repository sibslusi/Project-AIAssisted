import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.models import GameRoundModel
from app.interfaces.web import templates
from app.main import app

HTML_HEADERS = {"accept": "text/html"}
FOOTER = "Schulungsplattform mit fiktiven Daten. Keine Rechtsberatung."


def client() -> TestClient:
    return TestClient(app, base_url="https://testserver")


def test_home_page_contains_login_form_csrf_and_required_footer():
    response = client().get("/", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert '<form action="/login" method="post">' in response.text
    assert 'name="csrf_token"' in response.text
    assert FOOTER in response.text


def test_html_employee_modules_page_is_denied_for_department_lead():
    test_client = client()
    _login(test_client, "chef@mail.ch")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert response.status_code == 403
    assert "Zugriff verweigert" in response.text


def test_html_login_requires_csrf_and_redirects_employee_to_modules():
    test_client = client()
    page = test_client.get("/", headers=HTML_HEADERS)

    missing_csrf = test_client.post(
        "/login",
        data={"email": "ma@mail.ch", "password": "demo-password"},
        headers=HTML_HEADERS,
    )
    logged_in = test_client.post(
        "/login",
        data={
            "email": "ma@mail.ch",
            "password": "demo-password",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
        follow_redirects=False,
    )

    assert page.status_code == 200
    assert missing_csrf.status_code == 403
    assert logged_in.status_code == 303
    assert logged_in.headers["location"] == "/mitarbeitende/module"


@pytest.mark.parametrize(
    ("email", "location"),
    [
        (" Ma@Mail.ch ", "/mitarbeitende/module"),
        ("chef@MAIL.ch", "/abteilungsleitung/auswertung"),
        ("DS@mail.ch", "/datenschutz/auswertung"),
    ],
)
def test_demo_login_aliases_are_case_insensitive(email, location):
    test_client = client()
    page = test_client.get("/", headers=HTML_HEADERS)

    response = test_client.post(
        "/login",
        data={
            "email": email,
            "password": "demo-password",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
        follow_redirects=False,
    )

    assert page.status_code == 200
    assert response.status_code == 303
    assert response.headers["location"] == location


def test_old_demo_email_is_rejected():
    test_client = client()
    test_client.get("/", headers=HTML_HEADERS)

    response = test_client.post(
        "/login",
        data={
            "email": "marek.dalenor@grenchen.example",
            "password": "demo-password",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
    )

    assert response.status_code == 401


def test_html_login_sets_session_cookie_and_logout_clears_access():
    test_client = client()
    test_client.get("/", headers=HTML_HEADERS)

    logged_in = test_client.post(
        "/login",
        data={
            "email": "ma@mail.ch",
            "password": "demo-password",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
        follow_redirects=False,
    )

    assert logged_in.status_code == 303
    session_cookie = next(
        cookie
        for cookie in logged_in.headers.get_list("set-cookie")
        if cookie.startswith("session=")
    )
    assert "HttpOnly" in session_cookie
    assert "Secure" in session_cookie
    modules = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)
    assert modules.status_code == 200

    logged_out = test_client.post(
        "/logout",
        data={"csrf_token": test_client.cookies["csrf_token"]},
        headers=HTML_HEADERS,
        follow_redirects=False,
    )

    assert logged_out.status_code == 303
    assert any(
        cookie.startswith("session=") and "Max-Age=0" in cookie
        for cookie in logged_out.headers.get_list("set-cookie")
    )
    modules = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)
    assert modules.status_code == 401


def test_home_page_redirects_logged_in_user_to_role_start_page():
    test_client = client()
    _login(test_client, "chef@mail.ch")

    response = test_client.get("/", headers=HTML_HEADERS, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/abteilungsleitung/auswertung"


def test_html_logout_requires_csrf():
    test_client = client()
    test_client.get("/", headers=HTML_HEADERS)

    response = test_client.post("/logout", headers=HTML_HEADERS)

    assert response.status_code == 403


def _login(test_client: TestClient, email: str) -> None:
    page = test_client.get("/", headers=HTML_HEADERS)
    response = test_client.post(
        "/login",
        data={
            "email": email,
            "password": "demo-password",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert page.status_code == 200


def test_html_employee_page_shows_only_assigned_modules_and_csrf_forms():
    test_client = client()
    _login(test_client, "ma@mail.ch")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert "module-einwohnerdienste" in response.text
    assert "module-soziale-dienste" not in response.text
    assert 'name="csrf_token"' in response.text
    assert "Datenschutz in den Einwohnerdiensten" in response.text
    assert "Frist: 2026-11-30" in response.text
    assert "Status:" in response.text
    assert FOOTER in response.text


def test_employee_navigation_marks_modules_as_active():
    test_client = client()
    _login(test_client, "ma@mail.ch")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert '<nav class="main-nav"' in response.text
    assert 'aria-current="page"' in response.text
    assert 'href="/mitarbeitende/module"' in response.text
    assert "Meine Module" in response.text


def test_data_protection_navigation_contains_evaluation_and_assignments():
    test_client = client()
    _login(test_client, "ds@mail.ch")

    response = test_client.get("/datenschutz/zuweisungen", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert response.text.count('class="nav-link active"') == 1
    assert 'href="/datenschutz/zuweisungen"' in response.text
    assert 'aria-current="page"' in response.text
    assert "Zuweisungen" in response.text


def test_employee_navigation_excludes_data_protection_links_and_shows_role():
    test_client = client()
    _login(test_client, "ma@mail.ch")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert 'href="/datenschutz/zuweisungen"' not in response.text
    assert "Mitarbeitende" in response.text
    assert "modules" not in response.text


def test_department_lead_navigation_marks_status_active_without_global_evaluation():
    test_client = client()
    _login(test_client, "chef@mail.ch")

    response = test_client.get("/abteilungsleitung/auswertung", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert "Abteilungsstatus" in response.text
    assert 'aria-current="page"' in response.text
    assert "Gesamtauswertung" not in response.text
    assert "Abteilungsleitung" in response.text


def test_login_page_has_no_authenticated_navigation():
    response = client().get("/", headers=HTML_HEADERS)

    assert '<nav class="main-nav"' not in response.text
    assert "Abmelden" not in response.text


def test_module_status_is_rendered_as_status_pill():
    test_client = client()
    _login(test_client, "ma@mail.ch")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert re.search(r'class="pill pill-(open|done|overdue)"', response.text)
    assert re.search(
        r">(offen|erledigt|verspätet erledigt|Frist überschritten)<", response.text
    )


def test_desktop_layout_uses_minimum_width_and_no_mobile_media_query():
    css = (
        Path(__file__).parents[2] / "src/app/interfaces/static/style.css"
    ).read_text()

    assert "min-width: 1024px" not in css
    assert "@media (max-width" not in css
    assert "--content-max" in css
    assert "clamp(" in css


def test_module_cards_render_exactly_one_status_pill_each():
    test_client = client()
    _login(test_client, "ma@mail.ch")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert response.text.count('class="module-card-heading"') == 1
    assert response.text.count('class="pill ') == 1


def test_late_status_uses_late_status_pill():
    macro = templates.env.get_template("macros.html").module

    rendered = macro.status_pill("verspätet erledigt")

    assert 'class="pill pill-late"' in rendered
    assert "verspätet erledigt" in rendered


def test_evaluation_tables_use_scrollable_table_wrapper():
    lead = client()
    _login(lead, "chef@mail.ch")
    department = lead.get("/abteilungsleitung/auswertung", headers=HTML_HEADERS)

    officer = client()
    _login(officer, "ds@mail.ch")
    evaluation = officer.get("/datenschutz/auswertung", headers=HTML_HEADERS)

    assert 'class="table-wrap"' in department.text
    assert 'class="table-wrap"' in evaluation.text


def test_role_and_department_are_visible_in_header():
    test_client = client()
    _login(test_client, "ma@mail.ch")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert "Mitarbeitende" in response.text
    assert "Einwohnerdienste" in response.text


def test_role_restricted_html_routes_render_error_pages():
    test_client = client()
    _login(test_client, "chef@mail.ch")
    csrf = test_client.cookies["csrf_token"]

    assert test_client.get(ROUND_PAGE, headers=HTML_HEADERS).status_code == 403
    assert (
        test_client.post(
            START_ROUND,
            data={"csrf_token": csrf},
            headers=HTML_HEADERS,
        ).status_code
        == 403
    )
    assert (
        test_client.get("/datenschutz/auswertung", headers=HTML_HEADERS).status_code
        == 403
    )
    assert (
        test_client.get("/datenschutz/zuweisungen", headers=HTML_HEADERS).status_code
        == 403
    )


def test_invalid_html_round_requests_render_error_pages():
    test_client = client()
    _login(test_client, "ma@mail.ch")
    csrf = test_client.cookies["csrf_token"]

    assert (
        test_client.get(
            "/mitarbeitende/module/module-soziale-dienste", headers=HTML_HEADERS
        ).status_code
        == 404
    )
    assert (
        test_client.post(
            "/mitarbeitende/runden/missing/antworten",
            data={"csrf_token": csrf, "position": 1, "option_id": "a"},
            headers=HTML_HEADERS,
        ).status_code
        == 404
    )


def test_invalid_html_assignment_requests_render_error_pages():
    test_client = client()
    _login(test_client, "ds@mail.ch")
    csrf = test_client.cookies["csrf_token"]

    assert (
        test_client.post(
            "/datenschutz/zuweisungen",
            data={
                "csrf_token": csrf,
                "module_id": "module-einwohnerdienste",
                "department_id": "department-einwohnerdienste",
                "due_date": "not-a-date",
            },
            headers=HTML_HEADERS,
        ).status_code
        == 422
    )
    assert (
        test_client.post(
            "/datenschutz/zuweisungen",
            data={
                "csrf_token": csrf,
                "module_id": "missing",
                "department_id": "department-einwohnerdienste",
                "due_date": "2026-12-31",
            },
            headers=HTML_HEADERS,
        ).status_code
        == 404
    )


CORRECT_OPTIONS = {
    "scenario-einwohnerdienste-01": "a",
    "scenario-einwohnerdienste-02": "b",
    "scenario-einwohnerdienste-03": "c",
    "scenario-einwohnerdienste-04": "d",
    "scenario-einwohnerdienste-05": "a",
}
ROUND_PAGE = "/mitarbeitende/module/module-einwohnerdienste"
START_ROUND = f"{ROUND_PAGE}/runden"


def _start_round(test_client: TestClient) -> str:
    response = test_client.post(
        START_ROUND,
        data={"csrf_token": test_client.cookies["csrf_token"]},
        headers=HTML_HEADERS,
    )
    assert response.status_code == 200
    return response.text


def _round_count(employee_id: str) -> int:
    with Session(app.state.engine) as session:
        return session.scalar(
            select(func.count())
            .select_from(GameRoundModel)
            .where(GameRoundModel.employee_id == employee_id)
        )


def _hidden(html: str, name: str) -> str | None:
    match = re.search(rf'name="{name}" value="([^"]+)"', html)
    return match.group(1) if match else None


def _play_open_round(test_client: TestClient, html: str, wrong_scenario=None):
    responses = []
    while _hidden(html, "round_id") is not None:
        scenario_id = _hidden(html, "scenario_id")
        option_id = CORRECT_OPTIONS[scenario_id]
        if scenario_id == wrong_scenario:
            option_id = "a" if option_id != "a" else "b"
        response = test_client.post(
            f"/mitarbeitende/runden/{_hidden(html, 'round_id')}/antworten",
            data={
                "position": _hidden(html, "position"),
                "option_id": option_id,
                "csrf_token": test_client.cookies["csrf_token"],
            },
            headers=HTML_HEADERS,
        )
        assert response.status_code == 200
        responses.append(response)
        html = response.text
    return responses


def test_html_employee_can_play_round_with_feedback_and_badge():
    test_client = client()
    _login(test_client, "ma@mail.ch")
    _play_open_round(test_client, _start_round(test_client))

    round_page = _start_round(test_client)

    assert _hidden(round_page, "position") == "1"
    assert "Am Schalter beantragt" in round_page
    assert 'type="radio"' in round_page
    assert 'name="csrf_token"' in round_page

    responses = _play_open_round(
        test_client, round_page, wrong_scenario="scenario-einwohnerdienste-02"
    )

    assert len(responses) == 5
    assert "Falsch" in responses[1].text
    for response in responses:
        assert "Erklärung" in response.text
        assert "Rechtsgrundlage" in response.text
    assert "Richtig" in responses[0].text
    assert "Punktzahl: 4/5" in responses[-1].text
    assert "Ergebnis: bestanden" in responses[-1].text
    assert "Abzeichen" in responses[-1].text
    modules = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)
    assert "Abzeichen" in modules.text
    assert re.search(r"Bester Versuch: [45]/5", modules.text)


def test_html_answer_requires_csrf():
    test_client = client()
    _login(test_client, "ma@mail.ch")
    round_page = _start_round(test_client)

    response = test_client.post(
        f"/mitarbeitende/runden/{_hidden(round_page, 'round_id')}/antworten",
        data={"position": _hidden(round_page, "position"), "option_id": "a"},
        headers=HTML_HEADERS,
    )
    _play_open_round(test_client, round_page)

    assert response.status_code == 403


def test_html_round_page_get_never_creates_a_round():
    test_client = client()
    _login(test_client, "ma@mail.ch")
    _play_open_round(test_client, _start_round(test_client))
    before = _round_count("user-einwohnerdienste-01")

    response = test_client.get(ROUND_PAGE, headers=HTML_HEADERS, follow_redirects=False)
    modules = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert response.status_code == 303
    assert response.headers["location"] == "/mitarbeitende/module"
    assert _round_count("user-einwohnerdienste-01") == before
    assert f'<form action="{START_ROUND}" method="post">' in modules.text
    assert "Neue Runde starten" in modules.text
    assert "Runde fortsetzen" not in modules.text


def test_html_start_round_requires_csrf():
    test_client = client()
    _login(test_client, "ma@mail.ch")
    _play_open_round(test_client, _start_round(test_client))
    before = _round_count("user-einwohnerdienste-01")

    response = test_client.post(START_ROUND, headers=HTML_HEADERS)

    assert response.status_code == 403
    assert _round_count("user-einwohnerdienste-01") == before


def test_html_open_round_is_continued_from_module_list():
    test_client = client()
    _login(test_client, "ma@mail.ch")
    started = _start_round(test_client)

    modules = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)
    resumed = test_client.get(ROUND_PAGE, headers=HTML_HEADERS)
    _play_open_round(test_client, started)

    assert f'<a href="{ROUND_PAGE}">Runde fortsetzen</a>' in modules.text
    assert "Neue Runde starten" not in modules.text
    assert resumed.status_code == 200
    assert _hidden(resumed.text, "round_id") == _hidden(started, "round_id")


def test_html_assignment_form_requires_csrf():
    test_client = client()
    _login(test_client, "ds@mail.ch")

    response = test_client.post(
        "/datenschutz/zuweisungen",
        data={
            "module_id": "module-finanzen-informatik",
            "department_id": "department-finanzen-informatik",
            "due_date": "2026-12-15",
        },
        headers=HTML_HEADERS,
    )

    assert response.status_code == 403


def test_html_data_protection_officer_can_submit_assignment_form():
    test_client = client()
    _login(test_client, "ds@mail.ch")
    test_client.get("/datenschutz/zuweisungen", headers=HTML_HEADERS)

    response = test_client.post(
        "/datenschutz/zuweisungen",
        data={
            "module_id": "module-finanzen-informatik",
            "department_id": "department-finanzen-informatik",
            "due_date": "2026-12-15",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/datenschutz/zuweisungen"


def test_html_assignment_form_rejects_due_date_in_the_past():
    test_client = client()
    _login(test_client, "ds@mail.ch")
    test_client.get("/datenschutz/zuweisungen", headers=HTML_HEADERS)

    response = test_client.post(
        "/datenschutz/zuweisungen",
        data={
            "module_id": "module-finanzen-informatik",
            "department_id": "department-finanzen-informatik",
            "due_date": "2020-01-01",
            "csrf_token": test_client.cookies["csrf_token"],
        },
        headers=HTML_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert (
        "2020-01-01"
        not in test_client.get("/datenschutz/zuweisungen", headers=HTML_HEADERS).text
    )


def test_html_department_lead_page_has_status_without_individual_scores():
    test_client = client()
    _login(test_client, "chef@mail.ch")

    response = test_client.get("/abteilungsleitung/auswertung", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert "Abteilungsstatus" in response.text
    assert "score" not in response.text.lower()
    assert "total_score" not in response.text
    assert "Marek Dalenor" in response.text
    assert "user-einwohnerdienste-01" not in response.text
    assert "Datenschutz in den Einwohnerdiensten" in response.text
    assert "Jorin Mavero" not in response.text


def test_html_data_protection_pages_show_assignment_form_and_csv_links():
    test_client = client()
    _login(test_client, "ds@mail.ch")

    assignments = test_client.get("/datenschutz/zuweisungen", headers=HTML_HEADERS)
    evaluation = test_client.get("/datenschutz/auswertung", headers=HTML_HEADERS)

    assert assignments.status_code == 200
    assert evaluation.status_code == 200
    assert 'name="module_id"' in assignments.text
    assert 'name="department_id"' in assignments.text
    assert 'name="due_date"' in assignments.text
    assert 'name="csrf_token"' in assignments.text
    csv_link = "/api/assignments/assignment-einwohnerdienste/training-evidence.csv"
    assert csv_link in assignments.text
    assert "Gesamtauswertung" in evaluation.text
    assert "Soziale Dienste" in evaluation.text
    assert "Jorin Mavero" in evaluation.text
    assert ">Datenschutz in den Einwohnerdiensten</option>" in assignments.text
    assert ">Einwohnerdienste</option>" in assignments.text


def test_html_errors_render_status_pages_without_data_leaks():
    test_client = client()
    _login(test_client, "ma@mail.ch")

    foreign = test_client.get(
        "/mitarbeitende/module/module-soziale-dienste", headers=HTML_HEADERS
    )
    missing = test_client.get(
        "/mitarbeitende/module/module-unbekannt", headers=HTML_HEADERS
    )

    assert foreign.status_code == 404
    assert missing.status_code == 404
    assert "scenario-" not in foreign.text
    assert "Modul nicht gefunden" in missing.text
    assert FOOTER in missing.text
