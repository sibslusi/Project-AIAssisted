# ADR-007: Logout macht das Session-Cookie ungültig

Status: Proposed
Datum: 2026-10-26
Entschieden von: Sibslusi (Auftrag „lösen“ nach der Repo-Prüfung vom 25.10.),
umgesetzt mit Claude Code

## Kontext

Die Session ist ein signiertes Cookie ohne Speicher auf dem Server (ADR-002).
Die Repo-Prüfung vom 25.10.2026 zeigte: Nach dem Logout blieb ein kopiertes
Cookie bis zu 8 Stunden gültig, weil der Server nichts über die Session wusste.

## Alternativen

- A: So lassen und als Grenze von V1 dokumentieren.
- B: Serverseitige Session-Tabelle, das Cookie enthält nur eine Session-ID.
- C: Session-Version pro Person in `employees`; das Cookie enthält die Version
  vom Login, der Logout erhöht sie.

## Entscheid

Variante C. `employees.session_version` (Migration `0002_session_version`,
Standard 0). Beim Login kommt die aktuelle Version ins signierte Cookie. Bei
jeder Anfrage vergleicht die Interfaces-Schicht sie über einen in `main.py`
eingesetzten Infrastructure-Adapter mit der Datenbank. Der Logout erhöht die
Version. Cookies ohne Version werden abgelehnt.

## Konsequenzen

- Ein kopiertes Cookie ist nach dem Logout sofort ungültig.
- Ein Logout beendet alle Sessions derselben Person, auch auf anderen Geräten.
- Jede Anfrage mit Session liest eine Zeile aus `employees`.
- Nach dem Deployment müssen sich alle einmal neu anmelden, weil alte Cookies
  keine Version enthalten.
- Der Seed überschreibt die Version nicht (Test
  `tests/integration/test_auth.py`).
