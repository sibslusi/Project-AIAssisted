# Antwort Modell A: gpt-5.6-luna (High)

GitHub Copilot Chat, Modus Ask, 26.10.2026 11:42, 1 min 44 s, 0.0178 USD.
Unveränderte Antwort, mit dem Kopier-Symbol aus Copilot kopiert (Prompt: [prompt.md](prompt.md), plus Zeile „Führe den Code-Review aus dem angehängten Text aus. Antworte direkt, ohne /fix oder /tests.“).

---

# Kurzfazit

Die CSRF-Prüfung der Assignment-Route ist grundsätzlich vorhanden. Ein signiertes Cookie ist zudem nicht ohne Kenntnis des Secrets manipulierbar.

Der wichtigste Befund ist jedoch, dass Autorisierungsdaten (`role`, `department_id`) dauerhaft aus dem Cookie vertraut werden. Eine Rollenänderung oder Deaktivierung wirkt dadurch bis zu acht Stunden nicht.

---

# Befunde

## 1. Autorisierung vertraut auf veraltete Rollen- und Abteilungsdaten

**Datei/Funktion:** `http.py`, `_actor()`  
**Schweregrad:** **hoch**

### Szenario

1. Eine Person ist zunächst Datenschutzverantwortliche und erhält ein gültiges Session-Cookie.
2. Die Rolle wird später auf `EMPLOYEE` geändert oder die Person wird deaktiviert.
3. Das alte, korrekt signierte Cookie bleibt bis zu `SESSION_MAX_AGE` gültig.
4. `_actor()` konstruiert weiterhin einen `Actor` mit der alten Rolle.
5. `AssignModule.execute()` sieht weiterhin `Role.DATA_PROTECTION_OFFICER` und erlaubt die Zuweisung.

Dass das Cookie signiert ist, schützt nur die Integrität der beim Ausstellen gespeicherten Daten. Es schützt nicht vor veralteten Berechtigungen oder einer fehlenden serverseitigen Sperrung.

### Problem

Die Geschäftsregel „nur aktuell berechtigte DSV dürfen zuweisen“ wird umgangen. Dasselbe gilt für eine veraltete Abteilungszugehörigkeit bei anderen Routen.

---

## 2. Signierte, aber veraltete oder fehlerhafte Session-Daten können einen 500-Fehler auslösen

**Datei/Funktion:** `http.py`, `_actor()`  
**Schweregrad:** **mittel**

### Szenario

Ein gültig signiertes Cookie stammt beispielsweise aus einer älteren Anwendungsversion und enthält kein `department_id`. Oder ein gespeicherter Rollenwert ist nicht mehr in `Role` vorhanden.

Dann können folgende Ausdrücke Ausnahmen auslösen:

```python
data["id"]                 # KeyError
Role(data["role"])         # ValueError
Actor(...)                 # TypeError oder ValueError
```

Gefangen wird nur `BadSignature`.

### Problem

Die Anfrage endet mit einem internen Serverfehler statt kontrolliert mit `401 Nicht angemeldet`. Das ist kein direkter Authentifizierungs-Bypass, weil ein Angreifer keine gültige Signatur erzeugen kann. Es ist aber ein Robustheits- und Verfügbarkeitsproblem bei alten, beschädigten oder inkonsistenten Sessions.

---

## 3. `module_id` und `department_id` werden vor dem Repository-Zugriff nicht typgeprüft

**Datei/Funktion:** `http.py`, `assign_module()`; `use_cases.py`, `AssignModule.execute()`  
**Schweregrad:** **mittel**

### Szenario

Ein authentifizierter Client sendet beispielsweise:

```json
{
  "module_id": [],
  "department_id": "department-1",
  "due_date": "2030-01-01"
}
```

`module_id` wird ungeprüft an `self.modules.get(module_id)` übergeben. Bei einem typischen Dictionary- oder SQLAlchemy-Repository kann ein nicht hashbarer Wert zu einem ungefangenen `TypeError` führen.

Die äußere `try`-Anweisung in der Route umfasst nur das Parsen des JSON-Payloads, nicht den späteren Repository-Aufruf.

### Problem

Ein fehlerhafter Client erhält einen 500-Fehler statt 422. Zusätzlich erzwingt die Domainklasse die Typen der IDs nicht: Die Annotation `str` ist zur Laufzeit keine Validierung.

