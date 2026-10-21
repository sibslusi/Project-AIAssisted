from fastapi.testclient import TestClient

from app.main import app


HTML_HEADERS = {"accept": "text/html"}


def client() -> TestClient:
    return TestClient(app, base_url="https://testserver")


def test_home_page_contains_login_form_csrf_and_required_footer():
    response = client().get("/", headers=HTML_HEADERS)

    assert response.status_code == 200
    assert '<form action="/login" method="post">' in response.text
    assert 'name="csrf_token"' in response.text
    assert "Schulungsplattform mit fiktiven Daten. Keine Rechtsberatung." in response.text


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
    assert "Schulungsplattform mit fiktiven Daten. Keine Rechtsberatung." in response.text


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
    assert "/api/assignments/assignment-einwohnerdienste/training-evidence.csv" in assignments.text
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
    assert "Schulungsplattform mit fiktiven Daten. Keine Rechtsberatung." in missing.text