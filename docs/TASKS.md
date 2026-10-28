# TASKS.md

PHASE: 5
STATUS: done

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

## Current Use Case

Phase 5 Deploy (UC-001/UC-002 live) und Korrekturen aus der Repo-Prüfung vom
25.10.2026

### Phase 5: Deploy

- **Umfang:** Neon-Datenbank, Render-Web-Service aus dem GHCR-Image
  (Auto-Deploy aus), GitHub-Environment `production` mit Secrets
  `RENDER_DEPLOY_HOOK_URL`, `DEMO_PASSWORD` und Variablen `CD_ENABLED`,
  `RENDER_SERVICE_URL`, `SMOKE_EMAIL` (ADR-006, jetzt Accepted).
- **Nachweis:** Tag `v0.1.1`, Release-Lauf 40194817567 am 25.10. grün: Tests,
  E2E im Image, Smoke im Container, Push nach GHCR, GitHub-Release, Deploy per
  Image-Digest und Smoke-Test gegen https://grenchen-datenschutz.onrender.com
  (`/health` mit Version `v0.1.1`, Demo-Login).
- **Korrektur-Release:** PR #22 am 26.10. gemergt, Tag `v0.1.2` von Sibslusi
  gesetzt. Release-Lauf 40316617386 grün: Tests, Image, GitHub-Release, Deploy
  per Image-Digest mit Migration `0002_session_version` auf Neon und
  Smoke-Test gegen die Live-URL.
- **Abschluss:** STATUS done am 26.10.2026 von Sibslusi bestätigt.
- **ADR-007:** Session-Widerruf (Variante C, `session_version`) am 26.10.2026
  von Sibslusi angenommen, Status Accepted.

### Korrekturen aus der Repo-Prüfung vom 25.10.

Keine Fast Track: B1 ändert Fachlogik, der Logout ist eine Sicherheits- und
Datenänderung (Migration). Darum Specs, ADR-007 und TDD-Commits.

- **B1:** Abteilungsleitungen und Datenschutzverantwortliche standen in den
  Statuslisten und wären nach Fristende „Frist überschritten“, obwohl sie
  keine Runden spielen dürfen. Jetzt nur Rolle Mitarbeitende (UC-002 Flow 7,
  AC-008, AC-012).
- **Logout:** Ein kopiertes Session-Cookie blieb nach dem Logout gültig. Jetzt
  Session-Version pro Person (ADR-007, Migration `0002`).
- **Frist:** Eine Frist vor dem heutigen Datum wurde angenommen. Jetzt 422
  (UC-002 AC-002, Regel `due_date_has_passed` mit `ClockPort`).
- **D1:** UC-001, UC-002 und PROJECT.md sagten „bester bestandener Versuch“
  für den Friststatus; Code und ADR-004 verwenden den ersten. Doku angeglichen.
- **D2:** `CurrentActorPort`, KI-Port und LiteLLM-Adapter standen in
  PROJECT.md, ADR-001 und ADR-002, gibt es im Code aber nicht. Doku
  angeglichen; `ENVIRONMENT` entfernt (wurde nie gelesen).
- **Regressionstests:** `tests/unit/application/test_uc002_use_cases.py`,
  `tests/integration/test_uc002_persistence.py`,
  `tests/integration/test_http.py`, `tests/integration/test_web.py`,
  `tests/integration/test_auth.py`, `tests/e2e/test_uc002_workflow.py`.
- **Checks:** 167 Tests grün, Coverage 97 %, Ruff, Format, import-linter,
  `alembic check` (SQLite im Test). PostgreSQL prüft der CI-Job `postgres`.
- **Bekannt, nicht geändert:** Die Gesamtauswertung der
  Datenschutzverantwortlichen zeigt nur Status pro Person (UC-002 Flow 6 am
  28.10. an den Code angeglichen); die Abteilungsseite zeigt Punkte, aber
  keine Fehler (AC-010, die API liefert beide).

### Phase 4: Validate

- **Umfang:** Smoke-Test-Skript, Version in `/health`, Seed im Image,
  `ci.yml`, `release.yml`, `cd.yml`, `scripts/deploy.sh`, ADR-006.
- **Ergebnis:** 154 Tests grün, Coverage 96 %, Ruff (Check und Format),
  Import-Linter, `pip-audit` ohne Befund. Docker-Image lokal gebaut, mit
  PostgreSQL 16 und `RUN_SEED=true` gestartet, Smoke-Test mit Version und
  Login grün, auch nach Neustart (Seed zweimal). `alembic check` auf
  PostgreSQL und SQLite ohne Änderungen. `release.yml` führt die 35
  E2E-Tests im gebauten Image gegen PostgreSQL aus (lokal nachgestellt:
  35 bestanden). `docker compose up` lädt die Seed-Daten (`RUN_SEED`), die
  Demo-Logins funktionieren lokal im Container.
- **Dabei gefunden und behoben:** Seed scheiterte auf PostgreSQL am
  Fremdschlüssel `module_scenarios.scenario_id` (SQLite prüfte ihn nicht);
  `alembic check` meldete auf PostgreSQL eine Scheinänderung beim
  Unique-Constraint, der dem Primärschlüssel entspricht.
- **Release-Nachweis:** Tag `v0.1.0` auf `main` (921788e), Release-Lauf
  grün am 22.10.: Tests mit Coverage, 35 E2E-Tests im gebauten Image gegen
  PostgreSQL, Smoke-Test gegen den Container (`/health` mit Version
  `v0.1.0`, Login `ma@mail.ch`), Image
  `ghcr.io/sibslusi/project-aiassisted:v0.1.0` in GHCR, GitHub-Release
  `v0.1.0`. Der Deploy-Job wurde wie vorgesehen übersprungen
  (`CD_ENABLED` noch nicht gesetzt). CI auf `main` grün, alle drei Jobs
  unter einer Minute.
