# Erkenntnisse pro Arbeitstag

Diese Datei ergänzt das [AI-LOG](AI-LOG.md). Im AI-LOG sind die einzelnen Aufträge an die KI-Agenten dokumentiert. Hier halte ich fest, was ich an den jeweiligen Tagen gelernt habe, wo Probleme aufgetreten sind und was ich beim nächsten Mal anders machen würde.

Die erste Zusammenfassung wurde am 26.10.2026 mit Unterstützung von Claude aus meinen AI-LOG-Einträgen erstellt. Die wichtigsten Erkenntnisse und das Fazit habe ich selbst ausgewählt und anschliessend überarbeitet.

## 2026-10-19

**Projektplanung und Vorbereitung**

An diesem Tag habe ich vor allem mit GitHub Copilot und Codex gearbeitet. Es ging darum, das Projekt zu planen, die Anforderungen festzulegen und die technische Grundlage vorzubereiten.

- **Eine genaue Planung macht die spätere Arbeit einfacher.** Ich habe mit Copilot zuerst das Problem, die Zielgruppe und die Funktionen der Anwendung Schritt für Schritt besprochen. Das hat ziemlich viel Zeit gebraucht. Im Nachhinein war es aber sinnvoll, weil die Anforderungen danach klarer waren und Codex auf dieser Grundlage weiterarbeiten konnte. Ich habe dadurch besser verstanden, was mit Spec-driven Development gemeint ist: Man beschreibt zuerst möglichst genau, was die Anwendung können soll, und beginnt erst danach mit dem Programmieren.
- **Die KI übernimmt manchmal mehr, als ich eigentlich verlangt habe.** Copilot hatte die ersten 30 Lernpunkte im AI-LOG selbst geschrieben, obwohl ich ihn nicht darum gebeten hatte. Mir wurde dadurch bewusst, dass ich einem Agenten nicht nur sagen muss, was er tun soll, sondern manchmal auch ausdrücklich, was er nicht tun darf. Eine entsprechende Regel hätte ich bereits zu Beginn in `AGENTS.md` festhalten können.
- **Paralleles Arbeiten ist nicht immer einfacher.** Ich habe mit zwei Worktrees gearbeitet, damit verschiedene Aufgaben getrennt bearbeitet werden konnten. Ein Worktree ist vereinfacht gesagt ein zusätzlicher Arbeitsordner für einen eigenen Git-Branch. Beim späteren Zusammenführen gab es jedoch Widersprüche, beispielsweise bei der Frage, welcher bestandene Versuch für den Schulungsstatus zählt. Diese Unstimmigkeiten wurden erst später entdeckt. Ich habe daraus gelernt, dass getrennt erstellte Ergebnisse am Schluss unbedingt miteinander verglichen werden müssen.
- **Dokumentierte Entscheidungen helfen bei der Zusammenarbeit mit KI.** Wir haben wichtige Architekturentscheidungen in sogenannten ADRs (Architecture Decision Records) festgehalten. Dadurch konnten die verschiedenen Agenten nachlesen, weshalb wir etwas so entschieden hatten. Ich fand das hilfreich, weil nicht in jeder neuen Sitzung wieder dieselben Fragen geklärt werden mussten.
- **Bei Git muss ich genauer aufpassen.** Beim Zusammenführen von Änderungen ging ein Eintrag im AI-LOG verloren. Mir war vorher nicht wirklich bewusst, dass bei einem Merge auch Teile einer Dokumentation verloren gehen können. Deshalb würde ich solche Dateien künftig nach einem Merge genauer kontrollieren.
- **KI-generierte Inhalte sind nicht automatisch richtig.** Bei den fiktiven Datenschutzfällen habe ich verlangt, dass unsichere Gesetzesartikel entsprechend gekennzeichnet werden. Gerade bei rechtlichen Themen möchte ich nicht einfach Angaben übernehmen, nur weil die KI sie überzeugend formuliert.

## 2026-10-21

**Programmieren, Tests und erste grössere Probleme**

An diesem Tag wurde vor allem an den beiden Use Cases gearbeitet. Codex übernahm viel von der Programmierung, während Claude bei Reviews und der Koordination unterstützte.

