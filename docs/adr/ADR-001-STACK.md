# ADR-001: Python-FastAPI-Stack und Clean Architecture

Status: Accepted
Datum: 2026-10-19
Entschieden von: Projektteam

## Kontext

Die Anwendung ist eine Webplattform für fiktive Datenschutzfälle der Gemeinde
Grenchen. Sie benötigt eine klare Trennung von Fachlogik, Use Cases,
Webschnittstellen und technischen Adaptern. PostgreSQL wird für das Deployment
auf Neon verwendet; lokale Tests dürfen SQLite verwenden.

## Alternativen

- A: Python mit FastAPI, Jinja2, SQLAlchemy und Alembic in Clean Architecture.
- B: Ein Full-Stack-Framework mit vermischter Web-, Datenbank- und Fachlogik.

## Entscheid

Wir verwenden Python 3.12, FastAPI, Jinja2, SQLAlchemy und Alembic. Die
Anwendung folgt Clean Architecture mit den Schichten Domain, Application,
Interfaces und Infrastructure. Die Abhängigkeiten zeigen nach innen:

`Interfaces / Infrastructure -> Application -> Domain`

PostgreSQL wird auf Neon betrieben. SQLite ist für lokale Tests zulässig.
Der KI-Zugriff von UC-003 wird über einen eigenen Application-Port und einen
Infrastructure-Adapter zum FHNW-LiteLLM-Proxy umgesetzt. Tests verwenden eine
Fake-KI.

## Konsequenzen

Die Domain bleibt framework-unabhängig und kann isoliert getestet werden.
Repository-, Uhr- und KI-Ports müssen in der Application-Schicht definiert und
in Infrastructure implementiert werden. Die Schichtenregel wird in CI geprüft.
Datenbankmigrationen werden mit Alembic verwaltet. Deployment und Betrieb
verwenden Docker, Render und Neon.

Diese Entscheidung wird in `docs/PROJECT.md` und den CI/CD-Workflows umgesetzt.
