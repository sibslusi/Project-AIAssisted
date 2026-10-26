# Antwort Lauf B: ibm/granite4.1:3b (Open-Weight)

GitHub Copilot Chat (Local), Modus Ask, 26.10.2026 ca. 12:16–12:21. Prompt: [prompt.md](prompt.md) plus Zusatzzeile.
Unveränderte Antwort bis zum Abbruch. Danach meldete Copilot:
„Sorry, your request failed. … LiteLLM request timed out after 300000ms.“

---

**1. Befunde**

| Datei / Funktion | Schweregrad | Szenario, wie der Fehler auftritt | Warum es ein Problem ist |
|------------------|-------------|-----------------------------------|--------------------------|
| `http.py` – `_actor(Request)` | Mittel | Wenn ein Mitarbeiter versucht, ohne Authentifizierung auf eine API-Endpunkt zuzugreifen (z.B. `/api/assignments`), wird der Fehler “Nicht angemeldet” geroutet, aber die Session‑Cookie‑Abfrage fehlschlägt, weil der Cookie nicht vorliegt. Dies kann dazu führen, dass Authentifizierungsfehler bei nicht‑Admin‑Benutzern nicht korrekt erkannt werden. |
| `http.py` – `_check_csrf(Request)` | Niedrig | Der CSRF‑Token wird nur vom Logout‑Endpoint prüft. Alle anderen Endpoints (z.B. `/api/assignments`) überlassen die CSRF‑Prüfung auf die `X-CSRF-Token`‑Header. Dies kann zu CSRF‑Angriffen führen, wenn ein böswilliger Benutzer die Header manipuliert. |
| `models.py` – `Assignment` | Hoch | Der `__post_init__` überprüft, dass `due_date` vom Typ `date` ist, aber der Code `from datetime import date` importiert den lokalen `date`‑Typ, der nicht vom Typ `datetime.date` ist. Dies führt zu einer `TypeError` bei der Konstruktion von `Assignment`, wenn `due_date` vom Typ `datetime.date` ist. |
| `use_cases.py` – `AssignModule.execute()` | Hoch | Die Methode prüft nur, ob der Aufrufer die Rolle `Role.DATA_PROTECTION_OFFICER` hat. Es wird keine zusätzliche Überprüfung durchgeführt, ob der aktuelle Benutzer das Modul tatsächlich verwalten darf (z.B. nach Abteilung oder Projekt). Dies kann dazu führen, dass DPOs Module zuweisen können, die nicht dem Zuständigkeitsbereich ihrer Abteilung entsprechen. |
| `http.py` – `/api/assignments` | Mittel | Die `payload["due_date"]` wird mit `date.fromisoformat()` parsiert, was nur ISO‑8601‑Strings akzeptiert, die keine Zeitinformationen enthalten. Ein Payload wie `2026-10-26T14:30` wird zu einem `TypeError` und somit zu einer 422‑Fehlermeldung, obwohl die Datenstruktur korrekt ist. |

**2. Wohlabsichteter konkreter Fix für die beiden wichtigsten Befunde**

---

### Fix 1 – `_actor(Request)` (Mittel)

Die Session wird falsch abgefragt. Der Cookie wird erst beim Setzen des Wertes gespeichert, daher kann die Abfrage auch ohne Cookie erfolgreich sein.

**Vorgeschlagener Fix (Domain → Application)**  

```python
# --- src/app/domain/user.py (neu) ---
from fastapi import Request
from typing import Optional

class User:
    def __init__(self, id: str, role: Role, department_id: str):
        self.id = id
        self.role = role
        self.department_id = department_id

# --- src/app/application/use_cases.py ---
def _require_actor(request: Request) -> User:
    value = request.cookies.get("session")
    if value is None:
        raise HTTPExceptionResponse(401, "Nicht angemeldet")
    try:
        data = URLSafeTimedSerializer(
            _services(request).session_secret,
            salt="session"
        ).loads(value, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None
    return User(data["id"], Role(data["role"]), data["department_id"])
```

**Test (pytest)**  

```python
# --- tests/test_assignments.py ---
from fastapi.testclient import TestClient
from app import models, use_cases

client = TestClient(app)

def test_assign_with_data_protection_officer():
    # Simulate a logged‑in DPO user
    response = client.post("/api/assignments", json={
        "module_id": "M001",
        "department_id": "D12",
        "due_date": "2026-11-01"
    })
    assert response.status_code == 201
    assert "assignment_id" in response.json

def test_assign_without_session_fails():
    # Send a request without the session cookie
    response = client.post("/api/assignments", json={})
    assert response.status_code == 401
    assert "Nicht angemeldet" in response.json
```

---

### Fix 2 – `Assignment.__post_init__` (Hoch)

Der Fehler tritt auf, wenn `due_date` vom Typ `datetime.date` ist, aber der Import `from datetime import date` importiert den lokalen `date`‑Typ, der nicht vom Typ `date` ist. Der Fix ist einfach: Importieren des richtigen `date` aus `datetime`.

**Vorgeschlagener Fix (Domain)**  

```python
# --- src/app/domain/models.py ---
from datetime import date as Date  # Import des richtigen Typs
```

**Test (pytest)**  

```python
# --- tests/test_assignment.py ---
# --- tests/test_assignment.py ---
```