Das ist kein belegter SQL-Injection-Befund; dafür ist aus dem Ausschnitt kein unsicherer SQL-Aufbau ersichtlich.

---

## 4. CSRF-Vergleich beim Logout verwendet keinen zeitkonstanten Vergleich

**Datei/Funktion:** `http.py`, `logout()`  
**Schweregrad:** **niedrig**

### Szenario

Beim Header-basierten Pfad wird korrekt `secrets.compare_digest()` verwendet:

```python
_check_csrf(request)
```

Beim Formularpfad wird dagegen normal verglichen:

```python
if csrf_token != request.cookies.get("csrf_token"):
```

### Problem

Ein normaler Stringvergleich kann theoretisch timingabhängige Informationen preisgeben. Wegen der Länge und Zufälligkeit des Tokens sowie Netzwerkrauschen ist ein praktischer Angriff hier sehr schwierig. Es ist dennoch eine unnötige Inkonsistenz.

Das ist kein offensichtlicher CSRF-Bypass.

---

## 5. Fristdatum in der Vergangenheit wird akzeptiert

**Datei/Funktion:** `AssignModule.execute()`, `Assignment.__post_init__()`  
**Schweregrad:** **unsicher, potenziell mittel**

### Szenario

Ein DSV kann ein beliebiges gültiges ISO-Datum, auch ein Datum in der Vergangenheit, zuweisen:

```json
{
  "module_id": "module-1",
  "department_id": "department-1",
  "due_date": "2020-01-01"
}
```

### Problem

Falls die Fachregel lautet, dass Fristen nicht in der Vergangenheit liegen dürfen, wird diese Regel nicht geprüft. Der vorhandene `ClockPort` wird für die Zuweisung nicht verwendet.

Dieser Befund ist ausdrücklich **unsicher**, weil aus dem Ausschnitt nicht hervorgeht, ob rückwirkende Fristen fachlich erlaubt sind. Falls die Prüfung erforderlich ist, muss die aktuelle Zeit über den `ClockPort` und die Zeitzone `Europe/Zurich` bestimmt werden, nicht über `datetime.now()`.

---

# Fix 1: Session nur als signierte Identität verwenden

Die Session sollte nur eine stabile Identität enthalten. Rolle, Abteilung und Aktivierungsstatus müssen bei jeder Anfrage aus der aktuellen Quelle geladen werden.

## Application-Port

```python
from typing import Protocol

from app.domain.models import Actor


class ActorRepository(Protocol):
    def get_active(self, actor_id: str) -> Actor | None:
        """Liefert nur den aktuell aktiven Actor mit aktuellen Berechtigungen."""
```

Die Infrastructure-Implementierung muss hierbei den aktuellen Datensatz laden und für unbekannte oder deaktivierte Personen `None` zurückgeben.

## Session-Ausstellung und Lesen

```python
def _set_session_cookies(response: Response, actor: Actor, secret: str) -> None:
    session = URLSafeTimedSerializer(secret, salt="session").dumps(
        {"id": actor.id}
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
        "csrf_token",
        secrets.token_urlsafe(24),
        secure=True,
        samesite="lax",
    )


def _actor(request: Request) -> Actor | None:
    value = request.cookies.get("session")
    if value is None:
        return None

    try:
        data = URLSafeTimedSerializer(
            _services(request).session_secret,
            salt="session",
        ).loads(value, max_age=SESSION_MAX_AGE)

        if not isinstance(data, dict):
            return None

        actor_id = data.get("id")
        if not isinstance(actor_id, str) or not actor_id:
            return None

    except (BadSignature, TypeError, ValueError):
        return None

    with _session(request) as session:
        repository = _services(request).actor_repository(session)
        return repository.get_active(actor_id)
```

Damit werden auch Cookies aus früheren Versionen mit zusätzlichen Feldern nicht mehr für die Autorisierung verwendet. Entscheidend ist ausschließlich der aktuelle Actor aus dem Repository.

## Test

Der Test ist vor dem Fix rot, weil `_actor()` den DSV-Rollenwert direkt aus dem Cookie übernimmt. Nach dem Fix ist er grün.

