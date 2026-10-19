# Datenschutzfälle im Gemeindewesen

## Purpose

Gemeinden müssen Mitarbeitende regelmässig im Datenschutz schulen. Heute ist
schwer nachvollziehbar, wer geschult wurde, welche Risiken in einzelnen
Abteilungen bestehen und ob Mitarbeitende Datenschutzsituationen im Arbeitsalltag
korrekt beurteilen können.

Das Projekt entwickelt dafür eine Compliance-Schulungsplattform für eine
fiktive Schweizer Stadtverwaltung. Mitarbeitende trainieren typische
Datenschutzsituationen in kurzen Szenario-Runden. Die Verwaltung kann den
Schulungsstatus nachweisen und Risiken auf Teamebene erkennen, ohne einzelne
Mitarbeitende durch Detailauswertungen offenzulegen.

Die Anwendung ist eine interaktive Datenschutz-Schulungsplattform.
Mitarbeitende lösen realistische, auf Grenchen zugeschnittene Datenschutzfälle
aus ihrem Arbeitsalltag. Sie erhalten direkt eine Erklärung und eine Bewertung.
Abteilungsleitungen sehen anonymisierte beziehungsweise aggregierte Ergebnisse
ihrer Abteilung. Datenschutzverantwortliche können Fälle und Schulungsmodule
verwalten sowie den Schulungsstand der Gemeinde kontrollieren.

### Kernfunktionen der ersten Version

1. Login für Mitarbeitende, Abteilungsleitungen und
	Datenschutzverantwortliche. Die Registrierung erfolgt mit einer
	`@grenchen.example`-E-Mail-Adresse; danach werden Benutzer, Abteilung und Rolle
	anhand der hinterlegten Adresse zugeordnet.
2. Datenschutzfälle als interaktive Szenarien lösen.
3. Sofortige Bewertung mit Erklärung.
4. Schulungsfortschritt und Abschlussstatus anzeigen.
5. Aggregierte Abteilungsauswertung anzeigen.
6. Fälle und Schulungsmodule verwalten.

### Zielgruppe und Rollen

Die Anwendung richtet sich primär an Mitarbeitende der Gemeinde Grenchen und
ist auf deren Verwaltungsalltag zugeschnitten. Die Grundstruktur soll später
auch von anderen Gemeinden übernommen werden können.

- **Mitarbeitende** der Gemeinde Grenchen spielen Szenarien ihrer eigenen
  Abteilung und sehen nur ihre eigenen Ergebnisse.
- **Abteilungsleitungen** sehen den Schulungsstatus der eigenen Abteilung.
  Punkte und Fehler werden nur aggregiert und erst ab drei Personen angezeigt.
- **Datenschutzverantwortliche** verwalten Szenarien, weisen Module zu und
  sehen die Auswertung aller Abteilungen.

### In scope

- Selbst erstelltes Konto mit einer fiktiven Demo-E-Mail-Adresse im Format
	`@grenchen.example` und
	Passwort. Nach `Create account` werden Benutzer, Abteilung und Rolle anhand
	einer hinterlegten Grenchen-E-Mail-Adresse zugeordnet.
- Die erste Version enthält realistische, fiktive Datenschutzfälle aus dem
	Arbeitsalltag einer Gemeinde nach dem Vorbild von Grenchen (Kanton
	Solothurn, InfoDG).
- Abgedeckt sind die Abteilungen Einwohnerdienste, Soziale Dienste sowie
	Finanzen und Informatik, mit je fünf Startfällen.
- Jeder Fall enthält eine Situation, drei bis vier Antwortmöglichkeiten,
	genau eine richtige Antwort, eine kurze Erklärung und die Rechtsgrundlage
	(zum Beispiel einen Artikel des InfoDG).
- UC-001: eine Szenario-Runde spielen, Antworten bewerten, Erklaerungen und
	ein Abzeichen ab 80 Prozent anzeigen. Ein Versuch gilt ab 80 Prozent
	richtigen Antworten als bestanden.
- UC-002: Module mit Frist zuweisen, Status anzeigen, aggregiert auswerten und
	einen Schulungsnachweis als CSV exportieren.
