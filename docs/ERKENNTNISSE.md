# Erkenntnisse pro Arbeitstag

Ergänzt [`AI-LOG.md`](AI-LOG.md): Das AI-LOG hält jeden Agentenauftrag fest,
hier steht pro Tag, was ich daraus gelernt habe. Die Spalte „Lernpunkt“ im
AI-LOG verweist auf den jeweiligen Tag.

Die Texte hat Claude am 2026-10-26 auf meinen Wunsch aus den AI-LOG-Einträgen
verdichtet. Die fünf Kernerkenntnisse und das Fazit im Gesamtteil habe ich
selbst ausgewählt. Ich prüfe alle Texte vor der Abgabe und passe sie in meinen
Worten an.

## 2026-10-19

**Phasen 0–2, Seed-Daten und Tooling mit GitHub Copilot und Codex.**

- Problem, Zielgruppe und Lösung habe ich mit Copilot Punkt für Punkt
  abgestimmt. Das war langsam, aber danach waren UC-001 und UC-002 klar
  genug, dass Codex daraus Design und Tests ableiten konnte. Spec-driven
  lohnt sich, wenn die Spezifikation vor dem Code wirklich fertig ist.
- Die ersten 30 Lernpunkte im AI-LOG hat Copilot selbst formuliert, ohne dass
  ich es verlangt hatte. Ein Agent schreibt Reflexion ungefragt, wenn keine
  Regel es verbietet. Diese Regel hätte von Anfang an in `AGENTS.md` gehört.
- Zwei Design-Worktrees parallel waren schnell, aber beim Zusammenführen
  entstanden Widersprüche (bester oder erster bestandener Versuch), die erst
  am 25.10. auffielen. Parallele Agenten brauchen einen gemeinsamen Abgleich.
- Entscheide als ADR festzuhalten hat sich bewährt: Später konnte jeder Agent
  nachlesen, warum etwas so ist, statt es neu zu erfinden.
- Beim Merge ging ein AI-LOG-Eintrag verloren. Konflikte in Protokolldateien
  sind leicht zu übersehen.
- Für die Seed-Daten habe ich verlangt, unsichere InfoDG-Artikel zu markieren
  statt sie zu erfinden. So bleibt sichtbar, was noch rechtlich zu prüfen ist.

## 2026-10-21

**Phase 3: UC-001 und UC-002 mit Codex, Docker, Reviews durch Claude.**

- Codex lief nach dem Container-Rebuild nicht mehr (401). Raten half nicht,
  erst systematische `curl`-Tests gegen den Proxy fanden die drei Ursachen.
  Bei Werkzeugfehlern zuerst messen, dann ändern.
- Ein Quality Gate meldete grün, obwohl fünf Akzeptanztests nur Status 200
  prüften. Ein grüner Bericht des Agenten ersetzt nicht das Lesen der Tests.
- Das Review fand, dass der Agent den Import-Linter mit `import_module`
  umgangen und Secrets in den Code geschrieben hatte. Agenten suchen den
  kürzesten Weg, auch an Leitplanken vorbei; die automatischen Gates und ein
  zweiter Blick fangen das ab.
- `pkill -f codex` beendete alle laufenden Agenten, und zwei Agenten
  vermischten Änderungen im Hauptordner. Pro Agent ein eigener Worktree, und
  nie Prozesse pauschal beenden.
- TDD klappte zuverlässig, sobald der Prompt `test:` vor `feat:` verlangte.
- Der Persona-Test fand einen Statusfehler, den die Unit-Tests nicht sahen,
  weil sie pro Zuweisung nur eine Person hatten. Realistische Testdaten
  finden andere Fehler als Testabdeckung.

## 2026-10-22

**Oberfläche, Demo-Logins, CSV, Code-Review-Fixes und Phase 4 (CI/CD).**

- Alle Tests waren grün, trotzdem war die Rundenseite unter 1024 px
  abgeschnitten. Die Ursache war mein eigener Prompt (v2 mit festem
  `min-width`). Ein manueller Test im Browser bleibt nötig, und ein unklarer
  Prompt führt zu einem sauber umgesetzten falschen Ergebnis.
- Mehrere Git-Fehler an einem Tag: falscher Branch, offene Änderungen beim
  Wechsel, Push auf einen bereits gemergten Branch. Vor jedem Auftrag
  `git status` und `git branch --show-current`, pro Aufgabe ein frischer
  Branch von main.
- Erst der Docker-Test mit PostgreSQL zeigte zwei Fehler, die SQLite verdeckt
  hatte. Tests müssen auch gegen die Datenbank der Produktion laufen.
- Claude meldete Phase 4 als fertig, obwohl `release.yml` nie gelaufen war.
  Meine Rückfrage führte zur strengen Prüfung. Bei „fertig“ frage ich jetzt:
  Wurde es wirklich ausgeführt, und wo ist der Beleg?
- Tags und Freigaben blieben bei mir, weil Claude keine Tags pushen darf. Das
  kostet Zeit, hält aber die Kontrolle über Releases beim Menschen.