- **Bei technischen Fehlern sollte ich nicht einfach alles ausprobieren, was die KI vorschlägt.** Nach einem Neustart des Dev Containers funktionierte Codex nicht mehr. Es erschien der Fehler 401 Unauthorized. Verschiedene Lösungsvorschläge brachten uns zuerst nicht weiter. Erst durch gezielte Tests mit `curl`, also direkten Anfragen an die Schnittstelle, konnten die Ursachen gefunden werden. Ich habe gelernt, dass es besser ist, einen Fehler zuerst einzugrenzen, anstatt auf gut Glück Einstellungen zu ändern.
- **Grüne Tests bedeuten nicht unbedingt, dass alles richtig funktioniert.** Bei einem Quality Gate meldete der Agent, dass alle Prüfungen erfolgreich waren. Später fiel jedoch auf, dass fünf Tests nur kontrollierten, ob der Server mit HTTP 200 antwortete. Das bedeutet lediglich, dass die Anfrage erfolgreich verarbeitet wurde, aber nicht unbedingt, dass das richtige Ergebnis zurückkam. Seitdem ist mir klarer, dass nicht nur die Anzahl der Tests wichtig ist, sondern auch, was diese tatsächlich überprüfen.
- **Ein KI-Agent hält sich nicht immer an die gewünschte Architektur.** Bei einem Review wurde beispielsweise entdeckt, dass der Import-Linter umgangen worden war und sensible Konfigurationswerte im Code standen. Der Import-Linter ist ein Werkzeug, das überprüft, ob bestimmte Programmteile unerlaubt auf andere Schichten zugreifen. Ich habe daraus gelernt, dass ich mich nicht allein darauf verlassen kann, dass der Agent meine Vorgaben richtig umsetzt. Der generierte Code muss ebenfalls kontrolliert werden.
- **Mehrere Agenten gleichzeitig zu verwenden braucht Organisation.** Mit dem Befehl `pkill -f codex` wurden versehentlich alle laufenden Codex-Prozesse beendet. Ausserdem arbeiteten zwei Agenten zeitweise im gleichen Projektordner, wodurch sich Änderungen vermischten. Beim nächsten Mal würde ich von Anfang an jedem Agenten einen eigenen Arbeitsbereich geben und vorsichtiger mit Terminalbefehlen umgehen.
- **TDD wurde für mich verständlicher.** TDD bedeutet Test-driven Development. Dabei wird zuerst ein Test geschrieben, der fehlschlägt, und anschliessend der benötigte Code implementiert. Mit klaren Anweisungen an den Agenten liess sich diese Reihenfolge auch in den Git-Commits nachvollziehen. So konnte ich besser erkennen, ob tatsächlich zuerst getestet und danach programmiert wurde.
- **Testdaten sollten möglichst realistische Situationen abbilden.** Ein Fehler beim persönlichen Schulungsstatus wurde erst bei einem Test mit verschiedenen Benutzerrollen entdeckt. Die vorherigen Unit-Tests hatten nur eine Person pro Zuweisung berücksichtigt. Ich habe dadurch verstanden, dass auch viele bestandene Tests nicht unbedingt ausreichen, wenn wichtige Situationen gar nicht getestet werden.

## 2026-10-22

**Benutzeroberfläche, Git und CI/CD**

An diesem Tag habe ich mich stärker mit der Benutzeroberfläche, den Demo-Zugängen und der Veröffentlichung der Anwendung beschäftigt. Es gab mehrere Probleme, aus denen ich viel gelernt habe.

- **Auch mein eigener Prompt kann die Ursache eines Fehlers sein.** Obwohl alle automatisierten Tests bestanden waren, war die Seite zum Spielen einer Runde bei einer Fensterbreite unter 1024 Pixeln rechts abgeschnitten. Der Grund war eine feste Mindestbreite, die ich im vorherigen Prompt vorgegeben hatte. Der Agent hatte meine Anweisung also umgesetzt, aber das Ergebnis war trotzdem nicht sinnvoll. Das hat mir gezeigt, wie wichtig es ist, die Anwendung auch selbst im Browser auszuprobieren. Ausserdem sollte ich meine Anweisungen an die KI genauer überdenken.
- **Git war für mich eine der grössten Herausforderungen.** Ich arbeitete teilweise auf dem falschen Branch, wollte wechseln, obwohl noch Änderungen offen waren, oder es wurden Änderungen auf einen bereits zusammengeführten Branch gepusht. Oft brauchte ich Hilfe von Claude, um die Situation wieder zu bereinigen. Ich habe daraus gelernt, dass ich vor einem neuen Auftrag immer zuerst mit `git status` und `git branch --show-current` kontrollieren sollte, wo ich mich gerade befinde und ob noch Änderungen vorhanden sind.
- **Die Testumgebung sollte möglichst der späteren Anwendung entsprechen.** Beim Testen mit Docker und PostgreSQL wurden zwei Fehler gefunden, die bei den Tests mit SQLite nicht aufgefallen waren. SQLite ist eine einfachere Datenbank, die wir lokal verwendeten, während PostgreSQL für den produktiven Betrieb vorgesehen war. Für mich war das ein gutes Beispiel dafür, weshalb man nicht nur in einer vereinfachten Testumgebung prüfen sollte.
- **Wenn der Agent «fertig» sagt, muss das nicht stimmen.** Claude meldete, dass Phase 4 abgeschlossen sei. Auf meine Nachfrage wurde aber festgestellt, dass der Release-Workflow noch gar nicht ausgeführt worden war. Ein Release-Workflow ist ein automatisierter Ablauf, der eine Softwareversion baut und prüft. Für mich war das eine wichtige Erkenntnis: Ich sollte nicht nur fragen, ob etwas funktioniert, sondern auch, ob es tatsächlich getestet wurde und wo ich das Ergebnis sehen kann.
- **Manche Schritte bewusst selbst durchzuführen, ist sinnvoll.** Beispielsweise musste ich bestimmte Git-Tags und Freigaben selbst vornehmen, weil Claude dazu nicht berechtigt war. Das war zwar teilweise umständlich, aber ich finde es sinnvoll, wenn die endgültige Veröffentlichung einer Anwendung nicht einfach ohne meine Kontrolle passiert.

## 2026-10-25

**Dokumentation, MCP und Überprüfung**

An diesem Tag ging es hauptsächlich darum, die Dokumentation zu verbessern, MCP auszuprobieren und das ganze Projekt noch einmal genauer kontrollieren zu lassen.

- **Die KI kann auch in der Dokumentation Fehler machen.** In der ersten Version der README standen Funktionen, die unsere Anwendung gar nicht hatte. Die README ist die wichtigste Projektbeschreibung auf GitHub. Ich hatte zuerst nicht erwartet, dass ein Agent solche Funktionen einfach als vorhanden beschreibt. Deshalb habe ich gelernt, dass ich auch Dokumentation nicht ungeprüft übernehmen darf, sondern mit der tatsächlichen Anwendung vergleichen muss.
- **Durch MCP habe ich den Unterschied zwischen einer Antwort und einer überprüfbaren Antwort besser verstanden.** MCP steht für Model Context Protocol. Damit kann ein KI-Agent zusätzliche Werkzeuge verwenden. In meinem Versuch nutzte ich Context7, um auf Dokumentationen von Python-Bibliotheken zuzugreifen. Ohne MCP gab das Modell eine Quelle an, die es lediglich aus meiner Frage übernommen hatte. Mit Context7 wurde die Dokumentation tatsächlich abgefragt. Interessant fand ich, dass der generierte Code in beiden Fällen korrekt war, die Quellenangabe aber nur im zweiten Fall nachvollziehbar geprüft werden konnte.
- **Least Privilege ist auch bei KI-Werkzeugen wichtig.** Least Privilege bedeutet, dass ein Programm nur die Berechtigungen erhalten soll, die es wirklich benötigt. Für meinen MCP-Vergleich musste ich alle anderen Werkzeuge deaktivieren. Sonst hätte der Agent beispielsweise die Lösung aus unseren Projektdateien übernehmen oder die Dokumentation über das Terminal abrufen können. So habe ich verstanden, dass eingeschränkte Berechtigungen nicht nur für die Sicherheit wichtig sind, sondern auch für einen fairen Vergleich.
- **Ein zusätzliches Review hätte früher stattfinden sollen.** Bei der vollständigen Überprüfung des Repositories wurden noch mehrere Fehler und Widersprüche zwischen Spezifikationen, Architekturentscheiden und Code entdeckt. Obwohl wir schon sehr viele Tests hatten, waren also noch Probleme vorhanden. Rückblickend wäre es besser gewesen, solche umfassenden Reviews regelmässig durchzuführen, statt erst kurz vor der Abgabe.

## 2026-10-26

**Fehlerkorrekturen, Modellvergleich und Abschluss**

An diesem Tag ging es darum, die letzten gefundenen Fehler zu korrigieren, verschiedene KI-Modelle zu vergleichen und Phase 5 abzuschliessen.

- **TDD hat sich auch beim Beheben von Fehlern bewährt.** Zuerst wurden Tests geschrieben, die den jeweiligen Fehler zeigten, und danach wurde der Code korrigiert. Bei einigen E2E-Tests gab es allerdings Probleme, weil diese mit der tatsächlichen Systemzeit arbeiteten. E2E-Tests überprüfen einen vollständigen Anwendungsablauf. Durch den bereits vorgesehenen ClockPort, also eine austauschbare Uhr, konnten wir eine feste Zeit für die Tests verwenden. Dadurch wurden sie zuverlässiger.
- **Ein grösseres oder aufwendigeres KI-Modell liefert nicht automatisch bessere Ergebnisse.** Beim Modellvergleich schnitt das kleine Open-Weight-Modell schlecht ab. Aber auch das stärkere Modell mit mehr Rechenaufwand übersah einen wichtigen Fehler beim Logout. Die günstigere Einstellung mit weniger Rechenaufwand war in diesem Versuch deutlich schneller und günstiger, ohne wesentlich schlechter abzuschneiden. Für mich zeigt das, dass man Modelle nicht einfach anhand ihrer Grösse oder ihres Rechenaufwands beurteilen sollte.
- **Nicht nur das Modell, sondern auch das verwendete Werkzeug beeinflusst die Antworten.** Bei Copilot wurde ein eingefügter Prompt plötzlich als Befehl interpretiert. Ausserdem wurden automatisch geöffnete Dateien als Kontext hinzugefügt, obwohl das für den Vergleich nicht vorgesehen war. Das hat mir gezeigt, dass man bei einem Modellvergleich auch die Einstellungen und das Verhalten des Werkzeugs berücksichtigen muss.
- **Wichtige Entscheidungen möchte ich selbst treffen.** Beim Abschluss von Phase 5 und bei ADR-007 wurden mir verschiedene Möglichkeiten erklärt. Die endgültige Entscheidung habe ich selbst getroffen. Ich finde es sinnvoll, die KI für Vorschläge und Erklärungen zu verwenden, aber Architekturentscheide und Freigaben nicht vollständig ihr zu überlassen.
- **Die Reflexion pro Arbeitstag ist für mich übersichtlicher.** Im AI-LOG stehen viele einzelne Aufträge, bei denen sich die Lernpunkte teilweise wiederholen. Wenn ich meine Erkenntnisse pro Tag zusammenfasse, erkenne ich besser, welche Schwierigkeiten häufiger aufgetreten sind und was ich daraus mitgenommen habe.

## 2026-10-28

**Letzter Abgleich vor der Abgabe**

Am Tag vor der Abgabe habe ich die gesamte Dokumentation noch einmal mit dem tatsächlichen Code vergleichen lassen: README, PROJECT.md, Spezifikationen, ADRs, TASKS.md und AGENTS.md.

