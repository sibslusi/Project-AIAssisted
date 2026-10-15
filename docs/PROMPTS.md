# Prompts pro Phase – „Datenschutz am Schalter“

Diese Prompts gibst du dem Coding-Agenten in VS Code, und zwar der Reihe nach. Jeder Prompt bearbeitet **einen** Schritt.
Am Ende jeder Phase führt der Agent automatisch den Quality Gate aus (`skills/ai-sdlc-quality-gate`): Er prüft eine Checkliste, belegt jeden Punkt, stellt Rückfragen und wartet auf dein OK. Danach prüfst du das Ergebnis, schreibst einen Eintrag in `docs/AI-LOG.md` und machst einen Commit.
Den Projektkontext schreibst du nur in Phase 0 aus. Danach steht er in `docs/PROJECT.md`.

---

## Phase 0 – BOOTSTRAP (einmal, Branch `bootstrap`)

```
Wir starten Phase 0 (BOOTSTRAP) gemäss AGENTS.md und skills/ai-sdlc-0-bootstrap. Schreibe noch keinen Anwendungscode.

Vorgehen in zwei Schritten:
- Schritt A: Prüfe das Repository, stelle mir deine Rückfragen und zeige mir einen Plan (Struktur, Entitäten, Dateien, die du änderst). Warte dann auf mein OK.
- Schritt B: Erst nach meinem OK legst du die Ordner an und schreibst die Dokumentation.

## Rahmen
Capstone-Projekt im Modul "AI-assisted Software Development" (FHNW), Abgabe 29.10.2026, also wenig Zeit: Halte alles minimal.
Anforderungen: Enterprise-Full-Stack-Anwendung, Clean Architecture (domain ← application ← interfaces ← infrastructure), mindestens 5 Entitäten mit ORM, mindestens 2 Use Cases, TDD mit Unit-, Integrations- und E2E-Tests, CI/CD mit Docker und Cloud-Deployment (Render für die App, Neon für PostgreSQL).

## Produkt
Compliance-Schulungsplattform für Gemeinden: "Datenschutz am Schalter".
Mitarbeitende einer fiktiven Schweizer Stadtverwaltung (Vorbild: Stadt Grenchen, Kanton Solothurn, kantonales InfoDG) trainieren Datenschutz mit realistischen Alltagsszenarien im Spielformat. Die Gemeinde kann nachweisen, dass geschult wurde, und sieht, wo Risiken bestehen. Sprache der Oberfläche: Deutsch.

## Abteilungen (Stammdaten, keine Rollen)
Stadtpräsidium/Stadtkanzlei, Finanzen und Informatik, Stadtkasse/Steuerregisteramt, Einwohnerdienste, Personalamt, Baudirektion, Schulverwaltung, Soziale Dienste Oberer Leberberg, Polizeiinspektorat.
Erste Version mit Szenarien nur für: Einwohnerdienste, Soziale Dienste, Finanzen und Informatik (je 5 Szenarien als Seed-Daten).

## Rollen (Berechtigungen)
1. Mitarbeitende: spielen Szenario-Runden ihrer Abteilung, sehen nur eigene Ergebnisse.
2. Abteilungsleitung: sieht nur die eigene Abteilung; pro Person nur den Status (erledigt / offen / Frist überschritten), Punkte und Fehler nur aggregiert fürs Team.
3. Datenschutzverantwortliche: verwaltet Szenarien, weist Module mit Frist zu, sieht Auswertung aller Abteilungen.
Abteilung und Rolle sind getrennt: Eine Person hat genau eine Abteilung und eine Rolle.
Login: einfacher Login mit Benutzername und Passwort (bcrypt oder argon2) und Session-Cookie (HttpOnly, Secure, SameSite), CSRF-Schutz für Formulare, Demo-Benutzer pro Rolle als Seed-Daten. Kein SSO.

## Entitäten (Vorschlag, bitte prüfen)
Abteilung, Mitarbeitende, Szenario (mit Versionsnummer und Feld "Rechtsgrundlage", z.B. "InfoDG SO, Art. …"), Antwortoption, Modul (Gruppe von Szenarien), Zuweisung (Modul an Abteilung mit Frist), Spielrunde, Rundenantwort (gewählte Antwort pro Szenario inkl. beantworteter Szenario-Version, nötig für die Fehlerauswertung), Abzeichen.

## Fachregeln (Domain, mit Unit-Tests)
- Mindestgruppengrösse: Aggregierte Team-Auswertungen werden erst ab 3 Personen angezeigt, sonst "zu wenige Teilnehmende" (Schutz vor Rückschluss auf Einzelpersonen).
- Fristen: Das aktuelle Datum wird der Logik als Parameter bzw. über einen Clock-Port übergeben, nie direkt datetime.now() in domain oder application.
- Wiederholung: Eine Runde darf wiederholt werden; für Status und Abzeichen zählt der beste Versuch, für die Fehlerauswertung alle Versuche. (Bitte als Annahme bestätigen lassen.)
- Szenario-Versionen: Wird ein Szenario geändert, entsteht eine neue Version; alte Rundenantworten bleiben unverändert gültig.
- Löschfrist (Version 2, nur dokumentieren): Detailantworten nach 12 Monaten löschen, Status "Schulung erledigt" bleibt.

## Use Cases
- UC-001 Szenario-Runde spielen: 5 Szenarien der eigenen Abteilung, Backend bewertet die Antworten, vergibt Punkte, zeigt eine Erklärung, schaltet ab 80 % richtigen Antworten ein Abzeichen frei (Schwelle konfigurierbar).
- UC-002 Schulung steuern: Module pro Abteilung mit Frist zuweisen, Status und aggregierte Auswertung gemäss Rollenrechten anzeigen, Schulungsnachweis als CSV exportieren (wer, welches Modul, wann erledigt) für die Datenschutzverantwortliche.
- UC-003 (optional, Innovation): KI erstellt aus einem Gesetzesartikel einen Szenario-Entwurf, die Datenschutzverantwortliche gibt ihn frei. LLM-Zugriff über LiteLLM (OpenAI-kompatibel), Key nur per Umgebungsvariable. In Tests wird das LLM durch einen Fake ersetzt.

## Technik und Grenzen
Python 3.12 (prüfe .python-version), FastAPI, Jinja2-Templates, SQLAlchemy 2 mit Alembic-Migrationen, PostgreSQL (lokal SQLite erlaubt), pytest, Playwright für E2E-Tests, import-linter für die Prüfung der Schichtenregeln.
Nur fiktive Daten, keine echten Personendaten. Keine Secrets im Repo (.env in .gitignore, .env.example mit Platzhaltern). Privacy by Design: Spielergebnisse sind Personendaten der Mitarbeitenden.
Out of Scope: Mobile App, SSO, E-Mail-Benachrichtigungen, echte Daten der Stadt Grenchen, Mehrmandantenfähigkeit.

## Deine Aufgabe
1. Prüfe die bestehende Repository-Struktur und schlage die minimal nötige Clean-Architecture-Struktur vor (src/app/domain, application, interfaces, infrastructure; tests/unit, integration, e2e).
2. Fülle docs/PROJECT.md aus: Zweck, Nutzer, In Scope, Out of Scope, Architektur, Entitäten mit Beziehungen, Rollen und Rechte, Commands, Konfigurationsvariablen.
3. Ergänze requirements.txt nur um das, was für den Stack fehlt.
4. Aktualisiere docs/TASKS.md (PHASE 0, Status) und lege den Backlog mit UC-001 bis UC-003 an. Die Specs selbst schreiben wir erst in Phase 1.
5. Schlage für die Stack-Wahl ein ADR vor (docs/adr/ADR-001-stack.md, Status: Proposed).
6. Schlage MCP-Server für die Entwicklung vor (Context7 für aktuelle FastAPI-/SQLAlchemy-Doku, Playwright-MCP für E2E-Tests) und dokumentiere in README-Abschnitt "KI-Tooling" Zweck und Rechte.
7. Liste offene Fragen und getroffene Annahmen auf. Lösche keine Dateien ohne meine Bestätigung.
Schliesse mit dem Quality Gate gemäss skills/ai-sdlc-quality-gate ab und warte auf mein OK, bevor STATUS auf done gesetzt wird.
```

