# Prompt für den Modellvergleich (beide Modelle identisch)

Du bist Senior-Reviewer für eine Python/FastAPI-Anwendung mit Clean Architecture.
Die Anwendung ist ein Datenschutz-Schulungsspiel für eine Gemeindeverwaltung.
Rollen: Mitarbeitende, Abteilungsleitung, Datenschutzverantwortliche (DSV).
Anmeldung über ein signiertes Session-Cookie (itsdangerous), dazu ein CSRF-Token im Cookie.
DSV weisen Abteilungen Module mit einem Fristdatum zu. Es gibt einen `ClockPort`
(Interface für die aktuelle Zeit), Zeitzone Europe/Zurich.

Aufgabe:
1. Prüfe den Code unten auf **Sicherheits- und Logikfehler**. Es sind Ausschnitte aus
   mehreren Dateien; Imports und andere Routen sind weggelassen und kein Fehler.
2. Liste jeden Befund mit: Datei/Funktion, Schweregrad (hoch/mittel/niedrig), konkretes
   Szenario, wie der Fehler auftritt, und warum es ein Problem ist.
3. Schlage für die zwei wichtigsten Befunde einen **konkreten Fix** als Code vor, passend
   zur Clean Architecture (Domain/Application/Infrastructure/Interfaces).
4. Nenne zu jedem Fix einen **Test** (pytest), der vorher rot und nachher grün ist.
   Du kannst die Tests nicht ausführen; behaupte nicht, sie ausgeführt zu haben.
5. Erfinde keine Befunde. Wenn du dir unsicher bist, schreibe "unsicher".

Antworte auf Deutsch, strukturiert mit Überschriften.

```python
# --- src/app/interfaces/http.py ---
router = APIRouter()
error_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
SESSION_MAX_AGE = 8 * 60 * 60
START_PAGES = {
    Role.EMPLOYEE: "/mitarbeitende/module",
    Role.DEPARTMENT_LEAD: "/abteilungsleitung/auswertung",
    Role.DATA_PROTECTION_OFFICER: "/datenschutz/auswertung",
}

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
    cookie = request.cookies.get("csrf_token")
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or not secrets.compare_digest(cookie, header):
        raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")


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

# --- src/app/application/use_cases.py ---
class AssignModule:
    def __init__(
        self,
        assignments: AssignmentRepository,
        modules: ModuleRepository,
        departments: DepartmentRepository,
    ):
        self.assignments = assignments
        self.modules = modules
        self.departments = departments

    def execute(
        self, actor: Actor, module_id: str, department_id: str, due_date
    ) -> Assignment:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied("Nur Datenschutzverantwortliche dürfen zuweisen")
        if self.modules.get(module_id) is None:
            raise NotFound("Modul nicht gefunden")
        if self.departments.get(department_id) is None:
            raise NotFound("Abteilung nicht gefunden")
        try:
            assignment = Assignment(
                id=str(uuid4()),
                module_id=module_id,
                department_id=department_id,
                due_date=due_date,
            )
        except (TypeError, ValueError) as error:
            raise InvalidRequest(str(error)) from error
        return self.assignments.save(assignment)

# --- src/app/domain/models.py ---
@dataclass(frozen=True)
class Assignment:
    id: str
    module_id: str
    department_id: str
    due_date: date

    def __post_init__(self):
        if not self.id or not self.module_id or not self.department_id:
            raise ValueError("Zuweisung benötigt ID, Modul und Abteilung")
        if type(self.due_date) is not date:
            raise ValueError("Zuweisung benötigt ein gültiges Fristdatum")

# --- src/app/interfaces/http.py (Fortsetzung) ---
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
```