- Szenarien werden initial als Seed-Daten geladen. Veröffentliche Szenarien und
	ihre Antwortoptionen sind unveränderlich. Die Datenschutzverantwortliche kann
	neue Szenarien anlegen und bestehende über `Scenario.active` deaktivieren.
	Ein fehlerhafter Fall wird deaktiviert und durch ein neues Szenario ersetzt.
- Neue Runden verwenden nur aktive Szenarien. Laufende Runden und alte
	`RoundAnswer`-Einträge bleiben gültig, weil sich ihr Szenario nicht ändert.
- Eine separate Szenario-Versionierung ist nur eine mögliche spätere Erweiterung.
- Es werden keine echten Personendaten verwendet.
- Mitarbeitende dürfen eine Runde wiederholen. Für den Schulungsstatus zählt
	der beste bestandene Versuch. Frühere Versuche bleiben gespeichert, damit
	der Lernfortschritt nachvollziehbar bleibt.

### Auswertungsregeln

- Mitarbeitende sehen nur ihre eigenen Ergebnisse.
- Abteilungsleitungen sehen den Status ihrer eigenen Abteilung.
- Punkte und Fehler werden für Abteilungsleitungen nur als aggregierte
	Teamwerte angezeigt.
- Die Auswertung wird erst ab mindestens drei Personen mit abgeschlossenem
	Versuch eingeblendet, damit keine Rückschlüsse auf Einzelpersonen möglich
	sind.
- Datenschutzverantwortliche sehen die Auswertung aller Abteilungen.

### Verwaltung von Fällen und Modulen

Datenschutzverantwortliche können neue Datenschutzfälle erstellen und bestehende
Fälle deaktivieren. Veröffentliche Szenarien und ihre Antwortoptionen werden
nicht bearbeitet oder gelöscht. Sie können mehrere Fälle zu einem Schulungsmodul
zusammenfassen, das Modul einer Abteilung zuweisen und eine Frist festlegen.

Fiktive Seed-Daten, automatisierte Tests und lokaler Betrieb mit PostgreSQL oder
SQLite fuer die Entwicklung gehören zum Projektumfang.

### Sicherheit und Datenschutz

Die Anwendung verarbeitet nur fiktive Daten. Es werden keine echten
Personendaten der Gemeinde Grenchen verwendet. Passwörter werden mit Argon2
gehasht und nicht im Klartext gespeichert. Die Session wird über ein sicheres
Cookie geschützt (`HttpOnly`, `Secure`, `SameSite`). Formulare verwenden
CSRF-Schutz. Rollen und Zugriffsrechte werden serverseitig geprüft.

Die Zugriffsregeln liegen in der Application-Schicht und werden dort mit
Unit-Tests geprüft. Sicherheit steckt damit nicht nur im Web-Layer.

Mitarbeitende sehen nur eigene Ergebnisse. Abteilungsleitungen sehen nur
aggregierte Daten ihrer Abteilung, und Teamwerte werden erst ab drei Personen
angezeigt, damit keine Rückschlüsse auf Einzelpersonen möglich sind.

Geheimnisse wie Datenbank- und LiteLLM-Zugangsdaten werden ausschließlich über
Umgebungsvariablen beziehungsweise GitHub Secrets verwaltet und nicht ins
Repository eingecheckt.

### Optionale Erweiterung: UC-003 KI-Szenarioentwurf

UC-003 wird nur umgesetzt, wenn UC-001 und UC-002 inklusive Tests und
Deployment fertiggestellt sind. Ohne UC-003 ist das Projekt vollständig.

Die Datenschutzverantwortliche kann aus einem Artikel des InfoDG einen Entwurf
für einen neuen Datenschutzfall erstellen lassen. Der Entwurf enthält eine
Situation, drei bis vier Antwortmöglichkeiten, eine richtige Antwort, eine
Erklärung und eine vorgeschlagene Rechtsgrundlage. Jeder KI-Entwurf wird als
Entwurf gekennzeichnet und muss vor der Veröffentlichung manuell geprüft und
freigegeben werden. Die KI veröffentlicht keine Fälle automatisch und liefert
keine verbindliche Rechtsberatung. An die KI werden keine Personendaten
übermittelt.