- **Die Frage «Ist alles vorhanden?» reicht nicht.** Ich hatte in den letzten Tagen mehrmals nachgefragt, ob alles vollständig ist und zusammenpasst. Trotzdem wurden beim letzten Abgleich noch Lücken gefunden. In UC-002 stand zum Beispiel, dass die Datenschutzverantwortliche aggregierte Ergebnisse aller Abteilungen sieht. Im Code gibt es nur den Status pro Person. In ADR-003 war beschrieben, wie ein Szenario ersetzt wird, obwohl es dafür keinen Code gibt. Im README stand «35 E2E-Tests», obwohl es inzwischen 37 waren, und TASKS.md verwies auf eine UC-003-Spezifikation, die nie erstellt wurde. Ich habe daraus gelernt, dass eine allgemeine Ja-Nein-Frage zu einer allgemeinen, meist zu optimistischen Antwort führt. Besser ist ein konkreter Auftrag: jede Aussage in der Dokumentation mit einer Datei oder einer Codezeile belegen.
- **Dokumentation veraltet still.** Die meisten Widersprüche waren am Anfang keine Fehler. Die Spezifikationen wurden in Phase 1 und 2 geschrieben, und der Code hat sich danach weiterentwickelt, zum Beispiel durch Reviews, Korrekturen und neue Tests. Die Beschreibung wurde dabei nicht immer mitgeändert. Beim nächsten Projekt würde ich darauf achten, dass ein Pull Request, der den Code ändert, auch die betroffenen Specs und ADRs anpasst und nicht erst ein späterer Abgleich.
- **Lieber streichen als etwas versprechen, das nicht existiert.** Ich habe entschieden, die nicht umgesetzten Punkte aus der Dokumentation zu entfernen oder ausdrücklich als «in V1 nicht umgesetzt» zu kennzeichnen, statt sie kurz vor der Abgabe noch schnell zu programmieren. Für die Bewertung ist wichtig, dass Beschreibung und Code übereinstimmen. Eine kleinere, aber ehrlich beschriebene Anwendung ist mir lieber als eine Dokumentation, die mehr verspricht, als die Anwendung kann.
- **Auch eine KI-Prüfung prüft nur, was sie sieht.** Copilot hat bei einem Review einen Fehler gemeldet, der bereits behoben war, weil im Prompt noch ein alter Codeausschnitt stand. Eine andere KI hat mein Projekt nur anhand der Dokumentation beurteilt und konnte deshalb nicht sagen, ob es wirklich fünf Entitäten im Code gibt. Das hat mir gezeigt, dass ich immer wissen muss, auf welchem Stand eine Prüfung gemacht wurde. Belastbar ist ein Befund erst, wenn er gegen den aktuellen Code geprüft ist, zum Beispiel mit Dateipfad, Commit oder Testlauf.
- **Begriffe müssen klar sein, bevor man zählt.** Bei der Frage nach der Anzahl Entitäten kamen je nach Zählweise 5, 7 oder 8 heraus: 5 Klassen in der Domain-Schicht, 7 Entitäten mit eigener Tabelle und 8 im logischen Modell mit `AnswerOption`. Erst als klar war, was gezählt wird, passten README und Code zusammen. Ich habe gelernt, dass ich bei solchen Nachweisen die Definition dazuschreiben muss.
- **Einfach vor vollständig** *(Vorschlag von Claude, von Sibslusi zu prüfen)*. Ich war unsicher, ob auf der Live-Instanz andere Logins gelten als lokal. Die Prüfung im Code ergab: dieselben Konten aus demselben Seed, nur das Passwort kommt aus `DEMO_PASSWORD`, und Gross- und Kleinschreibung der E-Mail spielt keine Rolle. Die erste Antwort darauf war eine genaue Tabelle mit Live und Lokal, die aber mehr verwirrt als geholfen hat. Ich habe daraus gelernt, dass Anleitungen für andere einheitlich und knapp sein müssen: eine Angabe, die überall gilt, und Sonderfälle nur als kurzer Hinweis.

## Gesamtfazit

### Meine fünf wichtigsten Erkenntnisse

**1. Das Template hat mir geholfen, strukturiert zu arbeiten.**

Am Anfang war mir nicht richtig klar, weshalb wir so viele Dateien wie `AGENTS.md`, `TASKS.md` und die verschiedenen Skills brauchen. Im Verlauf des Projekts habe ich verstanden, dass diese Dateien den KI-Agenten eine gemeinsame Arbeitsgrundlage geben. Das Template lieferte nicht die fertige Anwendung, sondern einen Ablauf, an dem wir uns orientieren konnten.

**2. Erfolgreiche Tests bedeuten nicht automatisch, dass die Anwendung fehlerfrei ist.**

Ich habe am Anfang stark darauf geachtet, ob die Tests grün waren. Erst durch die verschiedenen Reviews und meine eigenen Tests im Browser wurde mir bewusst, dass dabei trotzdem wichtige Fehler übersehen werden können. Heute würde ich genauer überprüfen, was die Tests tatsächlich kontrollieren.

