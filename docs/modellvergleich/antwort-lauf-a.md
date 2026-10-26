# Antwort Lauf A: gpt-5.6-luna (Extra High)

GitHub Copilot Chat (Local), Modus Ask, 26.10.2026. Prompt: [prompt.md](prompt.md) plus Zusatzzeile.
Unveränderte Antwort, mit dem Kopier-Symbol aus Copilot kopiert.

---

## Zusammenfassung

Im gezeigten Ausschnitt sehe ich keinen offensichtlichen direkten CSRF-Bypass oder eine Möglichkeit, die signierte Session ohne Kenntnis des Secrets zu fälschen. Die Cookie-Attribute `Secure`, `HttpOnly` und `SameSite=Lax` sind grundsätzlich sinnvoll.

Die wichtigsten Befunde sind:

1. **Berechtigungen stammen ausschließlich aus potenziell veralteten Session-Claims.**
2. **Fristdaten werden nicht gegen das aktuelle Datum in Europe/Zurich geprüft.**

---

## Befunde

### F-01: Veraltete Berechtigungen aus dem Session-Cookie

- **Datei/Funktion:** `src/app/interfaces/http.py:_actor`
- **Schweregrad:** mittel; bei sofortiger Rollenentziehung potenziell hoch
- **Status:** unsicher, falls Rollen und Abteilungszugehörigkeiten absichtlich bis zum Session-Ablauf gelten sollen

#### Szenario

Eine Person meldet sich als DSV an. Das Session-Cookie enthält:

```python
{"id": "...", "role": "DATA_PROTECTION_OFFICER", "department_id": "..."}
```

Danach wird die Rolle entzogen oder die Person in eine andere Abteilung versetzt. Das Cookie bleibt bis zu acht Stunden gültig.

`_actor()` liest weiterhin Rolle und Abteilung aus dem signierten Cookie:

```python
return Actor(data["id"], Role(data["role"]), data["department_id"])
```

`AssignModule.execute()` sieht weiterhin die Rolle `DATA_PROTECTION_OFFICER` und erlaubt die Zuweisung.

#### Problem

Eine Signatur schützt die Integrität des Cookies, aber nicht die Aktualität der enthaltenen Berechtigungen. Ein DSV kann nach einer Rollenänderung weiterhin privilegierte Aktionen ausführen.

Wenn diese achtstündige Berechtigungs-Caching-Strategie ausdrücklich gewollt ist, muss sie dokumentiert werden. Für sofortige Rollenänderungen oder Kontosperrungen reicht sie nicht aus.

---

### F-02: Ungültige, aber signierte Session-Daten können einen 500-Fehler verursachen

- **Datei/Funktion:** `src/app/interfaces/http.py:_actor`
- **Schweregrad:** niedrig bis mittel
- **Status:** Die Ausnutzung durch einen externen Angreifer setzt ein gültiges Signing-Secret voraus; relevant sind insbesondere alte oder fehlerhafte Tokens

#### Szenario

Ein unter einem alten Schema ausgestelltes Cookie enthält beispielsweise kein `role`-Feld oder einen unbekannten Rollenwert:

```python
{"id": "a-1", "role": "UNKNOWN"}
```

Dann können folgende Fehler außerhalb des `try`-Blocks entstehen:

- `KeyError` bei fehlenden Feldern
- `ValueError` bei `Role(data["role"])`
- `TypeError` bei einer unerwarteten Payload-Struktur

Abgefangen wird nur `BadSignature`.

#### Problem

Ein ungültiges Session-Cookie sollte zu einer anonymen Anfrage beziehungsweise zu `401` führen, nicht zu einem internen Serverfehler. Das kann nach Schemaänderungen zu unnötigen 500-Fehlern führen.

---

### F-03: Fristdatum kann bereits in der Vergangenheit liegen

- **Datei/Funktion:** `src/app/application/use_cases.py:AssignModule.execute`, `src/app/domain/models.py:Assignment.__post_init__`
- **Schweregrad:** mittel
- **Status:** unsicher, weil im Ausschnitt nicht ausdrücklich definiert ist, ob historische Fristdaten erlaubt sind

#### Szenario

Eine DSV sendet:

```json
{
  "module_id": "mod-1",
  "department_id": "dept-1",
  "due_date": "2020-01-01"
}
```

Das Datum ist syntaktisch gültig und wird akzeptiert. `ClockPort` wird nicht verwendet. `Assignment` prüft nur den Python-Typ `date`, nicht die Beziehung zum aktuellen Datum.

#### Problem

Eine neue Zuweisung kann unmittelbar als überfällig angelegt werden. Falls die Fachregel lautet „Fristdatum muss heute oder später sein“, fehlt diese Regel vollständig.

Die lokale Zeitzone muss dabei für den Tageswechsel `Europe/Zurich` berücksichtigen.

---

### F-04: ID-Typen und leere Werte werden nicht ausreichend validiert

- **Datei/Funktion:** `src/app/interfaces/http.py:assign_module`, `src/app/domain/models.py:Assignment.__post_init__`
- **Schweregrad:** mittel