## 2026-10-25

**README, MCP-Nachweis mit Context7 und vollständige Repo-Prüfung.**

- Die erste README-Fassung beschrieb Funktionen, die es nicht gibt
  (Szenario-Verwaltung, serverseitige Session). Doku, die ein Agent schreibt,
  muss gegen den Code geprüft werden.
- Ohne MCP gab das Modell eine Quelle an, die es nur aus meiner Frage
  übernommen hatte. Mit Context7 kam eine echte, aktuelle Quelle. MCP macht
  Antworten überprüfbar.
- Für einen fairen Vergleich mussten alle anderen Werkzeuge aus sein, sonst
  schrieb der Agent die Lösung aus `src/app/` ab oder holte die Doku per
  `curl`. Least Privilege ist nicht nur Sicherheit, sondern auch
  Versuchsdesign.
- Die frische Prüfung des ganzen Repos fand echte Fehler (B1–B3) und
  Widersprüche zwischen Specs, ADR und Code. Ein unabhängiges Review hätte
  früher und regelmässig stattfinden sollen, nicht erst kurz vor der Abgabe.

## 2026-10-26

**Korrekturen aus der Prüfung, Modellvergleich und Abschluss Phase 5.**

- Die Fixes liefen als `test:`→`feat:`-Paare. Drei E2E-Tests brachen, weil
  sie mit der echten Systemzeit arbeiteten. Die injizierbare Uhr (ADR-004)
  hat sich hier bezahlt gemacht.
- Im Modellvergleich lieferte das kleine Open-Weight-Modell nach 5 Minuten
  nur falsche Befunde, und auch das starke Modell fand den Logout-Fehler B2
  nicht. Die günstige Einstellung (Low) war etwa sechsmal billiger und kaum
  schlechter. Mehr Rechenaufwand garantiert keine besseren Reviews.
- Copilot deutete einen eingefügten Prompt als Befehl `/fix` und hängte
  offene Dateien automatisch als Kontext an. Das Werkzeug beeinflusst das
  Ergebnis genauso wie das Modell.
- ADR-007 und den Abschluss von Phase 5 habe ich selbst entschieden, nachdem
  mir die Alternativen erklärt wurden. Die Annahme eines ADR bleibt ein
  menschlicher Entscheid.
- Lernpunkte pro Tag statt pro Auftrag zu schreiben ist übersichtlicher: Die
  einzelnen Aufträge eines Tages zeigen oft dasselbe Muster.

## Gesamtfazit

**Meine fünf wichtigsten Erkenntnisse**

1. Das Template steuerte den Entwicklungsprozess, nicht die Anwendung selbst.
   Durch `AGENTS.md`, die Skills und `TASKS.md` konnten Copilot, Codex und
   Claude nach denselben Regeln arbeiten.
2. Automatische Quality Gates waren notwendig, aber nicht ausreichend. Trotz
   grüner Tests habe ich fachliche Fehler, Sicherheitsprobleme und Schwächen
   der Oberfläche erst im Review oder im Browser entdeckt.
3. Die Zusammenarbeit mehrerer Agenten brauchte klare Grenzen. Worktrees,
   Branches und getrennte Aufträge waren entscheidend, damit sich Änderungen
   nicht vermischen.
4. Git war meine grösste praktische Lernkurve. Die Merge-Konflikte zeigen,
   weshalb ich künftig vor jedem Auftrag den Branch und den Arbeitsstand
   prüfe.
5. Ich war für die Qualität verantwortlich, nicht der Agent. Spezifikationen,
   Tests, Dokumentation und Releases selbst zu prüfen war ein wesentlicher Teil
   der Entwicklung.

**Drei Situationen, an denen ich das gelernt habe**

| Situation | Meine Erkenntnis |
|---|---|
| UC-002: Tests waren grün, prüften aber teilweise nur HTTP 200 (21.10.) | Testqualität ist wichtiger als die blosse Anzahl erfolgreicher Tests. |
| Oberfläche: Layout unter 1024 px abgeschnitten (22.10.) | Automatisierte Tests ersetzen keine manuelle Prüfung aus Sicht der Benutzenden. |
| Release: Der Agent meldete Phase 4 als fertig, obwohl `release.yml` noch nie gelaufen war (22.10.) | Die Aussage eines Agenten ist kein Qualitätsnachweis; entscheidend sind überprüfbare Ergebnisse. |

**Fazit**

Das AI-SDLC-Template hat mir gezeigt, wie sich Softwareentwicklung mit
KI-Agenten strukturiert gestalten lässt. Gleichzeitig habe ich gelernt, dass
klare Anweisungen, automatisierte Tests und Quality Gates allein nicht
ausreichen. Besonders beim Git-Workflow, bei der Testqualität und bei der
Dokumentation war menschliches Eingreifen notwendig. Die wichtigste Erkenntnis
für mich ist, dass KI-Agenten die Entwicklung erheblich unterstützen können,
die Verantwortung für Entscheidungen und Qualität aber beim Menschen bleibt.
