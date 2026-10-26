# Antwort Zusatzlauf: gpt-5.6-luna (Low)

GitHub Copilot Chat, Modus Ask, gleiche Standardwerkzeuge, 26.10.2026 ca. 12:00.
Gleicher Prompt ([prompt.md](prompt.md)) wie Lauf A, nur Denkstufe **Low** statt High.
Unveränderte Antwort:

---

# Befunde

## 1. Fristdatum wird nicht gegen das aktuelle Datum geprüft

**Datei/Funktion:**  
`use_cases.py`, `AssignModule.execute`  
`models.py`, `Assignment.__post_init__`

**Schweregrad:** Mittel

**Szenario:**  
Ein DSV weist ein Modul mit einem bereits vergangenen Fristdatum zu, zum Beispiel:

```json
{
  "module_id": "modul-1",
  "department_id": "abteilung-1",
  "due_date": "2024-01-01"
}
```

Das Datum ist syntaktisch gültig und vom Typ `date`. `Assignment` akzeptiert es deshalb, und die Zuweisung wird gespeichert.

**Warum problematisch:**  
Eine vergangene Frist ist für eine neue Schulungszuweisung fachlich wahrscheinlich ungültig. Außerdem wird der vorhandene `ClockPort` nicht verwendet. Dadurch ist die Fristregel weder zentral modelliert noch testbar gegen eine definierte Zeitzone beziehungsweise einen kontrollierten Zeitpunkt.

Ob eine Frist am aktuellen Tag noch erlaubt sein soll, ist aus dem Ausschnitt nicht eindeutig. Die Prüfung selbst ist jedoch mit hoher Wahrscheinlichkeit erforderlich. Die konkrete Grenze, also `due_date < today` oder `due_date <= today`, ist **unsicher** und muss aus der Fachspezifikation entschieden werden.

---

## 2. Serverseitige Session wird nach Änderungen am Benutzerkonto nicht ungültig

**Datei/Funktion:**  
`http.py`, `_set_session_cookies` und `_actor`

**Schweregrad:** Mittel bis hoch

**Szenario:**  

1. Ein Benutzer meldet sich als DSV an.
2. Danach wird seine Rolle in der Datenbank auf Mitarbeitender geändert, oder sein Benutzer wird deaktiviert.
3. Das signierte Cookie bleibt bis zu acht Stunden gültig.
4. `_actor()` liest `id`, `role` und `department_id` ausschließlich aus dem Cookie.
5. Die Route `/api/assignments` akzeptiert den Actor weiterhin als DSV und erlaubt eine Zuweisung.

**Warum problematisch:**  
Die Signatur schützt die Daten vor Manipulation, verhindert aber keine veralteten Berechtigungen. Ein gültiges Cookie ist hier zugleich Identitäts- und Autorisierungsquelle. Rollen- und Kontosperrungen wirken erst nach Ablauf des Cookies oder nach einem Schlüsselwechsel.

Das ist besonders relevant, weil die Anwendung rollenabhängige Datenschutzdaten verarbeitet. Für eine belastbare Berechtigungsprüfung sollte das Cookie höchstens eine Sitzungsreferenz oder Identität enthalten. Die aktuelle Rolle und der Kontostatus sollten serverseitig geprüft werden.

---

## 3. Fehlerhafte oder manipulierte signierte Payload kann einen 500-Fehler erzeugen

**Datei/Funktion:**  
`http.py`, `_actor`

**Schweregrad:** Mittel

**Szenario:**  
Ein Server oder ein älterer Anwendungsversionstand erzeugt ein signiertes Cookie ohne eines der erwarteten Felder:

```python
{"id": "...", "role": "..."}
```

Oder die Payload enthält eine ungültige Rolle:

```python
{"id": "...", "role": "UNKNOWN", "department_id": None}
```

`loads()` kann erfolgreich sein, aber anschließend schlagen diese Ausdrücke fehl:

```python
data["department_id"]       # KeyError
Role(data["role"])           # ValueError
```

Diese Ausnahmen werden nicht abgefangen.

**Warum problematisch:**  
Eine ungültige Session sollte wie eine nicht angemeldete Session behandelt werden und mit `401` enden. Stattdessen kann sie einen internen Serverfehler verursachen. Das kann zu unnötigen Fehlern, Lograuschen und möglicherweise Informationslecks führen.