- **Ausgelassen, mit Grund:**
  - Playwright-Browsertests: nicht umgesetzt. Die Oberfläche ist über
    TestClient-Tests (`tests/integration/test_web.py`,
    `tests/e2e/test_web_workflow.py`) und manuelle Prüfung abgedeckt;
    Playwright wäre ein zusätzliches Paket und laut Checkliste nur Bonus.
  - `cd.yml` mit echtem Deploy: erst nach dem Einrichten von Render, Neon
    und dem Environment `production` (Phase 5).
  - Echter Render-Deploy und Smoke-Test gegen die Live-URL: Phase 5.
  - Workflows haben keine pytest-Tests; Beleg sind die grünen Läufe von CI
    und Release.
  - Branch-Schutz auf `main` (empfohlen, nicht verlangt): noch nicht aktiv,
    muss in den GitHub-Einstellungen gesetzt werden.

### Fast Track: Code-Review vom 21.10.

- **Umfang:** Fehler F1–F3 und Spec-Abweichung S1 aus dem Code-Review vom
  21.10. beheben, ungenutzten Code entfernen. Keine neue Funktion, keine
  API- oder Datenänderung.
- **Grund:** CSRF-Prüfung liess Anfragen ohne Cookie und Header durch
  (`None == None`), entgegen ADR-002; `alembic/env.py` sah die Modelle nicht
  (autogenerate hätte alle Tabellen gelöscht); der Seed setzte deaktivierte
  Szenarien und geänderte Fristen zurück, entgegen ADR-003; der Friststatus
  nahm den besten statt den ersten bestandenen Versuch, entgegen UC-002 AC-006.
- **Akzeptanz:** POST ohne CSRF-Cookie und -Header ergibt 403; `alembic check`
  meldet nach `upgrade head` keine Änderungen; ein erneuter Seed lässt
  deaktivierte Szenarien und geänderte Fristen unverändert; rechtzeitig
  bestanden und später verbessert bleibt `erledigt`.
- **Regressionstests:** `tests/integration/test_http.py`,
  `tests/integration/test_migrations.py`,
  `tests/integration/test_persistence.py`,
  `tests/unit/domain/test_scenario_and_round.py`.

### Fast Track: Rundenstart per POST

- **Umfang:** Modulliste zeigt „Runde fortsetzen“ oder „Neue Runde starten“;
  neue Runden nur per POST-Formular mit CSRF-Feld.
- **Grund:** GET `/mitarbeitende/module/{modul}` legte eine Runde an
  (Zustandsänderung per GET, ohne CSRF).
- **Akzeptanz:** GET zeigt nur eine offene Runde oder leitet zur Modulliste
  zurück und legt keine Runde an; POST ohne CSRF ergibt 403.
- **Regressionstests:** `tests/unit/application/test_use_cases.py`,
  `tests/integration/test_web.py`, `tests/e2e/test_web_workflow.py`.

### Fast Track: Architektur-Review

- **Umfang:** Szenario-Speichern, Session-Ablauf, 422-Fehlerverträge,
  Infrastructure-Verschiebungen und dokumentierte Startbefehle korrigieren.
- **Grund:** ADR-002/ADR-003 und die Clean-Architecture-Regel sind im Review
  verletzt; bestehende API-Verträge sollen erhalten bleiben.
- **Akzeptanz:** Deaktivierte Szenarien bleiben deaktiviert, abgelaufene
  Sessions ergeben 401, ungültige Antworten 422, Infrastructure enthält Clock
  und Authentifizierung, und PROJECT.md dokumentiert beide Startbefehle.
- **Geplante Regressionstests:**
  - Szenario bleibt nach dem Speichern einer Antwort deaktiviert;
    `tests/integration/test_persistence.py`.
  - Abgelaufenes Session-Cookie ergibt 401;
    `tests/integration/test_http.py`.
  - Fehlendes/ungültiges JSON sowie fehlende Felder ergeben 422;
    `tests/integration/test_http.py`.
  - Import- und Composition-Root-Prüfung für `clock.py`, `auth.py` und
    `main.py`; `tests/unit/test_main_configuration.py` sowie lint-imports.
  - Commands-Dokumentation wird manuell gegen `docs/PROJECT.md` geprüft.
- **Checks:** `python -m pytest -q`, `ruff check .`,
  `PYTHONPATH=src lint-imports`, Coverage.

## Backlog

- UC-001 (`docs/specs/UC-001-SZENARIO-RUNDE-SPIELEN.md`) – erledigt, live seit v0.1.1
- UC-002 (`docs/specs/UC-002-SCHULUNG-STEUERN.md`) – erledigt, live seit v0.1.1
- UC-003 KI-Entwurf von Fällen – optional, nicht spezifiziert und nicht umgesetzt (Idee in `docs/PROJECT.md`)

## Meilensteine

| Datum | Ziel |
|---|---|
| 16.10. | Phase 0 auf main (PROJECT.md, Struktur, ADR-001) |
| 19.–21.10. | UC-001 entwickeln, TDD und CI |
| 22.10. | UC-001-PR prüfen und mergen |
| 23.10. | UC-001 validieren, deployen, Smoke-Test |
| 24.–25.10. | UC-002 entwickeln, TDD und CI |
| 26.10. | UC-002-PR, mergen, deployen |
| 27.–28.10. | README, AI-LOG, Modellvergleich, Präsentation |
| 29.10. | Abgabe und Präsentation |

## Working agreement

- Keep one active use case small enough to deliver vertically.
- Update this file when the lifecycle phase or active use case changes.
- Link decisions and validation evidence from the relevant project artefact.
- One AI-LOG entry per agent session.
