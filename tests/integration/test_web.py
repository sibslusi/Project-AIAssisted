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