#### Szenario

Die JSON-Payload kann Werte enthalten wie:

```json
{
  "module_id": 123,
  "department_id": true,
  "due_date": "2026-11-01"
}
```

Die API validiert nur, dass die Schlüssel vorhanden sind. Die Domain-Prüfung prüft bei diesen Feldern nur die Wahrheithaftigkeit:

```python
if not self.id or not self.module_id or not self.department_id:
```

Damit wären beispielsweise `123`, `True` oder `"   "` teilweise zulässig.

#### Problem

Die Typannotation `str` erzwingt zur Laufzeit keine String-Werte. Je nach Repository kann das zu folgenden Ergebnissen führen:

- falsche Repository-Abfragen,
- unerwartete 500-Fehler,
- Persistierung eines fachlich ungültigen `Assignment`-Objekts.

Die Prüfung sollte sowohl am HTTP-Eingang als auch als Domain-Invariante erfolgen.

---

### F-05: CSRF-Vergleich beim Logout ist nicht konstantzeitlich

- **Datei/Funktion:** `src/app/interfaces/http.py:logout`
- **Schweregrad:** niedrig

#### Szenario

Bei einem Form-Token wird verglichen mit:

```python
if csrf_token != request.cookies.get("csrf_token"):
```

Bei Header-Tokens wird dagegen korrekt `secrets.compare_digest()` verwendet.

#### Problem

Der direkte Stringvergleich kann theoretisch Timing-Informationen offenlegen. Bei einem zufälligen 24-Byte-Token und normalen Netzwerkbedingungen ist dies kein realistischer unmittelbarer CSRF-Bypass, aber die beiden Prüfpfade sollten einheitlich implementiert werden.

---

## Fix 1: Session nur mit Actor-ID und aktuellen Berechtigungen auflösen

Die Session sollte keine autorisierungsrelevanten Claims wie Rolle oder Abteilung als Quelle der aktuellen Berechtigung verwenden. Der signierte Cookie kann weiterhin die Actor-ID enthalten. Rolle, Abteilung und aktiver Status kommen aus dem aktuellen Repository.

### Application-Port und Use Case

```python
from typing import Protocol

from app.domain.models import Actor


class SessionCodec(Protocol):
    def encode_actor_id(self, actor_id: str) -> str:
        ...

    def decode_actor_id(self, raw_value: str) -> str | None:
        ...


class CurrentActorRepository(Protocol):
    def get_current(self, actor_id: str) -> Actor | None:
        """
        Liefert die aktuell gültige Rolle und Abteilungszugehörigkeit.
        Deaktivierte oder gelöschte Accounts liefern None.
        """
        ...
```

```python
# ...existing code...

class ResolveSessionActor:
    def __init__(
        self,
        session_codec: SessionCodec,
        actors: CurrentActorRepository,
    ):
        self.session_codec = session_codec
        self.actors = actors

    def execute(self, raw_session: str | None) -> Actor | None:
        if raw_session is None:
            return None

        actor_id = self.session_codec.decode_actor_id(raw_session)
        if actor_id is None:
            return None

        return self.actors.get_current(actor_id)

# ...existing code...
```

### Infrastructure-Adapter für `itsdangerous`

```python
from itsdangerous import BadData, URLSafeTimedSerializer


class ItsDangerousSessionCodec:
    def __init__(self, secret: str, max_age: int):
        self.serializer = URLSafeTimedSerializer(secret, salt="session")
        self.max_age = max_age

    def encode_actor_id(self, actor_id: str) -> str:
        if type(actor_id) is not str or not actor_id.strip():
            raise ValueError("Ungültige Actor-ID")

        return self.serializer.dumps({"id": actor_id})

    def decode_actor_id(self, raw_value: str) -> str | None:
        try:
            data = self.serializer.loads(raw_value, max_age=self.max_age)
        except BadData:
            return None

        if not isinstance(data, dict):
            return None

        actor_id = data.get("id")
        if type(actor_id) is not str or not actor_id.strip():
            return None

        return actor_id
```

`BadData` umfasst auch Signatur- und Zeitfehler. Damit werden beschädigte oder nicht mehr gültige Cookies einheitlich als anonyme Session behandelt.

### HTTP-Adapter

```python
# ...existing code...

def _set_session_cookies(
    response: Response,
    actor: Actor,
    session_codec: SessionCodec,
) -> None:
    session = session_codec.encode_actor_id(actor.id)

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
    raw_session = request.cookies.get("session")
    if raw_session is None:
        return None

    with _session(request) as session:
        services = _services(request)
        return ResolveSessionActor(
            services.session_codec,
            services.current_actor_repository(session),
        ).execute(raw_session)

# ...existing code...
```

Der Login-Aufrufer muss entsprechend `services.session_codec` statt des Secrets an `_set_session_cookies()` übergeben.

### Test für Fix 1

Der Test ist vor dem Fix rot, weil die bisherige Implementierung Rolle und Abteilung aus dem Cookie verwendet. Nach dem Fix muss die aktuelle Rolle aus dem Repository stammen.