Danach: PR öffnen → eine Person aus dem Team reviewt → Merge → ADR-001 auf „Accepted“ setzen.

---

## Phase 1 – SPECIFY (pro Use Case, Branch `uc-001-...`)

```
Phase 1 SPECIFY für UC-001 "Szenario-Runde spielen" gemäss skills/ai-sdlc-1-specify.
Nutze docs/specs/UC-TEMPLATE.md. Schreibe keinen Code und keine Tests.

Achte besonders auf:
- Akzeptanzkriterien als Given/When/Then, jedes einzeln testbar (z.B. "Given 4 von 5 richtig, When Runde abgeschlossen, Then Abzeichen vergeben").
- Fehlerfälle: nicht eingeloggt, Szenario aus fremder Abteilung, Runde bereits abgeschlossen, ungültige Antwort.
- Rollenrechte aus docs/PROJECT.md.
- Im Abschnitt Tests: welche Kriterien als Unit-, Integrations- und E2E-Test geprüft werden.
Stelle Rückfragen, wenn eine Regel unklar ist. Aktualisiere docs/TASKS.md.
Schliesse mit dem Quality Gate gemäss skills/ai-sdlc-quality-gate ab und warte auf mein OK, bevor STATUS auf done gesetzt wird.
```

Für UC-002 tauschst du Name und Fokus aus. Fokus dort: **Rechte der Abteilungsleitung** (nur Zusammenfassungen, nur die eigene Abteilung) und **Fristen** (offen, erledigt, Frist überschritten).

---

## Phase 2 – DESIGN

```
Phase 2 DESIGN für UC-001 gemäss skills/ai-sdlc-2-design. Kein Anwendungscode.
1. Bestimme die minimalen Komponenten pro Schicht (Entitäten, Use-Case-Service, Repository-Ports, Adapter, Endpoints/Seiten).
2. Beschreibe im Abschnitt "Tests" der UC-Spec die E2E-Testfälle (Schritte und erwartetes Ergebnis) für jedes Akzeptanzkriterium. Den Playwright-Code schreiben wir erst in Phase 4.
3. Ergänze ein Mermaid-Diagramm der Schichten und Entitäten in docs/PROJECT.md, falls es noch fehlt.
4. Wichtige Entscheide als ADR (Status Proposed).
Aktualisiere docs/TASKS.md.
Schliesse mit dem Quality Gate gemäss skills/ai-sdlc-quality-gate ab und warte auf mein OK, bevor STATUS auf done gesetzt wird.
```

---

## Phase 3 – DEVELOP

```
Phase 3 DEVELOP für UC-001 gemäss skills/ai-sdlc-3-develop, strikt TDD.
Arbeite in kleinen Schritten und committe jeden Schritt einzeln, damit TDD in der Git-Historie sichtbar ist:
1. "test: ..." – fehlschlagender Test (RED), Testlauf zeigen
2. "feat: ..." – minimaler Code, Test grün (GREEN)
3. "refactor: ..." – aufräumen, Tests weiterhin grün
Reihenfolge: Integrationstests, dann Unit-Tests, dann Implementierung.
Domain-Schicht ohne Imports von fastapi, sqlalchemy oder jinja2. Prüfe das mit import-linter.
Zeige mir am Ende die Testergebnisse und aktualisiere docs/TASKS.md.
Schliesse mit dem Quality Gate gemäss skills/ai-sdlc-quality-gate ab und warte auf mein OK, bevor STATUS auf done gesetzt wird.
```

---

## Phase 4 – VALIDATE

```
Phase 4 VALIDATE gemäss skills/ai-sdlc-4-validate.
1. Führe Unit-, Integrations- und E2E-Tests lokal aus und zeige die Ergebnisse, inklusive Testabdeckung (pytest-cov).
2. Prüfe bzw. erstelle Dockerfile und docker-compose (App + PostgreSQL) und starte die App lokal.
3. Prüfe .github/workflows/ci.yml: Lint, import-linter, Unit- und Integrationstests, Laufzeit unter 10 Minuten.
4. Prüfe .github/workflows/release.yml: Container bauen, E2E-Tests, Artefakt veröffentlichen.
5. Ergänze einen Sicherheits-Check (pip-audit) im CI und aktiviere Dependabot.
Erfasse Ergebnisse und fehlende Checks mit Begründung in docs/TASKS.md.
Schliesse mit dem Quality Gate gemäss skills/ai-sdlc-quality-gate ab und warte auf mein OK, bevor STATUS auf done gesetzt wird.
```

---

## Phase 5 – DEPLOY (einmal, zusammen entscheiden)

```
Phase 5 DEPLOY gemäss skills/ai-sdlc-5-deploy.
Plattform: Render (Web Service, Docker) für die App, Neon für PostgreSQL.
Entscheid: Deploy nur bei einem Release, nicht bei jedem Merge.
1. Schlage cd.yml vor (Trigger: Release, Deploy-Hook als GitHub Secret RENDER_DEPLOY_HOOK, danach Smoke-Test der öffentlichen URL).
2. Liste die nötigen Umgebungsvariablen und Secrets auf (nur Namen, keine Werte).
3. Erstelle nichts ohne meine Bestätigung. Erfasse das Ergebnis in docs/TASKS.md.
Schliesse mit dem Quality Gate gemäss skills/ai-sdlc-quality-gate ab und warte auf mein OK, bevor STATUS auf done gesetzt wird.
```

---

## Extra-Prompts

**Code-Review vor dem PR**
```
Prüfe die Änderungen dieses Branches gegen AGENTS.md: Schichtenregel, TDD-Reihenfolge, Rollenrechte, Secrets, Datenschutz der Spielergebnisse. Liste Probleme nach Schweregrad. Ändere nichts.
```

**Seed-Szenarien**
```
Erstelle 5 realistische, fiktive Szenarien für die Abteilung <Abteilung> einer Schweizer Stadtverwaltung (Kanton Solothurn).
Pro Szenario: Situation (2–3 Sätze), 3 Antwortoptionen, genau eine richtige, kurze Erklärung mit Hinweis auf das Prinzip (Zweckbindung, Datensperre, Need-to-know usw.).
Keine echten Namen. Format: Seed-Datei gemäss docs/PROJECT.md. Markiere rechtliche Aussagen, die ich prüfen muss.
```

**README am Schluss**
```
Schreibe README.md neu: Zweck, Screenshot-Platzhalter, Architekturdiagramm (Mermaid), Rollen, lokaler Start (Docker), Tests, CI/CD, Live-URL, eingesetzte KI-Tools und Modelle mit Begründung, MCP-Server mit Rechten, Grenzen ("keine Rechtsberatung, fiktive Daten").
```
