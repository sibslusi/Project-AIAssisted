"""Smoke-Test gegen eine laufende Instanz, lokal im Release-Job oder auf Render.

Konfiguration über Umgebungsvariablen: BASE_URL (Pflicht), EXPECTED_VERSION,
SMOKE_EMAIL und DEMO_PASSWORD (nur zusammen), SMOKE_TIMEOUT_SECONDS.
"""

import os
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from http.cookies import SimpleCookie

import httpx

RETRY_INTERVAL_SECONDS = 10.0


class SmokeTestError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    base_url: str
    expected_version: str | None
    email: str | None
    password: str | None
    timeout_seconds: float


def load_config(env: Mapping[str, str]) -> Config:
    base_url = env.get("BASE_URL", "").rstrip("/")
    if not base_url:
        raise SmokeTestError("BASE_URL muss gesetzt sein")
    email = env.get("SMOKE_EMAIL") or None
    password = env.get("DEMO_PASSWORD") or None
    if (email is None) != (password is None):
        raise SmokeTestError("SMOKE_EMAIL und DEMO_PASSWORD nur zusammen setzen")
    return Config(
        base_url=base_url,
        expected_version=env.get("EXPECTED_VERSION") or None,
        email=email,
        password=password,
        timeout_seconds=float(env.get("SMOKE_TIMEOUT_SECONDS", "600")),
    )


def wait_for_health(
    client: httpx.Client,
    expected_version: str | None,
    timeout_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict:
    deadline = monotonic() + timeout_seconds
    while True:
        try:
            response = client.get("/health")
            if response.status_code == 200:
                payload = response.json()
                version = payload.get("version")
                if expected_version is None or version == expected_version:
                    return payload
                problem = f"Version {version!r} statt {expected_version!r}"
            else:
                problem = f"HTTP {response.status_code}"
        except httpx.HTTPError as error:
            problem = type(error).__name__
        if monotonic() >= deadline:
            raise SmokeTestError(f"/health nicht bereit: {problem}")
        sleep(RETRY_INTERVAL_SECONDS)


def _cookies(response: httpx.Response) -> dict[str, str]:
    # Die App setzt Secure-Cookies. Über http://localhost würde httpx sie nicht
    # zurückschicken, darum lesen wir sie selbst aus den Set-Cookie-Headern.
    jar = SimpleCookie()
    for header in response.headers.get_list("set-cookie"):
        jar.load(header)
    return {name: morsel.value for name, morsel in jar.items()}


def _cookie_header(cookies: Mapping[str, str]) -> dict[str, str]:
    return {"Cookie": "; ".join(f"{name}={value}" for name, value in cookies.items())}


def _expect(response: httpx.Response, step: str) -> None:
    if response.status_code != 200:
        raise SmokeTestError(f"{step}: HTTP {response.status_code}")


def check_login(client: httpx.Client, email: str, password: str) -> None:
    page = client.get("/login")
    _expect(page, "GET /login")
    cookies = _cookies(page)
    login = client.post(
        "/login",
        data={
            "email": email,
            "password": password,
            "csrf_token": page.json()["csrf_token"],
        },
        headers=_cookie_header(cookies),
    )
    _expect(login, "POST /login")
    cookies.update(_cookies(login))
    _expect(
        client.get("/api/modules", headers=_cookie_header(cookies)),
        "GET /api/modules",
    )


def main(
    env: Mapping[str, str] = os.environ,
    transport: httpx.BaseTransport | None = None,
) -> int:
    try:
        config = load_config(env)
        with httpx.Client(
            base_url=config.base_url, timeout=10.0, transport=transport
        ) as client:
            payload = wait_for_health(
                client, config.expected_version, config.timeout_seconds
            )
            print(f"/health ok, Version {payload.get('version')}")
            if config.email and config.password:
                check_login(client, config.email, config.password)
                print(f"Login und /api/modules ok für {config.email}")
    except SmokeTestError as error:
        print(f"Smoke-Test fehlgeschlagen: {error}", file=sys.stderr)
        return 1
    print("Smoke-Test bestanden")
    return 0


if __name__ == "__main__":
    sys.exit(main())
