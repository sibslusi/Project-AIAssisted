import secrets
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.application.use_cases import (
    AccessDenied,
    AssignModule,
    CreateTeamAggregation,
    GetDepartmentStatus,
    GetDisplayNames,
    GetOpenGameRound,
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
    START_PAGES,
    HTTPExceptionResponse,
    _actor,
    _require_actor,
    _services,
    _session,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _context(request: Request, **values: Any) -> dict[str, Any]:
    return {"request": request, "actor": _actor(request), **values}


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
    path = request.url.path
    if path.startswith("/mitarbeitende"):
        active_nav = "modules"
    elif path.startswith("/abteilungsleitung"):
        active_nav = "department"
    elif path.startswith("/datenschutz/zuweisungen"):
        active_nav = "assignments"
    elif path.startswith("/datenschutz"):
        active_nav = "evaluation"
    else:
        active_nav = None
    response = templates.TemplateResponse(
        request=request,
        name=template,
        context=_context(
            request,
            csrf_token=csrf_token,
            active_nav=active_nav,
            role_label={
                "employee": "Mitarbeitende",
                "department_lead": "Abteilungsleitung",
                "data_protection_officer": "Datenschutzverantwortliche",
            }.get(_actor(request).role.value if _actor(request) else ""),
            **values,
        ),
    )
    if request.cookies.get("csrf_token") is None:
        response.set_cookie(
            "csrf_token", csrf_token, httponly=False, secure=True, samesite="lax"
        )
    return response


def _check_form_csrf(request: Request, csrf_token: str | None) -> None:
    cookie = request.cookies.get("csrf_token")
    if not cookie or not csrf_token or not secrets.compare_digest(cookie, csrf_token):
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
        modules = ListAssignedModules(assignments).execute(actor)
        lookup = GetOpenGameRound(assignments, rounds)
        open_modules = {
            module.module_id
            for module in modules
            if lookup.execute(actor, module.module_id) is not None
        }
    by_assignment = {status.assignment_id: status for status in statuses}
    return tuple(
        (
            module,
            by_assignment.get(module.assignment_id),
            module.module_id in open_modules,
        )
        for module in modules
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    actor = _actor(request)
    if actor is not None:
        return RedirectResponse(START_PAGES[actor.role], status_code=303)
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
            view = GetOpenGameRound(
                services.assignment_repository(session), rounds
            ).execute(actor, module_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        if view is None:
            return RedirectResponse("/mitarbeitende/module", status_code=303)
        context = _round_context(rounds.get(view.id))
    return _render(request, "round.html", **context)


@router.post("/mitarbeitende/module/{module_id}/runden", response_class=HTMLResponse)
def start_round(
    request: Request,
    module_id: str,
    csrf_token: str | None = Form(default=None),
):
    actor = _require_actor(request)
    _check_form_csrf(request, csrf_token)
    with _session(request) as session:
        services = _services(request)
        try:
            StartOrResumeGameRound(
                services.assignment_repository(session),
                services.scenario_repository(session),
                services.game_round_repository(session),
            ).execute(actor, module_id)
        except AccessDenied as error:
            raise HTTPExceptionResponse(403, str(error)) from error
        except NotFound as error:
            raise HTTPExceptionResponse(404, str(error)) from error
        except ValueError as error:
            raise HTTPExceptionResponse(409, str(error)) from error
    return RedirectResponse(f"/mitarbeitende/module/{module_id}", status_code=303)


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
            feedback = SubmitRoundAnswer(rounds, services.clock).execute(
                actor, round_id, position, option_id
            )
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
