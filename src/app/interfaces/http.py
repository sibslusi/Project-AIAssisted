import secrets
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, FastAPI, Form, Request, Response
from fastapi.responses import JSONResponse
from itsdangerous import BadSignature, URLSafeSerializer

from app.application.models import Actor, Role
from app.application.use_cases import (
    AccessDenied,
    GetTrainingProgress,
    ListAssignedModules,
    NotFound,
    StartOrResumeGameRound,
    SubmitRoundAnswer,
)


@dataclass(frozen=True)
class Services:
    session_factory: Callable[[], Any]
    assignment_repository: Callable[[Any], Any]
    scenario_repository: Callable[[Any], Any]
    game_round_repository: Callable[[Any], Any]
    authenticate: Callable[[Any, str, str], Actor | None]
    session_secret: str


class HTTPExceptionResponse(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


router = APIRouter()


def _services(request: Request) -> Services:
    return request.app.state.services


@contextmanager
def _session(request: Request):
    session = _services(request).session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _csrf(response: Response) -> str:
    token = secrets.token_urlsafe(24)
    response.set_cookie(
        "csrf_token", token, httponly=False, secure=True, samesite="lax"
    )
    return token


def _actor(request: Request) -> Actor | None:
    value = request.cookies.get("session")
    if value is None:
        return None
    try:
        data = URLSafeSerializer(
            _services(request).session_secret, salt="session"
        ).loads(value)
    except BadSignature:
        return None
    return Actor(data["id"], Role(data["role"]), data["department_id"])


def _require_actor(request: Request) -> Actor:
    actor = _actor(request)
    if actor is None:
        raise HTTPExceptionResponse(401, "Nicht angemeldet")
    return actor


def _check_csrf(request: Request) -> None:
    if request.cookies.get("csrf_token") != request.headers.get("X-CSRF-Token"):
        raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/login")
def login_form(response: Response):
    return {"csrf_token": _csrf(response)}


@router.post("/login")
def login(
    request: Request,
    response: Response,
    email: str = Form(),
    password: str = Form(),
    csrf_token: str = Form(),
):
    if csrf_token != request.cookies.get("csrf_token"):
        raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")
    with _session(request) as session:
        actor = _services(request).authenticate(session, email, password)
    if actor is None:
        raise HTTPExceptionResponse(401, "Ungültige Anmeldung")
    value = URLSafeSerializer(_services(request).session_secret, salt="session").dumps(
        {"id": actor.id, "role": actor.role, "department_id": actor.department_id}
    )
    response.set_cookie("session", value, httponly=True, secure=True, samesite="lax")
    response.set_cookie(
        "csrf_token", secrets.token_urlsafe(24), secure=True, samesite="lax"
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(request: Request, response: Response):
    _check_csrf(request)
    response.delete_cookie("session")
    return {"status": "ok"}


@router.get("/api/modules")
def list_modules(request: Request):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        result = ListAssignedModules(
            services.assignment_repository(session),
            services.game_round_repository(session),
        ).execute(actor)
        return [item.__dict__ for item in result]


@router.post("/api/modules/{module_id}/rounds")
def start_round(request: Request, module_id: str):
    actor = _require_actor(request)
    _check_csrf(request)
    with _session(request) as session:
        services = _services(request)
        assignments = services.assignment_repository(session)
        rounds = services.game_round_repository(session)
        scenarios = services.scenario_repository(session)
        assignment = next(
            (
                item
                for item in assignments.for_department(actor.department_id)
                if item.module_id == module_id
            ),
            None,
        )
        was_open = (
            assignment is not None
            and rounds.open_for(actor.id, assignment.id) is not None
        )
        try:
            result = StartOrResumeGameRound(assignments, scenarios, rounds).execute(
                actor, module_id
            )
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        except ValueError as error:
            raise HTTPExceptionResponse(409, str(error)) from error
        return JSONResponse(result.__dict__, status_code=200 if was_open else 201)


@router.post("/api/rounds/{round_id}/answers")
async def submit_answer(request: Request, round_id: str):
    actor = _require_actor(request)
    _check_csrf(request)
    payload = await request.json()
    with _session(request) as session:
        services = _services(request)
        assignments = services.assignment_repository(session)
        rounds = services.game_round_repository(session)
        try:
            feedback = SubmitRoundAnswer(assignments, rounds, SystemClock()).execute(
                actor, round_id, payload["position"], payload["option_id"]
            )
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        except ValueError as error:
            status = 409 if "bereits" in str(error) else 422
            raise HTTPExceptionResponse(status, str(error)) from error
        response = feedback.__dict__.copy()
        saved_round = rounds.get(round_id)
        if saved_round is not None and saved_round.completed_at is not None:
            response.update(score=saved_round.score, passed=saved_round.passed)
        return JSONResponse(response, status_code=201)


@router.get("/api/modules/{module_id}/progress")
def progress(request: Request, module_id: str):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        try:
            result = GetTrainingProgress(
                services.assignment_repository(session),
                services.game_round_repository(session),
                SystemClock(),
            ).execute(actor, module_id)
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        return result.__dict__


def create_app(services: Services) -> FastAPI:
    application = FastAPI()
    application.state.services = services
    application.include_router(router)

    @application.exception_handler(HTTPExceptionResponse)
    async def handle_http_error(request: Request, exc: HTTPExceptionResponse):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return application