Die Signaturprüfung schützt nur die Integrität einer Payload, die der Server mit seinem aktuellen Secret signiert hat. Sie garantiert nicht, dass die Payload strukturell noch gültig ist.

---

## 4. Die Formular-CSRF-Prüfung verwendet keinen Konstantzeitvergleich

**Datei/Funktion:**  
`http.py`, `logout`

**Schweregrad:** Niedrig

**Szenario:**  
Bei einem Formular-Logout wird der übermittelte Token mit dem Cookie-Token so verglichen:

```python
if csrf_token != request.cookies.get("csrf_token"):
```

Beim Header-Pfad wird dagegen korrekt `secrets.compare_digest()` verwendet.

**Warum problematisch:**  
Ein normaler Stringvergleich kann prinzipiell timingabhängig sein. Für kurze zufällige CSRF-Tokens ist ein praktischer Remote-Angriff vermutlich schwierig, aber es besteht eine unnötige Inkonsistenz in einer Sicherheitsprüfung.

Die Formularprüfung sollte ebenfalls `secrets.compare_digest()` verwenden. Das ist ein echter, aber kleiner Befund.

---

## 5. Die CSRF-Prüfung ist nicht ausdrücklich an die Session gebunden

**Datei/Funktion:**  
`http.py`, `_set_session_cookies` und `_check_csrf`

**Schweregrad:** Niedrig bis mittel, teilweise unsicher

**Szenario:**  
Der CSRF-Token wird als separates Cookie gesetzt und nur gegen den vom Client gesendeten Header verglichen. Er ist nicht in der signierten Session enthalten und wird nicht serverseitig gespeichert.

Ein Angreifer, der das `csrf_token`-Cookie setzen oder überschreiben kann, könnte denselben Wert anschließend auch im Header senden.

**Warum problematisch:**  
Das Double-Submit-Cookie-Muster kann sicher sein, wenn Cookie-Injection ausgeschlossen ist. Im Ausschnitt fehlen jedoch:

- ein `__Host-`-Cookie-Präfix,
- eine explizite Einschränkung auf `Path=/`,
- eine Aussage zur Domain- und Subdomain-Konfiguration.

Bei einer kompromittierten oder unsicher konfigurierten Subdomain können Cookie-Injection-Angriffe relevant werden. Das ist daher **unsicher**, aber die Cookie-Härtung wäre empfehlenswert.

Zusätzlich ist der CSRF-Token nicht automatisch an eine bestimmte Session gebunden. Ein serverseitig gespeicherter oder signiert mit der Session verknüpfter Token wäre robuster.

---

## 6. Die Rollen- und Department-Daten im Cookie können veraltet sein

**Datei/Funktion:**  
`http.py`, `_set_session_cookies` und `_actor`

**Schweregrad:** Mittel

**Szenario:**  
Ein Benutzer wechselt die Abteilung. Das Cookie enthält weiterhin:

```python
{
    "id": actor.id,
    "role": actor.role,
    "department_id": actor.department_id
}
```

Nach dem Wechsel verwendet die Anwendung weiter die alte Abteilungszuordnung aus der Session.

**Warum problematisch:**  
Bei Routen, die Abteilungszugriff anhand des `Actor` prüfen, kann der Benutzer entweder noch auf alte Daten zugreifen oder den Zugriff auf die neue Abteilung verlieren. Die konkrete Auswirkung auf die hier gezeigte Zuweisungsroute ist begrenzt, weil für DSV nur die Rolle geprüft wird. Für die übrigen rollenabhängigen Auswertungsrouten ist die Wirkung abhängig vom nicht gezeigten Code.

Dieser Befund überschneidet sich mit Befund 2, ist aber die konkrete Datenintegritätsfolge für `department_id`.

---

## 7. Keine Prüfung auf fachliche Duplikate oder bestehende Zuweisungen

**Datei/Funktion:**  
`use_cases.py`, `AssignModule.execute`

**Schweregrad:** Niedrig bis mittel, unsicher

**Szenario:**  
Der DSV weist dasselbe Modul derselben Abteilung mehrfach zu. Im Use Case wird nur geprüft, ob Modul und Abteilung existieren. Eine Suche nach einer bereits vorhandenen Zuweisung findet nicht statt.

