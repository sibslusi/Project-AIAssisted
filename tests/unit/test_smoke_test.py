import importlib.util
from pathlib import Path

import httpx
import pytest

SCRIPT = Path(__file__).parents[2] / "scripts" / "smoke_test.py"
spec = importlib.util.spec_from_file_location("smoke_test", SCRIPT)
smoke_test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke_test)


class FakeTime:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def client(handler):
    return httpx.Client(
        base_url="http://localhost:8000", transport=httpx.MockTransport(handler)
    )


def health_sequence(*responses):
    remaining = list(responses)

    def handler(request):
        assert request.url.path == "/health"
        status, body = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return httpx.Response(status, json=body)

    return handler


def wait(handler, expected_version=None, timeout_seconds=60):
    fake = FakeTime()
    return smoke_test.wait_for_health(
        client(handler),
        expected_version,
        timeout_seconds,
        sleep=fake.sleep,
        monotonic=fake.monotonic,
    )


def test_health_ok_returns_payload():
    handler = health_sequence((200, {"status": "ok", "version": "v1"}))

    assert wait(handler, "v1") == {"status": "ok", "version": "v1"}


def test_health_retries_until_service_is_ready():
    handler = health_sequence(
        (502, {"detail": "starting"}), (200, {"status": "ok", "version": "v2"})
    )

    assert wait(handler, "v2")["version"] == "v2"


def test_health_fails_when_version_never_matches():
    handler = health_sequence((200, {"status": "ok", "version": "v1"}))

    with pytest.raises(smoke_test.SmokeTestError, match="v1"):
        wait(handler, "v2", timeout_seconds=30)


def login_handler(login_status=200, modules_status=200):
    seen = {}

    def handler(request):
        cookies = request.headers.get("cookie", "")
        if request.method == "GET" and request.url.path == "/login":
            return httpx.Response(
                200,
                json={"csrf_token": "token-1"},
                headers={"set-cookie": "csrf_token=token-1; Secure; Path=/"},
            )
        if request.method == "POST" and request.url.path == "/login":
            seen["login_cookie"] = cookies
            seen["login_body"] = request.content.decode()
            if login_status != 200:
                return httpx.Response(login_status, json={"detail": "nein"})
            return httpx.Response(
                200,
                json={"status": "ok"},
                headers=[
                    ("set-cookie", "session=abc; HttpOnly; Secure; Path=/"),
                    ("set-cookie", "csrf_token=token-2; Secure; Path=/"),
                ],
            )
        if request.url.path == "/api/modules":
            seen["modules_cookie"] = cookies
            return httpx.Response(modules_status, json=[])
        raise AssertionError(request.url)

    return handler, seen


def test_login_sends_secure_cookies_itself_and_reads_modules():
    handler, seen = login_handler()

    smoke_test.check_login(client(handler), "ma@mail.ch", "geheim")

    assert "csrf_token=token-1" in seen["login_cookie"]
    assert "csrf_token=token-1" in seen["login_body"]
    assert "session=abc" in seen["modules_cookie"]


def test_login_rejected_is_an_error_without_password_in_message():
    handler, _ = login_handler(login_status=401)

    with pytest.raises(smoke_test.SmokeTestError) as error:
        smoke_test.check_login(client(handler), "ma@mail.ch", "geheim")

    assert "401" in str(error.value)
    assert "geheim" not in str(error.value)


def test_modules_not_available_after_login_is_an_error():
    handler, _ = login_handler(modules_status=500)

    with pytest.raises(smoke_test.SmokeTestError, match="500"):
        smoke_test.check_login(client(handler), "ma@mail.ch", "geheim")


def test_config_requires_base_url():
    with pytest.raises(smoke_test.SmokeTestError, match="BASE_URL"):
        smoke_test.load_config({})


@pytest.mark.parametrize(
    "env", [{"SMOKE_EMAIL": "ma@mail.ch"}, {"DEMO_PASSWORD": "geheim"}]
)
def test_config_requires_email_and_password_together(env):
    with pytest.raises(smoke_test.SmokeTestError, match="SMOKE_EMAIL"):
        smoke_test.load_config({"BASE_URL": "http://localhost:8000", **env})


def test_config_defaults():
    config = smoke_test.load_config({"BASE_URL": "https://demo.example/"})

    assert config.base_url == "https://demo.example"
    assert config.expected_version is None
    assert config.email is None
    assert config.timeout_seconds == 600


def test_main_returns_one_and_hides_password(capsys):
    env = {
        "BASE_URL": "http://localhost:8000",
        "SMOKE_EMAIL": "ma@mail.ch",
        "DEMO_PASSWORD": "geheim",
        "SMOKE_TIMEOUT_SECONDS": "0",
    }
    handler, _ = login_handler(login_status=401)

    def health_then_login(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "version": "dev"})
        return handler(request)

    result = smoke_test.main(env, transport=httpx.MockTransport(health_then_login))

    output = capsys.readouterr()
    assert result == 1
    assert "geheim" not in output.out + output.err


def test_main_returns_zero_when_everything_works():
    handler, _ = login_handler()

    def health_then_login(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "version": "v3"})
        return handler(request)

    env = {
        "BASE_URL": "http://localhost:8000",
        "EXPECTED_VERSION": "v3",
        "SMOKE_EMAIL": "ma@mail.ch",
        "DEMO_PASSWORD": "geheim",
    }

    assert smoke_test.main(env, transport=httpx.MockTransport(health_then_login)) == 0
