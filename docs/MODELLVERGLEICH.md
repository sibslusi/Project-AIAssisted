# Modellvergleich: Code-Review mit zwei Modellen (SW3)

Gleicher Review-Prompt, gleicher Code, zwei Modelle. Ziel: Modellwahl mit Beleg statt Bauchgefühl
begründen (Qualität, Zeit, Kosten).

## Einstellungen (Stand 26.10.2026)

![Einstellungen: Copilot Chat im Modus Ask mit gpt-5.6-luna und High, LiteLLM-Spend vor Lauf A im Terminal](images/modellvergleich-1-einstellungen.png)

| Punkt | Festlegung |
|---|---|
| Werkzeug | VS Code, GitHub Copilot Chat, Modus **Ask** (liest nur, ändert keine Dateien) |
| Modell A | `gpt-5.6-luna` über LiteLLM (`litellm.engines.aisl.science`), Denkstufe **High** |
| Modell B | folgt (gleiche Denkstufe wie Modell A) |
| Kontext | Kein `#codebase`, keine angehängte Datei, keine MCP-Werkzeuge; nur der Prompt mit eingefügtem Code |
| Chat | Für jedes Modell ein neuer Chat |
| Code | `main` Commit `27e63a4` (= Release v0.1.1): Logout/Session-Handling in `src/app/interfaces/http.py`, Fristlogik in `AssignModule` und `Assignment` |
| Zeit | Stoppuhr ab Abschicken bis Antwort fertig |
| Kosten | Spend des LiteLLM-Keys vor und nach jedem Lauf über `GET /key/info` (Terminal, Funktion `spend`); das Dashboard zeigt nur 2 Nachkommastellen |

Spend vor Lauf A: **5.542206720 USD** (Terminal im Screenshot, Key-Anfang geschwärzt).

## Bekannte Fehler im geprüften Code (Lösungsschlüssel)

- **B2:** Logout löscht nur die Cookies im Browser. Das signierte Session-Cookie bleibt bis
  8 h nach dem Login gültig, ein kopiertes Cookie funktioniert nach dem Abmelden weiter.
- **B3:** `AssignModule` akzeptiert Fristen in der Vergangenheit.

## Ergebnisse

Folgt nach den beiden Läufen.