```python
from contextlib import contextmanager
from types import SimpleNamespace

from itsdangerous import URLSafeTimedSerializer

from app.domain.models import Actor, Role
from app.interfaces import http


def test_actor_uses_current_role_instead_of_cookie_role(monkeypatch):
    secret = "test-secret"
    current_actor = Actor(
        id="actor-1",
        role=Role.EMPLOYEE,
        department_id="department-2",
    )

    class ActorRepository:
        def get_active(self, actor_id: str):
            assert actor_id == "actor-1"
            return current_actor

    services = SimpleNamespace(
        session_secret=secret,
        actor_repository=lambda session: ActorRepository(),
    )

    @contextmanager
    def fake_session(request):
        yield object()

    monkeypatch.setattr(http, "_services", lambda request: services)
    monkeypatch.setattr(http, "_session", fake_session)

    stale_cookie = URLSafeTimedSerializer(
        secret,
        salt="session",
    ).dumps(
        {
            "id": "actor-1",
            "role": Role.DATA_PROTECTION_OFFICER.value,
            "department_id": "department-1",
        }
    )

    request = SimpleNamespace(
        cookies={"session": stale_cookie},
    )

    actor = http._actor(request)

    assert actor == current_actor
    assert actor.role is Role.EMPLOYEE
```

---

# Fix 2: IDs an der Application-Grenze und in der Domain validieren

Die Validierung muss vor dem Repository-Zugriff erfolgen. Die Domain sollte zusätzlich keine ungültigen ID-Typen akzeptieren.

## Application

```python
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
        self,
        actor: Actor,
        module_id: str,
        department_id: str,
        due_date,
    ) -> Assignment:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied("Nur Datenschutzverantwortliche dürfen zuweisen")

        if not isinstance(module_id, str) or not module_id:
            raise InvalidRequest("Ungültige Modul-ID")

        if not isinstance(department_id, str) or not department_id:
            raise InvalidRequest("Ungültige Abteilungs-ID")

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
```

## Domain

```python
@dataclass(frozen=True)
class Assignment:
    id: str
    module_id: str
    department_id: str
    due_date: date

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("Zuweisung benötigt eine gültige ID")

        if not isinstance(self.module_id, str) or not self.module_id:
            raise ValueError("Zuweisung benötigt eine gültige Modul-ID")

        if not isinstance(self.department_id, str) or not self.department_id:
            raise ValueError("Zuweisung benötigt eine gültige Abteilungs-ID")

        if type(self.due_date) is not date:
            raise ValueError("Zuweisung benötigt ein gültiges Fristdatum")
```

Die Route fängt `InvalidRequest` bereits ab und kann deshalb weiterhin mit HTTP 422 antworten.

## Test

Der Test ist vor dem Fix rot, weil der ungültige Listenwert ungeprüft an das Modul-Repository weitergegeben wird. Nach dem Fix ist er grün.

```python
from datetime import date
from unittest.mock import Mock

import pytest

from app.application.use_cases import AssignModule
from app.domain.models import Actor, Role
from app.application.errors import InvalidRequest


def test_rejects_non_string_module_id_before_repository_lookup():
    assignments = Mock()
    modules = Mock()
    departments = Mock()

    use_case = AssignModule(
        assignments=assignments,
        modules=modules,
        departments=departments,
    )

    actor = Actor(
        id="dsv-1",
        role=Role.DATA_PROTECTION_OFFICER,
        department_id=None,
    )

    with pytest.raises(InvalidRequest, match="Modul-ID"):
        use_case.execute(
            actor=actor,
            module_id=[],
            department_id="department-1",
            due_date=date(2030, 1, 1),
        )

    modules.get.assert_not_called()
```

---

# Weitere kleine Korrektur

Der Formularpfad des Logouts sollte denselben zeitkonstanten Vergleich verwenden:

```python
@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    csrf_token: str | None = Form(default=None),
):
    if csrf_token is not None:
        cookie_token = request.cookies.get("csrf_token")
        if (
            not cookie_token
            or not secrets.compare_digest(csrf_token, cookie_token)
        ):
            raise HTTPExceptionResponse(403, "Ungültiger CSRF-Token")
    else:
        _check_csrf(request)

    if "text/html" in request.headers.get("accept", ""):
        redirect = RedirectResponse("/", status_code=303)
        _delete_session_cookies(redirect)
        return redirect

    _delete_session_cookies(response)
    return {"status": "ok"}
```

Die vorgeschlagenen Tests wurden nicht ausgeführt.