```python
from itsdangerous import URLSafeTimedSerializer

from app.application.use_cases import ResolveSessionActor
from app.domain.models import Actor, Role
from app.infrastructure.session import ItsDangerousSessionCodec


class FakeCurrentActorRepository:
    def __init__(self, actor: Actor):
        self.actor = actor

    def get_current(self, actor_id: str) -> Actor | None:
        return self.actor if actor_id == self.actor.id else None


def test_uses_current_role_instead_of_role_from_old_cookie():
    secret = "test-secret"
    codec = ItsDangerousSessionCodec(secret, max_age=8 * 60 * 60)

    old_cookie = URLSafeTimedSerializer(
        secret,
        salt="session",
    ).dumps(
        {
            "id": "actor-1",
            "role": "DATA_PROTECTION_OFFICER",
            "department_id": "old-department",
        }
    )

    current_actor = Actor(
        "actor-1",
        Role.EMPLOYEE,
        "current-department",
    )

    resolved = ResolveSessionActor(
        codec,
        FakeCurrentActorRepository(current_actor),
    ).execute(old_cookie)

    assert resolved == current_actor
    assert resolved.role is Role.EMPLOYEE
    assert resolved.department_id == "current-department"
```

---

## Fix 2: Fristdatum mit `ClockPort` und Europe/Zurich prüfen

Der aktuelle Tag sollte außerhalb der Domain über `ClockPort` bezogen und als Wert an eine reine Domain-Prüfung übergeben werden.

### Domain-Regel

```python
from datetime import date

# ...existing code...

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

    @staticmethod
    def validate_due_date(due_date: date, current_date: date) -> None:
        if type(due_date) is not date:
            raise ValueError("Zuweisung benötigt ein gültiges Fristdatum")
        if type(current_date) is not date:
            raise ValueError("Ungültiges aktuelles Datum")
        if due_date < current_date:
            raise ValueError(
                "Fristdatum darf nicht vor dem aktuellen Datum liegen"
            )

# ...existing code...
```

### Application-Use-Case

```python
from zoneinfo import ZoneInfo

# ...existing code...

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
        due_date,
    ) -> Assignment:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied("Nur Datenschutzverantwortliche dürfen zuweisen")

        if self.modules.get(module_id) is None:
            raise NotFound("Modul nicht gefunden")

        if self.departments.get(department_id) is None:
            raise NotFound("Abteilung nicht gefunden")

        try:
            current_date = (
                self.clock
                .now()
                .astimezone(ZoneInfo("Europe/Zurich"))
                .date()
            )
            Assignment.validate_due_date(due_date, current_date)

            assignment = Assignment(
                id=str(uuid4()),
                module_id=module_id,
                department_id=department_id,
                due_date=due_date,
            )
        except (TypeError, ValueError) as error:
            raise InvalidRequest(str(error)) from error

        return self.assignments.save(assignment)

# ...existing code...
```

Der `ClockPort` muss ein timezone-aware `datetime` liefern. Eine mögliche Infrastructure-Implementierung ist:

```python
from datetime import datetime
from zoneinfo import ZoneInfo


class ZurichClock:
    def now(self) -> datetime:
        return datetime.now(ZoneInfo("Europe/Zurich"))
```

### Test für Fix 2

Dieser Test ist vor dem Fix rot, weil `AssignModule` aktuell keinen `ClockPort` entgegennimmt und ein vergangenes Datum akzeptiert. Nach dem Fix muss `InvalidRequest` ausgelöst und nichts gespeichert werden.

```python
from datetime import datetime, date
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest

from app.application.use_cases import AssignModule
from app.domain.models import Actor, Role
from app.application.errors import InvalidRequest


class FixedClock:
    def now(self) -> datetime:
        return datetime(
            2026,
            10,
            26,
            12,
            0,
            tzinfo=ZoneInfo("Europe/Zurich"),
        )


def test_rejects_due_date_before_current_zurich_date():
    assignments = Mock()
    modules = Mock()
    departments = Mock()

    modules.get.return_value = object()
    departments.get.return_value = object()

    use_case = AssignModule(
        assignments=assignments,
        modules=modules,
        departments=departments,
        clock=FixedClock(),
    )

    actor = Actor(
        "dsv-1",
        Role.DATA_PROTECTION_OFFICER,
        "dsv",
    )

    with pytest.raises(InvalidRequest, match="Fristdatum"):
        use_case.execute(
            actor=actor,
            module_id="module-1",
            department_id="department-1",
            due_date=date(2026, 10, 25),
        )

    assignments.save.assert_not_called()
```

---

## Empfohlene zusätzliche Tests

Für die übrigen Befunde wären zusätzlich sinnvoll:

- ungültige Session-Payload führt zu `401`, nicht zu `500`;
- `module_id` und `department_id` mit Nicht-String-Werten führen zu `422`;
- leere oder nur aus Leerzeichen bestehende IDs werden abgelehnt;
- Form-CSRF-Token wird ebenfalls mit `secrets.compare_digest()` verglichen.

Die Tests wurden nicht ausgeführt.
