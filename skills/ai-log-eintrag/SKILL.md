---
name: ai-log-eintrag
description: Nach jeder abgeschlossenen Aufgabe genau einen Eintrag in docs/AI-LOG.md ergänzen (Phase, Agent + Modell, Prompt, Ergebnis, menschliche Korrektur).
---

# AI-LOG-Eintrag

## Wann

Nach jeder abgeschlossenen Aufgabe, vor dem Commit. Das gilt auch, wenn die
Aufgabe abgebrochen oder verworfen wurde.

## Schritte

1. Lies `docs/AI-LOG.md` und übernimm das bestehende Tabellenformat exakt.
2. Ergänze am Ende genau eine Zeile. Bestehende Einträge dürfen nicht geändert
   oder gelöscht werden.
3. Fülle die Felder so aus:
   - **Datum:** `JJJJ-MM-TT`.
   - **Phase / UC:** zum Beispiel `Phase 2 / UC-001`.
   - **Agent + Modell:** Werkzeug und konkretes Modell, zum Beispiel
     `Codex CLI + azure_ai/gpt-6-luna (LiteLLM)` oder
     `Copilot Chat + <Modellname>`. Schreibe niemals `unbekannt`. Wenn das
     Modell unklar ist, frage die Person vor dem Eintrag.
   - **Aufgabe:** ein Satz.
   - **Prompt:** Kern des Prompts, gekürzt auf höchstens zwei Sätze. Wenn die
     bestehende Tabelle keine eigene Prompt-Spalte besitzt, integriere den
     gekürzten Prompt in das bestehende Aufgabenfeld, ohne die Tabelle
     umzustrukturieren.
   - **Ergebnis:** erstellte oder geänderte Dateien.
   - **Menschliche Korrektur:** was die Person korrigiert, verworfen oder
     entschieden hat. Schreibe `keine`, wenn nichts korrigiert wurde.
   - **Lernerkenntnis:** Verweis auf den Tagestext, zum Beispiel
     `Siehe [Erkenntnisse 2026-10-26](ERKENNTNISSE.md#2026-10-26)`.
     Die Erkenntnis selbst steht pro Tag in `docs/ERKENNTNISSE.md` und wird
     von Sibslusi formuliert oder geprüft. Fehlt der Tag dort, lege die
     Überschrift `## JJJJ-MM-TT` an und frage Sibslusi nach dem Text.
4. Zeige der Person den neuen Eintrag, bevor du committen lässt oder selbst
   committen darfst.

## Regeln

- Keine Secrets, API-Keys, Passwörter oder Personendaten in den Log schreiben.
- Keine Angaben erfinden. Was nicht sicher ist, als `unklar` markieren; beim
  Modell gilt stattdessen die Pflicht zur Rückfrage.
- Pro Aufgabe genau ein Eintrag, auch wenn mehrere Dateien betroffen sind.
- Bestehende Einträge nie nachträglich ändern oder löschen, ausser Sibslusi
  verlangt es ausdrücklich; dann im neuen Eintrag festhalten, was geändert wurde.
