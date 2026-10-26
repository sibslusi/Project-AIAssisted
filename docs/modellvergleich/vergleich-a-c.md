# Vergleich Lauf A (Extra High) und Lauf C (Low): gpt-5.6-luna

Analyse durch Claude Code (Cloud-Thread), 26.10.2026, gegen den echten Code auf `main` `27e63a4`
geprüft. Die Punktevergabe macht Sibslusi; diese Datei liefert nur die geprüften Fakten.

## Kennzahlen

| | Lauf A: Extra High | Lauf C: Low |
|---|---|---|
| Zeit | 2 min 48 s | 28 s |
| Kosten | 0.0289 USD | 0.0043 USD |
| Befunde | 5 | 5 |
| Wichtigster Befund laut Modell | veraltete Rolle im Cookie (Z1) | vergangene Frist (B3) |

## Befunde gegen den Lösungsschlüssel

| Befund | Lauf A | Lauf C |
|---|---|---|
| **B2** Logout macht Session nicht ungültig (kopiertes Cookie gilt weiter) | nicht gefunden | nicht gefunden |
| **B3** vergangene Frist wird akzeptiert | gefunden (F-03), als „unsicher“ markiert | gefunden (Befund 1), Schweregrad mittel |
| Z1 Rolle/Abteilung im Cookie veraltet (gleiche Ursache wie B2) | gefunden, als wichtigster Befund | gefunden, als „unsicher“ markiert |
| Z2 CSRF-Vergleich mit `!=` | gefunden | gefunden |
| 500 statt 401 bei ungültiger signierter Payload | gefunden | gefunden |
| weitere | ID-Typen nicht validiert (F-04), plausibel | doppelte Zuweisungen, selbst als „unsicher“ markiert |
| Falschbefunde | keine | keine |

Beide Läufe finden dieselben Kernpunkte. Keiner nennt B2 direkt: Beide sehen, dass das Cookie
8 h gültig bleibt, verbinden das aber nur mit Rollenänderungen, nicht mit dem Logout.

## Qualität der Fixes

| | Lauf A: Extra High | Lauf C: Low |
|---|---|---|
| Fix Session | Port `SessionCodec` + `CurrentActorRepository` + Use Case `ResolveSessionActor`, Adapter in Infrastructure. Sauber nach Clean Architecture, aber grösserer Umbau. Löst Z1, **nicht** B2 (nach Logout bleibt die ID im Cookie gültig). | Nur defensives `_actor` (alle Parse-Fehler → `None`). Klein und passend, löst aber nur den 500-Befund, weder Z1 noch B2. |
| Fix Frist (B3) | Nutzt `ClockPort.now()` mit `astimezone(Europe/Zurich)`. **Passt zum echten Port** (`ClockPort` hat `now()`). | Nimmt einen `ClockPort.today()` an, den es im Projekt nicht gibt. Domain-Methode `Assignment.create(today=…)` ist ein guter Entwurf. |
| Lauffähigkeit der Tests | Beide Tests importieren `Actor`/`Role` aus `app.domain.models` (liegen in `app.application.models`), Test 2 zusätzlich `app.application.errors` (gibt es nicht). Test 1 setzt die Rolle als `"DATA_PROTECTION_OFFICER"`, der echte Wert ist `"data_protection_officer"`. | Test 1 importiert ebenfalls `app.application.errors` und `Role` aus `app.domain.models`. Test 2 (defensives `_actor`) importiert nur `app.interfaces.http` und wäre vermutlich ohne Änderung lauffähig. |

## Einschätzung

- **Gleiche Befunde, 6× schneller, knapp 7× günstiger:** Für das Finden der Fehler bringt Extra High
  hier keinen Vorteil.
- **Extra High ist beim Fix genauer:** Es hat die echte Schnittstelle (`now()`) getroffen und
  einen architektonisch vollständigen Umbau vorgeschlagen. Low rät eine Schnittstelle.
- **Beide erfinden Importpfade.** Ohne Blick in den Code (nur Ausschnitt) sind die Tests bei
  beiden nicht direkt übernehmbar; ein Mensch oder ein Agent mit Repo-Zugriff muss nacharbeiten.
- **Beide verpassen B2.** Ein Logout-spezifischer Hinweis im Prompt hätte das vermutlich geändert,
  hätte den Vergleich aber verfälscht.
