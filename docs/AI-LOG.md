# AI-LOG – Einsatz der KI im Projekt

Pro Agenten-Sitzung ein kurzer Eintrag. Daraus entsteht am Schluss die Reflexion in der Präsentation (40 % der Note).

| Datum | Phase / UC | Agent + Modell | Auftrag (kurz) | Ergebnis | Was ich korrigieren musste | Lernpunkt |
|---|---|---|---|---|---|---|
| 2026-10-15 | 0 / – | z.B. Copilot + gpt-5.4-mini via LiteLLM | Bootstrap: PROJECT.md, Struktur | PROJECT.md erstellt | Entität „Rundenantwort“ fehlte | Rückfragen vor dem Schreiben verlangen |
| 2026-10-19 | 0 / – | GitHub Copilot | Projektnamen gemeinsam präzisieren | Name auf „Datenschutzfälle im Gemeindewesen“ geändert | – | Entscheidungen punktweise mit der Nutzerin abstimmen |
| 2026-10-19 | 0 / – | GitHub Copilot | Problemdefinition gemeinsam abstimmen | Problemformulierung bestätigt und in PROJECT.md übernommen | – | Problem vor Lösung und Umsetzung festhalten |
| 2026-10-19 | 0 / – | GitHub Copilot | Zielgruppe gemeinsam präzisieren | Gemeinde Grenchen als primäre Zielgruppe und spätere Übertragbarkeit auf andere Gemeinden festgelegt | Optionale Admin-Rolle entfernt | Zielgruppe und Produktgrenzen klar trennen |
| 2026-10-19 | 0 / – | GitHub Copilot | Lösungsidee gemeinsam abstimmen | Interaktive Plattform mit Grenchen-spezifischen Fällen, Erklärungen, Bewertungen und aggregierten Auswertungen bestätigt | – | Erst Problem und Zielgruppe, dann Lösung festlegen |
| 2026-10-19 | 0 / – | GitHub Copilot | Login gemeinsam präzisieren | Selbst erstelltes Konto mit `@grenchen.ch`-E-Mail und serverseitiger Zuordnung von Benutzer, Abteilung und Rolle festgelegt | – | Rollen und Abteilungen nicht aus frei eingegebenen Werten ableiten |
| 2026-10-19 | 0 / – | GitHub Copilot | Kernfunktionen erneut abstimmen | Ursprüngliche Liste mit Login, interaktiven Fällen, Bewertung, Fortschritt, Auswertung sowie Fall- und Modulverwaltung wiederhergestellt | – | Bestätigte Anforderungen bei späteren Änderungen beibehalten |
| 2026-10-19 | 0 / – | GitHub Copilot | Datenschutzfälle gemeinsam konkretisieren | Fiktive Grenchen-Fälle mit je fünf Startfällen pro Abteilung, 3–4 Antworten, Rechtsgrundlage und Versionierung festgelegt | – | Rechtliche Hinweise als prüfbare Grundlage dokumentieren |
| 2026-10-19 | 0 / – | GitHub Copilot | Bestehensgrenze gemeinsam festlegen | Ein einzelner Versuch gilt ab 80 Prozent richtigen Antworten als bestanden | – | Bestehensgrenze explizit von allgemeinem Lernfortschritt trennen |
| 2026-10-19 | 0 / – | GitHub Copilot | Wiederholungen gemeinsam festlegen | Runden dürfen wiederholt werden; für den Schulungsstatus zählt der beste bestandene Versuch, frühere Versuche bleiben gespeichert | – | Lernfortschritt und Abschlussstatus getrennt modellieren |
| 2026-10-19 | 0 / – | GitHub Copilot | Auswertungsregeln gemeinsam bestätigen | Eigene Ergebnisse für Mitarbeitende, Abteilungsstatus und aggregierte Werte für Leitungen, Mindestgruppe drei, Vollzugriff für Datenschutzverantwortliche | – | Datenschutz durch rollenbezogene und aggregierte Auswertungen umsetzen |
| 2026-10-19 | 0 / – | GitHub Copilot | Verwaltungsfunktionen gemeinsam bestätigen | Datenschutzverantwortliche verwalten versionierte Fälle, Module, Abteilungszuweisungen und Fristen; abgeschlossene Runden behalten ihre Fallversion | – | Änderungen an Lerninhalten dürfen bestehende Resultate nicht verändern |
| 2026-10-19 | 0 / – | GitHub Copilot | Technische Basis gemeinsam festlegen | Python 3.12, FastAPI, Jinja2, SQLAlchemy, Alembic, PostgreSQL auf Neon, pytest, Playwright, Argon2, CSRF und Dev Container bestätigt | – | Technologie-, Sicherheits- und Testentscheidungen früh dokumentieren |
| 2026-10-19 | 0 / – | GitHub Copilot | Test- und Deployment-Strategie präzisieren | pytest mit FastAPI-TestClient/httpx für API-E2E-Tests in tests/e2e; Playwright nur optional; Neon und Render für das Deployment festgelegt | Playwright aus dem Pflichtumfang entfernt | Pflichtumfang realistisch an die verfügbare Zeit anpassen |
| 2026-10-19 | 0 / – | GitHub Copilot | Optionale Erweiterung UC-003 festlegen | KI-Szenarioentwurf über FHNW-LiteLLM-Proxy, eigener Port, manuelle Freigabe, keine Personendaten, Fake-KI in Tests; UC-003 erst nach UC-001/002 inklusive Tests und Deployment | – | Optionale Innovation darf die vollständige Kernlösung nicht gefährden |
| 2026-10-19 | 0 / – | GitHub Copilot | Sicherheits- und Datenschutzregeln gemeinsam festlegen | Fiktive Daten, Argon2, sichere Session-Cookies, CSRF, serverseitige Rechteprüfung, Mindestgruppe drei und Secrets über Umgebungsvariablen/GitHub Secrets bestätigt | – | Datenschutzanforderungen als überprüfbare technische Regeln formulieren |
| 2026-10-19 | 0 / – | GitHub Copilot | Zugriffsregeln architektonisch präzisieren | Zugriffsregeln liegen in der Application-Schicht und werden dort mit Unit-Tests geprüft | – | Sicherheitslogik nicht nur im Web-Layer verankern |
| 2026-10-19 | 0 / – | GitHub Copilot | CI/CD und Deployment gemeinsam festlegen | Docker auf Render, PostgreSQL auf Neon, CI bei Push/PR, Release mit E2E und Docker-Image, CD über Render Deploy Hook, Alembic-Migrationen und Health-Smoke-Test bestätigt | Auto-Deploy in Render ausgeschlossen | Deployment reproduzierbar und kontrolliert ausführen |
| 2026-10-19 | 0 / – | GitHub Copilot | README- und Präsentationsumfang präzisieren | README mit Zweck, Grenchen-Fällen, Rollen, Use Cases, Architektur, Dev-Container-Start, Tests, CI/CD, Live-URL, Demo-Zugängen, KI-Tools, MCP-Rechten, AI-LOG- und ADR-Verweisen festgelegt | – | Bewertungsnachweise früh als konkrete Dokumentationspunkte festhalten |
| 2026-10-19 | 0 / – | GitHub Copilot | Präsentationsnachweise konkretisieren | Live-Demo, Rollenvergleich, Architekturdiagramm, Testabdeckung, TDD-Commit-Verlauf, grüner CI/CD-Lauf sowie konkretes Skill- und MCP-Beispiel als Nachweise festgelegt | – | Bewertete Prozessnachweise mit konkreten Artefakten verknüpfen |
| 2026-10-19 | 0 / – | GitHub Copilot | Clean Architecture präzisieren | Abhängigkeiten zeigen nach innen: Interfaces/Infrastructure -> Application -> Domain; Uhr-Port, CI-Prüfung und ADRs unter docs/adr/ ergänzt | Pfeilrichtung der ursprünglichen Darstellung war missverständlich | Abhängigkeiten und Ports explizit dokumentieren |
| 2026-10-19 | 0 / – | GitHub Copilot | Domänenmodell gemeinsam festlegen | GameRound ergänzt; attempt_number, Punktzahl und Abschlussstatus liegen auf GameRound; Scenario.version bleibt ausreichend; Badge wird ab 80 Prozent berechnet | Badge-Entität entfernt | Ergebnisse für Auswertung und CSV-Export effizient speichern |
| 2026-10-19 | 0 / – | GitHub Copilot | Bootstrap-Lücken für Phase 0 schliessen | Clean-Architecture- und Testordner, .env.example, ADR-001 und bestätigte Dependencies ergänzt; weiterhin kein Anwendungscode | Phase 0 war ohne diese Artefakte noch nicht vollständig | Quality-Gate-Checks vor dem Commit ausführen |
| 2026-10-19 | 0 / – | GitHub Copilot | Quality Gate für Phase 0 ausführen | Quality Gate fand fehlende Bootstrap-Artefakte; danach wurden .env.example, ADR-001, Ordnerstruktur und Dependencies ergänzt. .env.example enthält nur Platzhalter, ADR-001 begründet Python/FastAPI und PostgreSQL/Neon, kein Anwendungscode vorhanden | Aktuell werden leere .gitkeep-Dateien verwendet, nicht __init__.py | Fehlende Artefakte als nachvollziehbaren Qualitätsnachweis dokumentieren |

## Modellvergleich (SW3-Aufgabe)

| Aufgabe | Modell A | Modell B | Qualität | Zeit | Kosten (LiteLLM Spend) |
|---|---|---|---|---|---|
| | | | | | |

## Wahl Agent + Modell und Begründung

- Agent:
- Modell(e):
- Warum:
