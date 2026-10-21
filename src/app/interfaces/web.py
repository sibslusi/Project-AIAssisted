import secrets
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.application.models import Role
from app.application.use_cases import (
    AccessDenied,
    AssignModule,
    CreateTeamAggregation,
    GetDepartmentStatus,
    GetDisplayNames,
    GetOverallEvaluation,
    GetPersonalStatus,
    InvalidRequest,
    ListAssignedModules,
    ListAssignments,
    NotFound,
    StartOrResumeGameRound,
    SubmitRoundAnswer,
)
from app.interfaces.http import (
    HTTPExceptionResponse,
    _actor,
    _csrf,
    _require_actor,
    _services,
    _session,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _context(request: Request, **values: Any) -> dict[str, Any]:
    response = values.pop("response", None)
    csrf_token = request.cookies.get("csrf_token")
    if response is not None:
        csrf_token = _csrf(response)
    return {
        "request": request,
        "actor": _actor(request),
        "csrf_token": csrf_token,
        **values,
    }


def _display_names(request: Request):
    actor = _actor(request)
    if actor is None:
        return None
    with _session(request) as session:
        services = _services(request)
        return GetDisplayNames(
            services.employee_repository(session),
            services.module_repository(session),
            services.department_repository(session),
        ).execute(actor)


def _render(request: Request, template: str, **values: Any) -> HTMLResponse:
    csrf_token = request.cookies.get("csrf_token") or secrets.token_urlsafe(24)
    values.setdefault("names", _display_names(request))
    response = templates.TemplateResponse(
        request=request,
        name=template,
        context=_context(request, csrf_token=csrf_token, **values),
    )
    if request.cookies.get("csrf_token") is None:
        response.set_cookie(
            "csrf_token", csrf_token, httponly=False, secure=True, samesite="lax"
        )
    return response


def _check_form_csrf(request: Request, csrf_token: str | None) -> None:
    if csrf_token is None or csrf_token != request.cookies.get("csrf_token"):
        raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")


def _round_context(game_round, feedback=None) -> dict[str, Any]:
    position = game_round.first_open_position
    return {
        "title": "Runde spielen",
        "game_round": game_round,
        "position": position,
        "scenario": None if position is None else game_round.scenarios[position - 1],
        "total": len(game_round.scenarios),
        "feedback": feedback,
    }


def _redirect_for(role: Role) -> str:
    return {
        Role.EMPLOYEE: "/mitarbeitende/module",
        Role.DEPARTMENT_LEAD: "/abteilungsleitung/auswertung",
        Role.DATA_PROTECTION_OFFICER: "/datenschutz/auswertung",
    }[role]


def _assigned_modules(request: Request, actor):
    with _session(request) as session:
        services = _services(request)
        assignments = services.assignment_repository(session)
        rounds = services.game_round_repository(session)
        try:
            statuses = GetPersonalStatus(assignments, rounds, services.clock).execute(
                actor
            )
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        modules = ListAssignedModules(assignments, rounds).execute(actor)
    by_assignment = {status.assignment_id: status for status in statuses}
    return tuple(
        (module, by_assignment.get(module.assignment_id)) for module in modules
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    actor = _actor(request)
    if actor is not None:
        return RedirectResponse(_redirect_for(actor.role), status_code=303)
    return _render(request, "login.html")


@router.get("/mitarbeitende/module", response_class=HTMLResponse)
def employee_modules(request: Request):
    actor = _require_actor(request)
    return _render(
        request,
        "modules.html",
        title="Meine Module",
        modules=_assigned_modules(request, actor),
    )


@router.get("/mitarbeitende/module/{module_id}", response_class=HTMLResponse)
def round_page(request: Request, module_id: str):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        rounds = services.game_round_repository(session)
        try:
            view = StartOrResumeGameRound(
                services.assignment_repository(session),
                services.scenario_repository(session),
                rounds,
            ).execute(actor, module_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        except ValueError as error:
            raise HTTPExceptionResponse(409, str(error)) from error
        context = _round_context(rounds.get(view.id))
    return _render(request, "round.html", **context)


@router.post("/mitarbeitende/runden/{round_id}/antworten", response_class=HTMLResponse)
def submit_round_answer(
    request: Request,
    round_id: str,
    position: int = Form(),
    option_id: str = Form(),
    csrf_token: str | None = Form(default=None),
):
    actor = _require_actor(request)
    _check_form_csrf(request, csrf_token)
    with _session(request) as session:
        services = _services(request)
        rounds = services.game_round_repository(session)
        try:
            feedback = SubmitRoundAnswer(
                services.assignment_repository(session), rounds, services.clock
            ).execute(actor, round_id, position, option_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        except ValueError as error:
            status = 409 if "bereits" in str(error) else 422
            raise HTTPExceptionResponse(status, str(error)) from error
        context = _round_context(rounds.get(round_id), feedback)
    return _render(request, "round.html", **context)


@router.get("/abteilungsleitung/auswertung", response_class=HTMLResponse)
def department_evaluation(request: Request):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        try:
            status = GetDepartmentStatus(
                services.assignment_repository(session),
                services.employee_repository(session),
                services.game_round_repository(session),
                services.clock,
            ).execute(actor, actor.department_id)
            aggregation = CreateTeamAggregation(
                services.assignment_repository(session),
                services.game_round_repository(session),
                services.clock,
            ).execute(actor, actor.department_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
    return _render(
        request,
        "department.html",
        title="Abteilungsstatus",
        persons=status.persons,
        aggregations=aggregation,
    )


@router.get("/datenschutz/auswertung", response_class=HTMLResponse)
def data_protection_evaluation(request: Request):
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
    return _render(
        request,
        "evaluation.html",
        title="Gesamtauswertung",
        departments=result.departments,
    )


@router.get("/datenschutz/zuweisungen", response_class=HTMLResponse)
def assignments_page(request: Request):
    actor = _require_actor(request)
    with _session(request) as session:
        services = _services(request)
        try:
            overview = ListAssignments(
                services.assignment_repository(session),
                services.module_repository(session),
                services.department_repository(session),
            ).execute(actor)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
    return _render(
        request,
        "assignments.html",
        title="Zuweisungen",
        assignments=overview.assignments,
        departments=overview.departments,
        modules=overview.modules,
    )


@router.post("/datenschutz/zuweisungen", response_class=HTMLResponse)
def create_assignment(
    request: Request,
    module_id: str = Form(),
    department_id: str = Form(),
    due_date: str = Form(),
    csrf_token: str | None = Form(default=None),
):
    _require_actor(request)
    _check_form_csrf(request, csrf_token)
    try:
        parsed_date = date.fromisoformat(due_date)
    except ValueError as error:
        raise HTTPExceptionResponse(422, "Ungültige Zuweisung") from error
    with _session(request) as session:
        services = _services(request)
        try:
            AssignModule(
                services.assignment_repository(session),
                services.module_repository(session),
                services.department_repository(session),
            ).execute(_require_actor(request), module_id, department_id, parsed_date)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        except (InvalidRequest, ValueError) as error:
            raise HTTPExceptionResponse(422, str(error)) from error
    return RedirectResponse("/datenschutz/zuweisungen", status_code=303)
