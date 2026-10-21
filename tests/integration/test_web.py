import re

from fastapi.testclient import TestClient

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
    _login(test_client, "liora.veylan@grenchen.example")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert response.status_code == 403
    assert "Zugriff verweigert" in response.text


def test_html_login_requires_csrf_and_redirects_employee_to_modules():
    test_client = client()
    page = test_client.get("/", headers=HTML_HEADERS)

    missing_csrf = test_client.post(
        "/login",
        data={"email": "marek.dalenor@grenchen.example", "password": "demo-password"},
        headers=HTML_HEADERS,
    )
    logged_in = test_client.post(
        "/login",
        data={
            "email": "marek.dalenor@grenchen.example",
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


def test_html_login_sets_session_cookie_and_logout_clears_access():
    test_client = client()
    test_client.get("/", headers=HTML_HEADERS)

    logged_in = test_client.post(
        "/login",
        data={
            "email": "marek.dalenor@grenchen.example",
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
    _login(test_client, "marek.dalenor@grenchen.example")

    response = test_client.get("/mitarbeitende/module", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert "module-einwohnerdienste" in response.text
    assert "module-soziale-dienste" not in response.text
    assert 'name="csrf_token"' in response.text
    assert "Frist: 2026-11-30" in response.text
    assert "Status:" in response.text
    assert FOOTER in response.text


CORRECT_OPTIONS = {
    "scenario-einwohnerdienste-01": "a",
    "scenario-einwohnerdienste-02": "b",
    "scenario-einwohnerdienste-03": "c",
    "scenario-einwohnerdienste-04": "d",
    "scenario-einwohnerdienste-05": "a",
}
ROUND_PAGE = "/mitarbeitende/module/module-einwohnerdienste"


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
    _login(test_client, "marek.dalenor@grenchen.example")
    previous = test_client.get(ROUND_PAGE, headers=HTML_HEADERS)
    _play_open_round(test_client, previous.text)

    round_page = test_client.get(ROUND_PAGE, headers=HTML_HEADERS)

    assert round_page.status_code == 200
    assert _hidden(round_page.text, "position") == "1"
    assert "Am Schalter beantragt" in round_page.text
    assert 'type="radio"' in round_page.text
    assert 'name="csrf_token"' in round_page.text

    responses = _play_open_round(
        test_client, round_page.text, wrong_scenario="scenario-einwohnerdienste-02"
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
    _login(test_client, "marek.dalenor@grenchen.example")
    round_page = test_client.get(ROUND_PAGE, headers=HTML_HEADERS)

    response = test_client.post(
        f"/mitarbeitende/runden/{_hidden(round_page.text, 'round_id')}/antworten",
        data={"position": _hidden(round_page.text, "position"), "option_id": "a"},
        headers=HTML_HEADERS,
    )

    assert response.status_code == 403


def test_html_assignment_form_requires_csrf():
    test_client = client()
    _login(test_client, "yara.merovan@grenchen.example")

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
    _login(test_client, "yara.merovan@grenchen.example")
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


def test_html_department_lead_page_has_status_without_individual_scores():
    test_client = client()
    _login(test_client, "liora.veylan@grenchen.example")

    response = test_client.get(
        "/abteilungsleitung/auswertung", headers=HTML_HEADERS
    )

    assert response.status_code == 200
    assert "Abteilungsstatus" in response.text
    assert "score" not in response.text.lower()
    assert "total_score" not in response.text
    assert "module-einwohnerdienste" in response.text


def test_html_data_protection_pages_show_assignment_form_and_csv_links():
    test_client = client()
    _login(test_client, "yara.merovan@grenchen.example")

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


def test_html_errors_render_status_pages_without_data_leaks():
    test_client = client()
    _login(test_client, "marek.dalenor@grenchen.example")

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