# Antwort Lauf C: gpt-5.6-luna (Low)

GitHub Copilot Chat (Local), Modus Ask, 26.10.2026. Prompt: [prompt.md](prompt.md) plus Zusatzzeile.
Unveränderte Antwort, mit dem Kopier-Symbol aus Copilot kopiert.

---

## Befunde

### 1. Fristdatum kann in der Vergangenheit liegen

- **Datei/Funktion:** `http.py`, `assign_module`; `use_cases.py`, `AssignModule.execute`; `models.py`, `Assignment.__post_init__`
- **Schweregrad:** mittel
- **Szenario:** Eine DSV sendet beispielsweise `"due_date": "2020-01-01"`. Das Datum wird erfolgreich geparst und die Zuweisung gespeichert.
- **Warum problematisch:** Eine Zuweisung ist bei ihrer Erstellung bereits abgelaufen. Das kann zu falschen Statusanzeigen, sofortigen Mahnungen oder unbrauchbaren Schulungszuweisungen führen. Außerdem wird der vorhandene `ClockPort` nicht verwendet. Dadurch fehlt eine testbare und zeitzonenbewusste Geschäftsregel.
- **Sicherheit:** Kein direkter Authentifizierungsfehler, aber eine nicht durchgesetzte Geschäftsregel.

### 2. Ungültige, aber signierte Sitzungsdaten können zu einem 500-Fehler führen

- **Datei/Funktion:** `http.py`, `_actor`
- **Schweregrad:** niedrig bis mittel
- **Szenario:** `_actor` lädt ein Cookie erfolgreich, aber die Daten enthalten beispielsweise keinen Schlüssel `id`, eine ungültige Rolle oder einen ungültigen `department_id`-Wert. Dann entstehen `KeyError`, `ValueError` oder möglicherweise `TypeError`, die nicht abgefangen werden.
- **Warum problematisch:** Eine fehlerhafte Sitzung sollte als nicht authentifiziert behandelt werden und nicht zu einem internen Serverfehler führen. Das erschwert Monitoring und kann Fehlerseiten für geschützte Endpunkte auslösen.
- **Einschränkung:** Ein Angreifer kann solche Daten nicht ohne Kenntnis des Session-Secrets gültig signieren. Der Befund betrifft primär Robustheit und den Umgang mit beschädigten oder veralteten Sitzungen.

### 3. CSRF-Vergleich beim Logout ist nicht zeitkonstant

- **Datei/Funktion:** `http.py`, `logout`
- **Schweregrad:** niedrig
- **Szenario:** Bei einem Formular-Logout wird `csrf_token != request.cookies.get("csrf_token")` verwendet, während `_check_csrf` `secrets.compare_digest` nutzt.
- **Warum problematisch:** Der Vergleich kann theoretisch Timing-Informationen preisgeben. Bei einem kurzen, zufälligen CSRF-Token ist das praktische Risiko gering, aber die beiden Prüfpfade haben unterschiedliche Sicherheitssemantik.
- **Hinweis:** Das ist kein CSRF-Bypass; ein gültiger Token ist weiterhin erforderlich.

### 4. Sitzungsrolle und Abteilung werden ausschließlich aus dem Cookie übernommen

- **Datei/Funktion:** `http.py`, `_actor`
- **Schweregrad:** unsicher, abhängig vom Sicherheitsmodell
- **Szenario:** Ein Benutzer wird nach der Anmeldung administrativ herabgestuft oder einer anderen Abteilung zugeordnet. Die bestehende Sitzung enthält weiterhin die alte Rolle beziehungsweise Abteilung bis zum Ablauf nach acht Stunden.
- **Warum problematisch:** Berechtigungsänderungen werden nicht sofort wirksam. Falls Rollenänderungen während einer Sitzung möglich sein müssen, kann dadurch ein zu weitgehender Zugriff bestehen bleiben.
- **Einschränkung:** Die Cookie-Signatur verhindert eine Manipulation durch den Client. Wenn bewusst stateless Sessions mit bis zu acht Stunden Gültigkeit vorgesehen sind, ist dies möglicherweise akzeptiertes Verhalten.

### 5. Möglicher fehlender Schutz gegen doppelte Zuweisungen

- **Datei/Funktion:** `use_cases.py`, `AssignModule.execute`
- **Schweregrad:** unsicher
- **Szenario:** Dasselbe Modul wird derselben Abteilung mehrfach zugewiesen.
- **Warum problematisch:** Es könnten doppelte Schulungsaufgaben, widersprüchliche Fristen oder doppelte Auswertungen entstehen.
- **Einschränkung:** Im Ausschnitt ist keine fachliche Regel erkennbar, die doppelte Zuweisungen verbietet. Deshalb ist dies kein sicherer Befund ohne zusätzliche Spezifikation.

## Wichtigster Fix 1: Fristdatum über `ClockPort` validieren

Die Regel sollte im Domain-Modell oder in einer Domain-Policy liegen. Die Anwendung übergibt das Datum der aktuellen Zeit; die Domain verwendet keine Systemuhr.

Beispiel für einen `ClockPort`:

```python
from datetime import date
from typing import Protocol


class ClockPort(Protocol):
    def today(self) -> date:
        ...
```

Domain-Regel:

```python
from datetime import date
from dataclasses import dataclass


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

    @classmethod
    def create(
        cls,
        *,
        id: str,
        module_id: str,
        department_id: str,
        due_date: date,
        today: date,
    ) -> "Assignment":
        if due_date < today:
            raise ValueError("Fristdatum darf nicht in der Vergangenheit liegen")

        return cls(
            id=id,
            module_id=module_id,
            department_id=department_id,
            due_date=due_date,
        )
```

Anwendung:

```python
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
        self, actor: Actor, module_id: str, department_id: str, due_date
    ) -> Assignment:
        if actor.role is not Role.DATA_PROTECTION_OFFICER:
            raise AccessDenied("Nur Datenschutzverantwortliche dürfen zuweisen")
        if self.modules.get(module_id) is None:
            raise NotFound("Modul nicht gefunden")
        if self.departments.get(department_id) is None:
            raise NotFound("Abteilung nicht gefunden")

        try:
            assignment = Assignment.create(
                id=str(uuid4()),
                module_id=module_id,
                department_id=department_id,
                due_date=due_date,
                today=self.clock.today(),
            )
        except (TypeError, ValueError) as error:
            raise InvalidRequest(str(error)) from error

        return self.assignments.save(assignment)
```

Die Infrastruktur sollte einen `ClockPort` für `Europe/Zurich` bereitstellen. Der konkrete Code dafür hängt von den vorhandenen Projekt-Ports und der verwendeten Datums-/Zeitzonen-Konvention ab.

### Test für Fix 1

Dieser Test ist vor dem Fix rot, weil ein vergangenes Datum aktuell akzeptiert wird:

```python
from datetime import date
from types import SimpleNamespace

import pytest

from app.application.use_cases import AssignModule
from app.application.errors import InvalidRequest
from app.domain.models import Role


class FixedClock:
    def today(self) -> date:
        return date(2026, 10, 26)


def test_assign_module_rejects_past_due_date():
    assignments = SimpleNamespace(save=lambda assignment: assignment)
    modules = SimpleNamespace(get=lambda module_id: object())
    departments = SimpleNamespace(get=lambda department_id: object())

    use_case = AssignModule(
        assignments=assignments,
        modules=modules,
        departments=departments,
        clock=FixedClock(),
    )

    actor = SimpleNamespace(
        role=Role.DATA_PROTECTION_OFFICER,
        id="dsv-1",
        department_id=None,
    )

    with pytest.raises(InvalidRequest):
        use_case.execute(
            actor=actor,
            module_id="module-1",
            department_id="department-1",
            due_date=date(2026, 10, 25),
        )
```

## Wichtigster Fix 2: Sitzungsdaten defensiv validieren

`_actor` sollte alle Fehler abfangen, die beim Interpretieren der signierten Payload entstehen. Ein Cookie mit ungültigem Inhalt wird einheitlich als nicht authentifiziert behandelt.

```python
# ...existing code...


def _actor(request: Request) -> Actor | None:
    value = request.cookies.get("session")
    if value is None:
        return None

    try:
        data = URLSafeTimedSerializer(
            _services(request).session_secret,
            salt="session",
        ).loads(value, max_age=SESSION_MAX_AGE)

        actor_id = data["id"]
        role = Role(data["role"])
        department_id = data["department_id"]

        if not isinstance(actor_id, str) or not actor_id:
            return None
        if department_id is not None and not isinstance(department_id, str):
            return None

        return Actor(actor_id, role, department_id)
    except (BadSignature, KeyError, TypeError, ValueError):
        return None
```

Falls `Actor` weitere Invarianten besitzt, sollten diese ebenfalls innerhalb desselben Validierungspfads geprüft werden.

### Test für Fix 2

Der Test simuliert eine gültig geladene, aber strukturell ungültige Payload. Vor dem Fix entsteht ein `KeyError`; nach dem Fix liefert `_actor` `None`.

```python
from types import SimpleNamespace

import app.interfaces.http as http


def test_actor_treats_malformed_signed_payload_as_anonymous(monkeypatch):
    request = SimpleNamespace(
        cookies={"session": "signed-session"},
    )

    services = SimpleNamespace(session_secret="test-secret")
    monkeypatch.setattr(http, "_services", lambda request: services)

    class Serializer:
        def __init__(self, secret, salt):
            pass

        def loads(self, value, max_age):
            return {"role": "employee"}

    monkeypatch.setattr(http, "URLSafeTimedSerializer", Serializer)

    assert http._actor(request) is None
```

## Zusammenfassung

Die zwei belastbarsten Befunde sind:

1. **Vergangene Fristen werden akzeptiert** und der vorhandene `ClockPort` wird nicht verwendet.
2. **Strukturell ungültige Sitzungsdaten können ungefangen zu einem 500-Fehler führen.**

Der Rollen-/Abteilungsbefund ist vom gewünschten Session-Modell abhängig und sollte vor einer Änderung fachlich geklärt werden.