**Warum problematisch:**  
Es können doppelte Schulungsaufgaben entstehen. Das könnte zu mehreren Fristen, doppelten Anzeigen und unklaren Auswertungen führen.

Ob Mehrfachzuweisungen fachlich erlaubt sind, ist aus dem Ausschnitt nicht ersichtlich. Daher ist dieser Befund ausdrücklich **unsicher**. Falls sie nicht erlaubt sind, sollte die Regel im Application Layer und zusätzlich durch eine Datenbank-Unique-Constraint abgesichert werden.

---

# Die zwei wichtigsten Fixes

## Fix 1: Rolle und Kontostatus serverseitig erneut prüfen

Die Session sollte nicht die vollständige Autorisierung dauerhaft selbst tragen. Eine minimale Verbesserung ist, im signierten Cookie nur die Benutzer-ID zu speichern und den aktuellen Actor aus einem Repository zu laden.

### Application-Port

```python
# src/app/application/ports.py
from typing import Protocol

class ActorRepository(Protocol):
    def get_active(self, actor_id: str) -> Actor | None:
        ...
```

### Application-Service

```python
# src/app/application/authentication.py
class CurrentActor:
    def __init__(self, actors: ActorRepository):
        self.actors = actors

    def load(self, actor_id: str) -> Actor | None:
        return self.actors.get_active(actor_id)
```

### Session-Cookie erstellen

```python
# src/app/interfaces/http.py
def _set_session_cookies(response: Response, actor: Actor, secret: str) -> None:
    session = URLSafeTimedSerializer(secret, salt="session").dumps(
        {"id": actor.id}
    )

    response.set_cookie(
        "__Host-session",
        session,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

    response.set_cookie(
        "__Host-csrf_token",
        secrets.token_urlsafe(32),
        secure=True,
        samesite="lax",
        path="/",
    )
```

Das `__Host-`-Präfix verlangt unter anderem `Secure`, `Path=/` und verhindert ein gesetztes `Domain`-Attribut.

### Actor laden und Payload validieren

```python
# src/app/interfaces/http.py
def _actor(request: Request) -> Actor | None:
    value = request.cookies.get("__Host-session")
    if value is None:
        return None

    try:
        data = URLSafeTimedSerializer(
            _services(request).session_secret,
            salt="session",
        ).loads(value, max_age=SESSION_MAX_AGE)

        actor_id = data["id"]
        if not isinstance(actor_id, str) or not actor_id:
            return None
    except (BadSignature, BadData, KeyError, TypeError, ValueError):
        return None

    services = _services(request)
    return services.current_actor().load(actor_id)
```

Die genaue Exception-Hierarchie von `itsdangerous` sollte an die tatsächlich verwendete Bibliotheksversion angepasst werden. Falls `BadData` bereits Basisklasse von `BadSignature` ist, genügt gegebenenfalls nur `BadData`.

Die Route erhält anschließend einen aktuellen Actor:

```python
def _require_actor(request: Request) -> Actor:
    actor = _actor(request)
    if actor is None:
        raise HTTPExceptionResponse(401, "Nicht angemeldet")
    return actor
```

### Zugehöriger pytest-Test

Dieser Test wäre vor dem Fix rot, weil der Actor trotz zwischenzeitlicher Deaktivierung aus dem Cookie akzeptiert wird:

```python
def test_deactivated_actor_cannot_assign_module(client, services):
    actor = services.create_actor(
        role=Role.DATA_PROTECTION_OFFICER,
        active=True,
    )
    session = services.login_as(actor)

    services.deactivate_actor(actor.id)

    response = client.post(
        "/api/assignments",
        cookies={
            "__Host-session": session,
            "__Host-csrf_token": "csrf-value",
        },
        headers={"X-CSRF-Token": "csrf-value"},
        json={
            "module_id": "module-1",
            "department_id": "department-1",
            "due_date": "2026-12-31",
        },
    )

    assert response.status_code == 401
```

Der Test setzt voraus, dass die vorhandenen Test-Fixtures eine Anmeldung und einen Statuswechsel ermöglichen.

### Zusätzlicher Test für ungültige Payload