**3. Die Arbeit mit mehreren KI-Agenten muss gut organisiert sein.**

Ich dachte zuerst, dass mehrere Agenten die Arbeit vor allem schneller machen würden. Teilweise war aber das Gegenteil der Fall, weil Änderungen in falschen Ordnern oder Branches landeten. Getrennte Worktrees und klare Aufgaben sind deshalb wichtig. Auch das Zusammenführen der Ergebnisse darf nicht vergessen werden.

**4. Git war meine grösste praktische Lernkurve.**

Viele der Schwierigkeiten im Projekt entstanden nicht beim eigentlichen Programmieren, sondern beim Umgang mit Branches, Worktrees, Commits und Merges. Oft musste ich mir die nächsten Schritte erklären lassen. Ich habe Git dadurch besser kennengelernt, merke aber auch, dass ich in diesem Bereich noch Übung brauche.

**5. Die KI kann viel Arbeit übernehmen, aber ich muss die Ergebnisse trotzdem verstehen und kontrollieren.**

Im Projekt wurde ein grosser Teil des Codes von KI-Agenten erstellt. Für mich war es deshalb besonders wichtig, die Entscheidungen, Tests und Ergebnisse nachzuvollziehen. Ich habe gemerkt, dass die KI durchaus Fehler machen oder Aufgaben als abgeschlossen melden kann, obwohl noch etwas fehlt. Am Schluss bin ich selbst dafür verantwortlich, was ich als fertiges Ergebnis akzeptiere.

### Drei Situationen, aus denen ich besonders viel gelernt habe

| Situation | Was ich daraus gelernt habe |
|---|---|
| 21.10.: Bei UC-002 waren Tests grün, obwohl sie teilweise nur HTTP 200 überprüften. | Ein Test muss nicht nur erfolgreich sein, sondern auch das richtige Verhalten prüfen. |
| 22.10.: Die Benutzeroberfläche war unter 1024 Pixeln abgeschnitten. | Ich muss die Anwendung auch selbst ausprobieren und darf mich nicht ausschliesslich auf automatisierte Tests verlassen. |
| 22.10.: Claude meldete Phase 4 als abgeschlossen, obwohl der Release-Workflow noch nicht gelaufen war. | Ich sollte bei Erfolgsmeldungen nach konkreten Nachweisen fragen und überprüfen, ob die Schritte wirklich ausgeführt wurden. |

### Persönliches Fazit

Vor diesem Projekt hatte ich noch wenig Erfahrung damit, eine vollständige Anwendung mit mehreren KI-Agenten zu entwickeln. Viele Begriffe und Abläufe, beispielsweise Worktrees, TDD, Quality Gates oder CI/CD, waren für mich neu oder zumindest noch nicht wirklich verständlich.

Durch die praktische Arbeit habe ich besser verstanden, wie diese Dinge zusammenhängen. Gleichzeitig war die Arbeit nicht immer einfach. Besonders Git hat mich teilweise viel Zeit gekostet, und ich war häufig auf Erklärungen und Unterstützung durch die KI angewiesen.

Am meisten überrascht hat mich, dass auch eine grosse Anzahl erfolgreicher Tests und ein scheinbar abgeschlossenes Quality Gate nicht garantieren, dass alles richtig funktioniert. Einige Fehler wurden erst entdeckt, weil ich nachgefragt, ein zusätzliches Review verlangt oder die Anwendung selbst ausprobiert habe.

Für zukünftige Projekte würde ich die Arbeit mit den Agenten von Anfang an besser organisieren, regelmässiger Reviews durchführen und mehr darauf achten, dass ich die Ergebnisse wirklich nachvollziehen kann.

Meine wichtigste Erkenntnis ist, dass KI die Softwareentwicklung stark erleichtern kann, ich aber trotzdem selbst mitdenken und Verantwortung übernehmen muss. Für mich geht es deshalb nicht nur darum, mit KI möglichst schnell eine funktionierende Anwendung zu erstellen, sondern auch darum, zu verstehen, wie sie entstanden ist und weshalb sie funktioniert.
