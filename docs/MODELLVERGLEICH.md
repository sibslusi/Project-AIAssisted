# Modellvergleich: Code-Review mit mehreren Modellen (SW3)

SW3-Aufgabe: „give the same small capstone task to two different models (e.g. a frontier model and
an open-weight model) – Quality of the result? Time? Cost (see spend in LiteLLM)?“

Aufgabe hier: derselbe Code-Review-Prompt mit demselben Code an mehrere Modelle. Ziel ist, die
Modellwahl mit Beleg statt Bauchgefühl zu begründen.

## Versuchsaufbau

| Punkt | Festlegung |
|---|---|
| Werkzeug | VS Code, GitHub Copilot Chat (Local), Modus **Ask**, Standardwerkzeuge von Ask unverändert |
| Lauf A | `gpt-5.6-luna` (Frontier), Denkstufe **Extra High** |
| Lauf B | `ibm/granite4.1:3b` (Open-Weight), keine Denkstufe wählbar |
| Lauf C | `gpt-5.6-luna`, Denkstufe **Low** (Einfluss der Denkstufe) |
| Prompt | [modellvergleich/prompt.md](modellvergleich/prompt.md), als Ganzes eingefügt, plus die Zeile `Führe den Code-Review aus dem angehängten Text aus. Antworte direkt, ohne /fix oder /tests.` |
| Code | `main` Commit `27e63a4` (= Release v0.1.1): Logout/Session-Handling in `src/app/interfaces/http.py`, Fristlogik in `AssignModule` und `Assignment` |
| Kontext | Pro Lauf ein neuer Chat, keine angehängte Datei (Kontext-Chip entfernt) |
| Zeit | Anzeige „Completed … in …“ in Copilot |
| Kosten | Spend des LiteLLM-Keys über `GET /key/info` (Funktion `spend` im Terminal), vor dem Lauf und **3 Minuten nach** dem Lauf, weil LiteLLM verzögert verbucht |

Warum kein Apertus: Apertus (Swiss AI) ist ohne Swiss-AI-Key nicht auswählbar, deshalb das offene
Modell Granite 4.1 aus dem LiteLLM.

## Bekannte Fehler im geprüften Code (Lösungsschlüssel)

- **B2:** Logout löscht nur die Cookies im Browser. Das signierte Session-Cookie bleibt bis
  8 h nach dem Login gültig, ein kopiertes Cookie funktioniert nach dem Abmelden weiter.
- **B3:** `AssignModule` akzeptiert Fristen in der Vergangenheit.

## Ergebnisse

### Lauf A: gpt-5.6-luna (Extra High)

![Lauf A: Ende der Antwort von gpt-5.6-luna (Extra High), Spend vor und nach dem Lauf im Terminal](images/modellvergleich-lauf-a.png)

| Messwert | Wert |
|---|---|
| Zeit | 2 min 48 s („Completed 2 steps in 2m 48s“) |
| Spend vorher / nachher | 5.582388570 / 5.611272170 USD |
| Kosten | **0.0289 USD** |
| Antwort | [antwort-lauf-a.md](modellvergleich/antwort-lauf-a.md) |
| Bewertung | folgt (Sibslusi) |

### Lauf B: ibm/granite4.1:3b

![Lauf B: granite4.1:3b bricht nach 300 s mit LiteLLM-Timeout ab, davor ein erfundener Fix zum date-Import](images/modellvergleich-lauf-b.png)

| Messwert | Wert |
|---|---|
| Zeit | Abbruch nach **300 s** (LiteLLM-Timeout `litellm-vscode-chat.chat.timeout`), Antwort unvollständig |
| Spend vorher / nachher | 5.611272170 / folgt |
| Kosten | folgt |
| Antwort | folgt |
| Bewertung | folgt (Sibslusi) |

Auffällig: „Fix 2“ behauptet, `from datetime import date` importiere einen falschen `date`-Typ, und
schlägt `from datetime import date as Date` vor. Das ist ein **Falschbefund**: Der Import ist korrekt,
der Fix ändert nichts. Der zugehörige Test ist leer.

### Lauf C: gpt-5.6-luna (Low)

![Lauf C: Anfang der Antwort mit Zeit und von Copilot automatisch verwendeten Referenzen](images/modellvergleich-lauf-c-antwort.png)

| Messwert | Wert |
|---|---|
| Zeit | 28 s („Completed 2 steps in 28s“) |
| Spend vorher / nachher | 5.578048570 / 5.582388570 USD |
| Kosten | **0.0043 USD** |
| Antwort | [antwort-lauf-c.md](modellvergleich/antwort-lauf-c.md) |
| Bewertung | folgt (Sibslusi) |

## Vergleich der beiden gpt-5.6-luna-Läufe

Geprüfte Gegenüberstellung von Lauf A und Lauf C: [modellvergleich/vergleich-a-c.md](modellvergleich/vergleich-a-c.md).

## Einschränkungen des Versuchs

- Copilot Ask hat standardmässig Lese- und Suchwerkzeuge für den Workspace aktiv. Die Modelle
  hätten also zusätzlich Dateien lesen können; die Werkzeuge sind für alle Läufe gleich.
- **Copilot hängt Projekt-Instruktionen automatisch an.** Laut „Used 3 references“ las Copilot
  `.github/copilot-instructions.md`, `AGENTS.md` und die Einstellung
  `github.copilot.chat.codeGeneration.instructions` mit. Der Input war also nicht nur der Prompt,
  aber für alle Läufe gleich.
- Pro Modell ein Lauf; Ergebnisse können bei Wiederholung abweichen.