```python
def test_malformed_signed_session_is_treated_as_unauthenticated(client, services):
    malformed = URLSafeTimedSerializer(
        services.session_secret,
        salt="session",
    ).dumps({"id": "actor-without-valid-structure"})

    response = client.post(
        "/api/assignments",
        cookies={"__Host-session": malformed},
        headers={"X-CSRF-Token": "csrf-value"},
        json={
            "module_id": "module-1",
            "department_id": "department-1",
            "due_date": "2026-12-31",
        },
    )

    assert response.status_code == 401
```

---

## Fix 2: Fristregel mit `ClockPort` im Application Layer prüfen

Die zeitabhängige Regel gehört in den Domain- oder Application-Layer, nicht in die HTTP-Route. Der Application Layer verwendet den `ClockPort`; die Domain erhält nur das bereits bestimmte heutige Datum.

Angenommen, die Fachregel lautet: Eine neue Zuweisung muss eine Frist **heute oder später** haben.

### Clock-Port

```python
# src/app/application/ports.py
from datetime import date
from typing import Protocol

class ClockPort(Protocol):
    def today(self) -> date:
        ...
```

### Application Use Case

```python
# src/app/application/use_cases.py
class AssignModule:
    def __init__(
        self,
        assignments: AssignmentRepository,
        modules: ModuleRepository,
        departments: DepartmentRepository,
        clock: ClockPort,
    ):
        self.assignments = assignments
        self.modules = modules
        self.departments = departments
        self.clock = clock

    def execute(
        self,
        actor: Actor,
        module_id: str,
        department_id: str,
        due_date: date,
    ) -> Assignment:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied("Nur Datenschutzverantwortliche dürfen zuweisen")

        if self.modules.get(module_id) is None:
            raise NotFound("Modul nicht gefunden")

        if self.departments.get(department_id) is None:
            raise NotFound("Abteilung nicht gefunden")

        if due_date < self.clock.today():
            raise InvalidRequest(
                "Das Fristdatum darf nicht in der Vergangenheit liegen"
            )

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

Die Infrastructure-Implementierung bestimmt das Datum in `Europe/Zurich`. Der Application Layer kennt dabei weder FastAPI noch SQLAlchemy noch die konkrete Zeitzonenimplementierung.

Beispielhaft:

```python
# src/app/infrastructure/clock.py
from datetime import date, datetime
from zoneinfo import ZoneInfo

class ZurichClock:
    def today(self) -> date:
        return datetime.now(ZoneInfo("Europe/Zurich")).date()
```

Die Route reicht den konfigurierten Clock-Service lediglich an den Use Case weiter:

```python
result = AssignModule(
    services.assignment_repository(session),
    services.module_repository(session),
    services.department_repository(session),
    services.clock(),
).execute(actor, module_id, department_id, due_date)
```

### Zugehöriger pytest-Test

Dieser Test wäre vor dem Fix rot, weil ein vergangenes Datum derzeit akzeptiert wird:

```python
def test_assign_module_rejects_due_date_in_the_past(
    assignment_repository,
    module_repository,
    department_repository,
):
    class FixedClock:
        def today(self) -> date:
            return date(2026, 10, 26)

    use_case = AssignModule(
        assignments=assignment_repository,
        modules=module_repository,
        departments=department_repository,
        clock=FixedClock(),
    )

    actor = Actor(
        id="dsv-1",
        role=Role.DATA_PROTECTION_OFFICER,
        department_id=None,
    )

    with pytest.raises(InvalidRequest, match="Vergangenheit"):
        use_case.execute(
            actor=actor,
            module_id="module-1",
            department_id="department-1",
            due_date=date(2026, 10, 25),
        )
```

Falls die Fachregel stattdessen lautet, dass Fristen erst ab morgen zulässig sind, muss die Bedingung entsprechend lauten:

```python
if due_date <= self.clock.today():
    ...
```

Diese fachliche Entscheidung sollte vor der Implementierung in der Use-Case-Spezifikation oder einem ADR festgehalten werden.

# Zusammenfassung

Die wichtigsten Risiken sind:

1. **Veraltete Rollen und Kontostatus werden aus einer bis zu acht Stunden gültigen Session akzeptiert.**
2. **Das Fristdatum wird trotz vorhandenem `ClockPort` nicht fachlich gegen das aktuelle Datum geprüft.**

Zusätzlich sollte `_actor()` ungültige Payload-Strukturen als unauthentifizierte Session behandeln und der Formular-CSRF-Vergleich `secrets.compare_digest()` verwenden. Tests wurden nicht ausgeführt.
