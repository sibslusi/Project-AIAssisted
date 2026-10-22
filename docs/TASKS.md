# TASKS.md

PHASE: 4
STATUS: in-progress

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

## Current Use Case

Phase 4 Validate und Vorbereitung Phase 5 Deploy (CI/CD für UC-001/UC-002)

### Phase 4: Validate

- **Umfang:** Smoke-Test-Skript, Version in `/health`, Seed im Image,
  `ci.yml`, `release.yml`, `cd.yml`, `scripts/deploy.sh`, ADR-006.
- **Ergebnis:** 154 Tests grün, Coverage 96 %, Ruff (Check und Format),
  Import-Linter, `pip-audit` ohne Befund. Docker-Image lokal gebaut, mit
  PostgreSQL 16 und `RUN_SEED=true` gestartet, Smoke-Test mit Version und
  Login grün, auch nach Neustart (Seed zweimal). `alembic check` auf
  PostgreSQL und SQLite ohne Änderungen.
- **Dabei gefunden und behoben:** Seed scheiterte auf PostgreSQL am
  Fremdschlüssel `module_scenarios.scenario_id` (SQLite prüfte ihn nicht);
  `alembic check` meldete auf PostgreSQL eine Scheinänderung beim
  Unique-Constraint, der dem Primärschlüssel entspricht.
- **Ausgelassen, mit Grund:**
  - `release.yml` und `cd.yml` laufen erst mit einem Tag bzw. nach dem
    Einrichten von Render und Neon (Teil B, von Hand); Prüfung bisher per
    Durchsicht, YAML-Parse und lokalem Nachstellen der Schritte.
  - Echter Render-Deploy und Smoke-Test gegen die Live-URL: Phase 5.
  - Workflows haben keine pytest-Tests; Beleg ist der grüne CI-Lauf im PR.

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

- docs/specs/UC-001-SZENARIO-RUNDE-SPIELEN.md – Mitarbeitende spielen 5 Szenarien ihrer Abteilung, Punkte, Erklärung, Abzeichen ab 80 %
- docs/specs/UC-002-SCHULUNG-STEUERN.md – Module mit Frist zuweisen, Status und Auswertung gemäss Rollenrechten
- docs/specs/UC-003-KI-SZENARIO-ENTWURF.md – optional: KI-Entwurf aus Gesetzesartikel, Freigabe durch Datenschutzverantwortliche

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