Im Projekt erfolgt der Zugriff über den LiteLLM-Proxy der FHNW. Im echten
Betrieb würde die Gemeinde ein in der Schweiz gehostetes Modell verwenden,
zum Beispiel Apertus (Swiss AI) oder Azure OpenAI in der Region Schweiz.
Die KI ist über einen eigenen Port angebunden. Dadurch kann das Modell ohne
Codeänderung ausgetauscht werden; Tests verwenden eine Fake-KI und führen
keinen echten KI-Aufruf aus.

### Out of scope

- Mobile App, Single Sign-on, E-Mail-Benachrichtigungen und
	Mehrmandantenfaehigkeit.
- Echte Personendaten oder vertrauliche Verwaltungsdaten der Gemeinde
	Grenchen.
- Rechtsberatung: Rechtliche Aussagen werden als zu pruefende Hinweise
	behandelt und nicht als verbindliche Rechtsauskunft.
- Automatisch veröffentlichte KI-Inhalte und die Übermittlung von Personendaten
  an ein KI-Modell.

## Architecture

The application uses Clean Architecture. Dependencies always point inward:

`Interfaces / Infrastructure -> Application -> Domain`

- **Domain** contains entities and business rules such as evaluation, the
  badge at 80 percent and team values from three people. It imports no
  FastAPI, SQLAlchemy, Jinja2 or HTTPX code.
- **Application** contains use cases, access-control rules and ports for
  repositories, the clock and the optional KI integration.
- **Interfaces** provides API endpoints, HTML pages with Jinja2 and CSV export.
- **Infrastructure** implements the ports: SQLAlchemy database access,
  authentication, session management and the LiteLLM adapter.

The dependency direction is checked automatically in CI. Important architecture
decisions are documented as ADRs under `docs/adr/`, especially the choice of
Python/FastAPI, PostgreSQL/SQLAlchemy with Neon and the replaceable KI port.

The application is implemented as a web application with Python 3.12, FastAPI,
Jinja2 and SQLAlchemy. Database migrations use Alembic. PostgreSQL is the
database for deployment on Neon; SQLite is permitted for local tests.

Unit and integration tests use pytest. End-to-end tests for API endpoints and
workflows use pytest with FastAPI TestClient and HTTPX in `tests/e2e/`.
Playwright browser tests for important workflows, such as playing UC-001, are
optional if time allows.
Passwords are hashed with Argon2, and forms are protected against CSRF.
Development takes place in the Dev Container. Deployment uses Neon for
PostgreSQL and Render for the application.

### Domain model

The domain model contains these entities:

1. `Department` - department of the municipality.
2. `Employee` - person with a role who belongs to exactly one department.
3. `Scenario` - immutable published privacy case with situation, explanation,
   legal basis and `active` flag.
4. `AnswerOption` - answer option for a scenario; exactly one option is
	correct.
5. `Module` - groups several scenarios.
6. `Assignment` - assigns a module to a department with a due date.
7. `GameRound` - one attempt by an employee to complete a module.
8. `RoundAnswer` - an employee's answer to a scenario, including the selected
   option and answer timestamp.

`GameRound` stores the `attempt_number`, completion data, calculated score and
whether the attempt passed. The score and pass status are stored when the round
is completed, which simplifies department reports and CSV exports. If a module
is played more than once, the best attempt determines the training status.

Published scenarios and their answer options are immutable. A faulty scenario
is deactivated and replaced by a new scenario; new rounds use only active
scenarios. Existing rounds and answers remain valid because their scenarios do
not change. A badge is not stored as a separate entity; it is calculated from
the best attempt when the score reaches 80 percent. Access rules are enforced
in application use cases and covered by application-layer unit tests, not only
in the web interface.

### Required business rules

- Team aggregates are available only for groups of at least three people.
- The current date is supplied through a clock port; domain and application
	code never call `datetime.now()` directly.
- A repeated round is allowed. The best attempt determines status and badges;
	all attempts remain available for error analysis.
- A published scenario cannot be edited or deleted; deactivation and a new
	replacement scenario are used for corrections.
- Passwords use Argon2. Forms use CSRF protection. Session cookies
	are HttpOnly, Secure and SameSite. Die Zuordnung von Benutzer, Abteilung und
	Rolle wird serverseitig geprüft und nicht aus frei eingegebenen Formularwerten
	übernommen.
