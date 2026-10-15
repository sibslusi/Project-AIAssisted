# ADR-001: Technologie-Stack

Status: Proposed
Datum: 2026-10-15
Entschieden von: (offen, Bestätigung durch Sibslusi)

## Kontext
Bis zur Abgabe am 29.10.2026 bleiben 2 Wochen, und ich arbeite allein. Verlangt sind eine Full-Stack-Anwendung mit Clean Architecture, ORM, TDD auf drei Teststufen sowie CI/CD mit Docker und Cloud-Deployment. Das Kurs-Template ist auf Python und FastAPI ausgerichtet (Devcontainer, `launch.json`, `requirements.txt`).

## Alternativen
- **A: Python, FastAPI, Jinja2, SQLAlchemy, PostgreSQL:** passt zum Template, alles in einer Sprache, serverseitig gerendertes Frontend
- **B: FastAPI-Backend mit separatem React-Frontend:** moderneres UI, aber zwei Build-Prozesse, mehr Tests und mehr Deployment-Aufwand
- **C: Django:** viel eingebaut (Admin, Auth), passt aber schlecht zur verlangten Clean Architecture, weil Modelle und ORM eng gekoppelt sind

## Entscheid
Variante A:
- Python 3.12, FastAPI, Jinja2-Templates
- SQLAlchemy 2 und Alembic
- lokal SQLite, in Docker und Cloud PostgreSQL (Neon)
- pytest, pytest-cov, Playwright, import-linter
- argon2 für Passwörter
- Deployment: Docker-Image auf Render

## Konsequenzen
- Einfacher: eine Sprache, ein Deployment, kurze CI. Das Template lässt sich direkt nutzen.
- Schwieriger: Die Oberfläche bleibt schlicht. Dafür gibt es in der Bewertung keine Punkte.
- Neon statt Render-Postgres, weil die Gratis-Datenbank von Render nach 30 Tagen gelöscht wird (SW4).
- PROJECT.md ist bereits angepasst. Die Schichtenregel ist in AGENTS.md festgehalten.
