import secrets
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

from fastapi import APIRouter, FastAPI, Form, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.application.models import Actor, Role
from app.application.ports import ClockPort
from app.application.use_cases import (
    AccessDenied,
    AssignModule,
    CreateTeamAggregation,
    ExportTrainingEvidence,
    GetDepartmentStatus,
    GetOverallEvaluation,
    GetPersonalStatus,
    GetTrainingProgress,
    InvalidRequest,
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
    employee_repository: Callable[[Any], Any]
    department_repository: Callable[[Any], Any]
    module_repository: Callable[[Any], Any]
    csv_adapter: Any
    clock: ClockPort
    authenticate: Callable[[Any, str, str], Actor | None]
    session_secret: str


class HTTPExceptionResponse(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


router = APIRouter()
SESSION_MAX_AGE = 8 * 60 * 60


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


def _set_session_cookies(response: Response, actor: Actor, secret: str) -> None:
    session = URLSafeTimedSerializer(secret, salt="session").dumps(
        {"id": actor.id, "role": actor.role, "department_id": actor.department_id}
    )
    response.set_cookie(
        "session",
        session,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.set_cookie(
        "csrf_token", secrets.token_urlsafe(24), secure=True, samesite="lax"
    )


def _delete_session_cookies(response: Response) -> None:
    response.delete_cookie("session", secure=True, httponly=True, samesite="lax")
    response.delete_cookie("csrf_token", secure=True, samesite="lax")


def _actor(request: Request) -> Actor | None:
    value = request.cookies.get("session")
    if value is None:
        return None
    try:
        data = URLSafeTimedSerializer(
            _services(request).session_secret, salt="session"
        ).loads(value, max_age=SESSION_MAX_AGE)
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
    if "text/html" in response.headers.get("accept", ""):
        return {"csrf_token": _csrf(response)}
    return {"csrf_token": _csrf(response)}


@router.post("/login")
def login(
    request: Request,
    response: Response,
    email: str = Form(),
    password: str = Form(),
    csrf_token: str | None = Form(default=None),
):
    if csrf_token is None or csrf_token != request.cookies.get("csrf_token"):
        raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")
    with _session(request) as session:
        actor = _services(request).authenticate(session, email, password)
    if actor is None:
        raise HTTPExceptionResponse(401, "Ungültige Anmeldung")
    if "text/html" in request.headers.get("accept", ""):
        redirect = RedirectResponse(
            {
                Role.EMPLOYEE: "/mitarbeitende/module",
                Role.DEPARTMENT_LEAD: "/abteilungsleitung/auswertung",
                Role.DATA_PROTECTION_OFFICER: "/datenschutz/auswertung",
            }[actor.role],
            status_code=303,
        )
        _set_session_cookies(redirect, actor, _services(request).session_secret)
        return redirect
    _set_session_cookies(response, actor, _services(request).session_secret)
    return {"status": "ok"}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    csrf_token: str | None = Form(default=None),
):
    if csrf_token is not None:
        if csrf_token != request.cookies.get("csrf_token"):
            raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")
    else:
        _check_csrf(request)
    if "text/html" in request.headers.get("accept", ""):
        redirect = RedirectResponse("/", status_code=303)
        _delete_session_cookies(redirect)
        return redirect
    _delete_session_cookies(response)
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
    try:
        payload = await request.json()
        position = payload["position"]
        option_id = payload["option_id"]
    except (JSONDecodeError, KeyError, TypeError) as error:
        raise HTTPExceptionResponse(422, "Ungültige Antwort") from error
    with _session(request) as session:
        services = _services(request)
        assignments = services.assignment_repository(session)
        rounds = services.game_round_repository(session)
        try:
                feedback = SubmitRoundAnswer(
                    assignments, rounds, services.clock
                ).execute(actor, round_id, position, option_id)
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
                services.clock,
            ).execute(actor, module_id)
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        return result.__dict__


@router.post("/api/assignments")
async def assign_module(request: Request):
    actor = _require_actor(request)
    _check_csrf(request)
    try:
        payload = await request.json()
        from datetime import date

        due_date = date.fromisoformat(payload["due_date"])
        module_id = payload["module_id"]
        department_id = payload["department_id"]
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPExceptionResponse(422, "Ungültige Zuweisung") from error
    with _session(request) as session:
        services = _services(request)
        try:
            result = AssignModule(
                services.assignment_repository(session),
                services.module_repository(session),
                services.department_repository(session),
            ).execute(actor, module_id, department_id, due_date)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        except InvalidRequest as error:
            raise HTTPExceptionResponse(422, str(error)) from error
        return JSONResponse(jsonable_encoder(result.__dict__), status_code=201)


@router.get("/api/me/training-status")
def personal_status(request: Request, employee_id: str | None = None):
    actor = _require_actor(request)
    if employee_id is not None and employee_id != actor.id:
        raise HTTPExceptionResponse(403, "Fremde Mitarbeiterdaten")
    with _session(request) as session:
        services = _services(request)
        try:
            result = GetPersonalStatus(
                services.assignment_repository(session),
                services.game_round_repository(session),
                services.clock,
            ).execute(actor)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        return [item.__dict__ for item in result]


@router.get("/api/departments/{department_id}/training-status")
def department_status(request: Request, department_id: str):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        if services.department_repository(session).get(department_id) is None:
            raise HTTPExceptionResponse(404, "Abteilung nicht gefunden")
        try:
            result = GetDepartmentStatus(
                services.assignment_repository(session),
                services.employee_repository(session),
                services.game_round_repository(session),
                services.clock,
            ).execute(actor, department_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        return {
            "department_id": result.department_id,
            "persons": [item.__dict__ for item in result.persons],
        }


@router.get("/api/departments/{department_id}/training-aggregation")
def training_aggregation(request: Request, department_id: str):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        if services.department_repository(session).get(department_id) is None:
            raise HTTPExceptionResponse(404, "Abteilung nicht gefunden")
        try:
            result = CreateTeamAggregation(
                services.assignment_repository(session),
                services.game_round_repository(session),
                services.clock,
            ).execute(actor, department_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        return [item.__dict__ for item in result]


@router.get("/api/training/evaluation")
def overall_evaluation(request: Request):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        try:
            result = GetOverallEvaluation(
                services.assignment_repository(session),
                services.employee_repository(session),
                services.department_repository(session),
                services.game_round_repository(session),
                services.clock,
            ).execute(actor)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        return {"departments": [item.__dict__ for item in result.departments]}


@router.get("/api/assignments/{assignment_id}/training-evidence.csv")
def training_evidence(request: Request, assignment_id: str):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        try:
            records = ExportTrainingEvidence(
                services.assignment_repository(session),
                services.game_round_repository(session),
            ).execute(actor, assignment_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        return Response(
            content=services.csv_adapter.render(records),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f"attachment; filename=schulungsnachweis-{assignment_id}.csv"
                )
            },
        )


def create_app(services: Services) -> FastAPI:
    application = FastAPI()
    application.state.services = services
    application.include_router(router)

    @application.exception_handler(HTTPExceptionResponse)
    async def handle_http_error(request: Request, exc: HTTPExceptionResponse):
        if "text/html" in request.headers.get("accept", ""):
            template = "error.html"
            message = {
                403: "Zugriff verweigert",
                404: "Modul nicht gefunden",
            }.get(exc.status_code, exc.detail)
            return HTMLResponse(
                content=Jinja2Templates(directory="src/app/interfaces/templates").get_template(template).render(
                    request=request,
                    actor=_actor(request),
                    csrf_token=request.cookies.get("csrf_token"),
                    status_code=exc.status_code,
                    message=message,
                ),
                status_code=exc.status_code,
            )
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return application