- Secrets are read from environment variables and never committed.

## Structure

```text
src/app/
	domain/          # entities and pure business rules
	application/     # use cases and ports
	interfaces/      # HTTP routes, views and schemas
	infrastructure/  # database and external adapters
tests/
	unit/
	integration/
	e2e/
docs/
	specs/
	adr/
```

## Commands

Run commands from the repository root with the project virtual environment
activated.

| Activity | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Unit tests | `pytest tests/unit -q` |
| Integration tests | `pytest tests/integration -q` |
| E2E API tests | `pytest tests/e2e -q` |
| Optional browser tests | `playwright test` |
| Run locally | `uvicorn app.interfaces.http:app --reload` |
| Coverage | `pytest --cov=src/app --cov-report=term-missing` |
| Build/release | `docker build -t datenschutzfaelle-gemeindewesen .` |

These commands describe the target project structure. The test and application
paths become executable during DEVELOP after the corresponding vertical slices
are implemented.

## CI/CD and deployment

The application is built as a Docker container and deployed on Render. The
PostgreSQL database runs on Neon. Render auto-deploy is disabled; deployments
are started explicitly through a Render Deploy Hook.

- `ci.yml` runs on every push and pull request. It checks code quality with
	linting, verifies that the Domain layer imports no framework code, and runs
	unit and integration tests.
- `release.yml` builds the Docker image, runs the E2E API tests and publishes
	the image only after all tests have passed.
- `cd.yml` starts deployment through the Render Deploy Hook. During deployment,
	Alembic database migrations are executed before the application is exposed.
- After deployment, a smoke test calls the health endpoint and verifies that
	the live application is reachable.

Secrets are stored exclusively in GitHub Secrets for CI/CD or in a local
gitignored `.env` file. Secrets are never stored in source code.

The README documents the purpose of the application, the Grenchen-specific
privacy cases, the roles, and the use cases with references to `docs/specs/`.
It also documents the architecture, local startup in the Dev Container, test
commands, CI/CD, the live URL with demo access for each role, the AI tools used
and the MCP server with its purpose and permissions.

The README refers to the AI protocol in `docs/AI-LOG.md` and the architecture
decisions in `docs/adr/`. It states explicitly that the application uses only
fictional data and does not provide legal advice.

### Nachweise für Dokumentation und Präsentation

Die Präsentation und das README enthalten folgende überprüfbare Nachweise:

- kurze Live-Demo von UC-001 auf der Live-URL bei Render;
- Beispiel der rollenabhängigen Auswertung für Mitarbeitende und
	Abteilungsleitungen, einschliesslich der Teamwerte ab drei Personen;
- Architekturdiagramm mit Clean-Architecture-Schichten und Ports;
- Testresultate mit Testabdeckung für Unit-, Integrations- und E2E-Tests;
- TDD-Nachweis anhand eines Commit-Verlaufs mit zuerst rotem und danach grünem
	Test;
- CI/CD-Workflow mit `ci.yml`, `release.yml` und `cd.yml` inklusive eines
	erfolgreichen Durchlaufs;
- `docs/AI-LOG.md` mit verwendeten Modellen, Prompts und Lernerkenntnissen;
- konkretes Beispiel für den Einsatz eines Skills und eines MCP-Servers, zum
	Beispiel der Develop-Skill für die TDD-Umsetzung von UC-001 sowie ein
	Playwright-MCP-Server für einen E2E-Test mit ausschliesslichen Test- und
	Browser-Rechten.

## Dependencies and configuration

The dependency manifest is `requirements.txt`. Runtime dependencies are
FastAPI, Uvicorn, Jinja2, SQLAlchemy, Alembic, a PostgreSQL driver, Argon2
support and HTTPX. Development dependencies include pytest, pytest-cov,
import-linter and pip-audit. Playwright is an optional development dependency
for browser tests.

Required configuration variable names:

- `DATABASE_URL`
- `SESSION_SECRET`
- `ENVIRONMENT`
- `LLM_API_KEY` (only for optional UC-003)
- `LLM_MODEL` (only for optional UC-003)

Local secrets belong in a gitignored `.env`; `.env.example` contains only
placeholders. Production secrets belong in GitHub Secrets, Render and Neon.
