import secrets
from contextlib import contextmanager
from datetime import UTC
from importlib import import_module
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import JSONResponse
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.application.models import Actor, Role
from app.application.use_cases import (
    AccessDenied,
    GetTrainingProgress,
    ListAssignedModules,
    NotFound,
    StartOrResumeGameRound,
    SubmitRoundAnswer,
)


def _infrastructure():
    db = import_module("app.infrastructure.db")
    models = import_module("app.infrastructure.models")
    repositories = import_module("app.infrastructure.repositories")
    seed = import_module("app.infrastructure.seed")
    return db.Base, models, repositories, seed


Base, _models, _repositories, _seed = _infrastructure()
EmployeeModel = _models.EmployeeModel
SqlAlchemyAssignmentRepository = _repositories.SqlAlchemyAssignmentRepository
SqlAlchemyGameRoundRepository = _repositories.SqlAlchemyGameRoundRepository
SqlAlchemyScenarioRepository = _repositories.SqlAlchemyScenarioRepository
load_seed_data = _seed.load_seed_data

DATABASE_URL = "sqlite://"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
with Session(engine) as seed_session:
    load_seed_data(seed_session, Path(__file__).parents[3] / "data" / "seed")
    seed_session.commit()

app = FastAPI()
serializer = URLSafeSerializer("development-only-session-secret", salt="session")
password_hasher = PasswordHasher()


@contextmanager
def request_session():
    session = Session(engine)
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
        data = serializer.loads(value)
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


class HTTPExceptionResponse(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


@app.exception_handler(HTTPExceptionResponse)
async def handle_http_error(request: Request, exc: HTTPExceptionResponse):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/login")
def login_form(response: Response):
    return {"csrf_token": _csrf(response)}


@app.post("/login")
def login(
    request: Request,
    response: Response,
    email: str = Form(),
    password: str = Form(),
    csrf_token: str = Form(),
):
    if csrf_token != request.cookies.get("csrf_token"):
        raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")
    with Session(engine) as session:
        employee = session.scalar(
            select(EmployeeModel).where(EmployeeModel.email == email)
        )
    if employee is None:
        raise HTTPExceptionResponse(401, "Ungültige Anmeldung")
    try:
        password_hasher.verify(employee.password_hash, password)
    except VerifyMismatchError:
        raise HTTPExceptionResponse(401, "Ungültige Anmeldung") from None
    session_value = serializer.dumps(
        {
            "id": employee.id,
            "role": employee.role,
            "department_id": employee.department_id,
        }
    )
    response.set_cookie(
        "session", session_value, httponly=True, secure=True, samesite="lax"
    )
    response.set_cookie(
        "csrf_token", secrets.token_urlsafe(24), secure=True, samesite="lax"
    )
    return {"status": "ok"}


@app.post("/logout")
def logout(request: Request, response: Response):
    _check_csrf(request)
    response.delete_cookie("session")
    return {"status": "ok"}


def _use_cases(session: Session):
    assignments = SqlAlchemyAssignmentRepository(session)
    rounds = SqlAlchemyGameRoundRepository(session)
    scenarios = SqlAlchemyScenarioRepository(session)
    return assignments, rounds, scenarios


@app.get("/api/modules")
def list_modules(request: Request):
    actor = _require_actor(request)
    with request_session() as session:
        assignments, rounds, _ = _use_cases(session)
        result = ListAssignedModules(assignments, rounds).execute(actor)
        return [item.__dict__ for item in result]


@app.post("/api/modules/{module_id}/rounds")
def start_round(request: Request, module_id: str):
    actor = _require_actor(request)
    _check_csrf(request)
    with request_session() as session:
        assignments, rounds, scenarios = _use_cases(session)
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


@app.post("/api/rounds/{round_id}/answers")
async def submit_answer(request: Request, round_id: str):
    actor = _require_actor(request)
    _check_csrf(request)
    payload = await request.json()
    with request_session() as session:
        assignments, rounds, _ = _use_cases(session)
        try:
            feedback = SubmitRoundAnswer(assignments, rounds, _SystemClock()).execute(
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


@app.get("/api/modules/{module_id}/progress")
def progress(request: Request, module_id: str):
    actor = _require_actor(request)
    with request_session() as session:
        assignments, rounds, _ = _use_cases(session)
        try:
            result = GetTrainingProgress(assignments, rounds, _SystemClock()).execute(
                actor, module_id
            )
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        return result.__dict__


class _SystemClock:
    def now(self):
        from datetime import datetime

        return datetime.now(UTC)
