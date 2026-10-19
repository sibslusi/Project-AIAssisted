# UC-002: Schulung steuern

## Intent

Die Datenschutzverantwortliche weist Schulungsmodule mit Fristen zu und kann
nachvollziehen, welche Mitarbeitenden geschult sind. Abteilungsleitungen sehen
nur die zulässigen Informationen ihrer eigenen Abteilung.

## Actors

**Primary**  
Datenschutzverantwortliche

**Secondary**  
Abteilungsleitung, Mitarbeitende, Anwendung

## Preconditions

- Die Datenschutzverantwortliche ist angemeldet und ihrer hinterlegten
  `@grenchen.ch`-Adresse zugeordnet.
- Module und veröffentlichte, aktive Datenschutzfälle existieren.
- Mitarbeitende gehören jeweils genau einer Abteilung an.
- Für jede Zuweisung sind Modul, Zielabteilung und Frist festgelegt.
- Der aktuelle Zeitpunkt wird über einen Clock-Port oder als Parameter an die
  Statuslogik übergeben.

## Flow

1. Die Datenschutzverantwortliche öffnet die Modulverwaltung.
2. Sie wählt ein Modul, eine Abteilung und eine Frist aus.
3. Die Anwendung prüft die Eingaben und speichert eine `Assignment`.
4. Die zugewiesenen Mitarbeitenden sehen das Modul und ihren persönlichen
   Schulungsstatus.
5. Die Anwendung berechnet den Status anhand des besten abgeschlossenen
  Versuchs und der Frist: `offen`, `erledigt`, `verspätet erledigt` oder
  `Frist überschritten`.
6. Die Datenschutzverantwortliche sieht den Status und aggregierte Ergebnisse
   aller Abteilungen.
7. Die Abteilungsleitung sieht nur den Status pro Person der eigenen Abteilung.
   Punkte und Fehler werden nur als Teamwerte aggregiert angezeigt.
8. Teamwerte werden erst ab mindestens drei Personen angezeigt.
9. Ausschliesslich die Datenschutzverantwortliche kann einen Schulungsnachweis
  als CSV mit Person, Modul und Abschlusszeitpunkt exportieren.

## Errors

- Nicht angemeldet: Zugriff auf Zuweisungen und Auswertungen wird verweigert.
- Falsche Rolle: Mitarbeitende und Abteilungsleitungen dürfen keine Module
  zuweisen. Eine Abteilungsleitung erhält beim CSV-Export HTTP 403.
- Fremde Abteilung: Eine Abteilungsleitung kann keine Status- oder
  Detailauswertung einer anderen Abteilung abrufen.
- Ungültige Eingabe: Ein fehlendes Modul, eine fehlende Abteilung oder eine
  ungültige beziehungsweise fehlende Frist wird abgelehnt.
- Nicht gefunden: Ein unbekanntes Modul oder eine unbekannte Abteilung führt zu
  einer kontrollierten Fehlermeldung.
- Zu kleine Gruppe: Teamwerte werden bei weniger als drei Personen nicht
  angezeigt; stattdessen erscheint `zu wenige Teilnehmende`.
- Fehlender Schulungsnachweis: Ein CSV-Export ohne gültige Zuweisung wird
  abgelehnt.

## Acceptance

### AC-001: Modul zuweisen

**Given** eine angemeldete Datenschutzverantwortliche und ein gültiges Modul  
**When** sie das Modul einer Abteilung mit einer gültigen Frist zuweist  
**Then** speichert die Anwendung eine `Assignment` mit Modul, Abteilung und
Frist.

### AC-002: Zuweisung validieren

**Given** eine neue Zuweisung  
**When** Modul, Abteilung oder Frist fehlt oder ungültig ist  
**Then** weist die Anwendung die Zuweisung ab und speichert sie nicht.

### AC-003: Status offen

**Given** eine gültige Zuweisung ohne bestandenen Versuch und eine noch nicht
abgelaufene Frist  
**When** der Schulungsstatus berechnet wird  
**Then** lautet der Status `offen`.

### AC-004: Status erledigt

**Given** eine gültige Zuweisung mit einem bestandenen Versuch  
**When** der Schulungsstatus berechnet wird  
**Then** lautet der Status `erledigt`.

### AC-005: Status Frist überschritten

**Given** eine gültige Zuweisung ohne bestandenen Versuch, unabhängig davon, ob
eine Runde gestartet wurde, und eine abgelaufene Frist  
**When** der Schulungsstatus mit dem aktuellen Zeitpunkt berechnet wird  
**Then** lautet der Status `Frist überschritten`.

### AC-006: Status verspätet erledigt

**Given** eine gültige Zuweisung mit einem bestandenen Versuch nach Ablauf der
Frist  
**When** der Schulungsstatus berechnet wird  
**Then** lautet der Status `verspätet erledigt`.

### AC-007: Eigenen Status anzeigen

**Given** eine angemeldete Mitarbeitende mit einer Zuweisung  
**When** sie ihren Schulungsstatus abfragt  
**Then** sieht sie nur ihren eigenen Status und ihre eigenen Ergebnisse.

### AC-008: Abteilungsstatus anzeigen

**Given** eine angemeldete Abteilungsleitung  
**When** sie die Schulungsstatus ihrer Abteilung abfragt  
**Then** sieht sie pro Person nur den Status `erledigt`, `offen`, `verspätet
erledigt` oder `Frist überschritten`.

### AC-009: Fremde Abteilung schützen

**Given** eine Abteilungsleitung aus Abteilung A  
**When** sie eine Auswertung für Abteilung B anfordert  
**Then** verweigert die Anwendung den Zugriff.

### AC-010: Teamwerte ab drei Personen

**Given** eine Abteilungsleitung und mindestens drei Personen in ihrer Abteilung  
**When** sie die Team-Auswertung abfragt  
**Then** sieht sie aggregierte Punkte und Fehler der Abteilung, aber keine
individuellen Punkte oder Fehler.

### AC-011: Teamwerte unter drei Personen schützen

**Given** eine Abteilungsleitung und weniger als drei Personen mit einer
Zuweisung  
**When** sie die Team-Auswertung abfragt  
**Then** zeigt die Anwendung keine Teamwerte und den Hinweis `zu wenige
Teilnehmende`.

### AC-012: Vollständige Auswertung

**Given** eine angemeldete Datenschutzverantwortliche  
**When** sie die Schulungsauswertung öffnet  
**Then** sieht sie die zulässige Auswertung aller Abteilungen.

### AC-013: CSV exportieren

**Given** eine angemeldete Datenschutzverantwortliche und eine gültige
Zuweisung  
**When** sie den Schulungsnachweis exportiert  
**Then** erhält sie eine CSV-Datei mit Person, Modul und Abschlusszeitpunkt.

### AC-014: CSV-Export für Abteilungsleitung verweigern

**Given** eine angemeldete Abteilungsleitung  
**When** sie den Schulungsnachweis als CSV exportieren möchte  
**Then** verweigert die Anwendung den Zugriff mit HTTP 403.

### AC-015: Aktuellen Zeitpunkt verwenden

**Given** eine Zuweisung ohne bestandenen Versuch  
**When** der Status mit einem übergebenen Zeitpunkt vor oder nach der Frist
berechnet wird  
**Then** ist das Ergebnis entsprechend `offen`, `erledigt`, `verspätet
erledigt` oder `Frist überschritten`, ohne die Systemzeit direkt in Domain oder
Application aufzurufen.

## Tests

- **Unit:** Zuweisungsvalidierung; Status `offen`, `erledigt`, `verspätet
  erledigt` und `Frist überschritten`, auch ohne gestartete Runde; Clock-Port;
  bester Versuch; Rollen- und
  Abteilungszugriffsregeln; Mindestgruppengrösse von drei Personen;
  Aggregation ohne individuelle Punkte oder Fehler; CSV-Datensätze; Verbot des
  CSV-Exports für Abteilungsleitungen.
- **Integration:** Zuweisung über den FastAPI-TestClient; Persistenz von
  `Assignment`; Statusabfrage für Mitarbeitende und Abteilungsleitung;
  Schutz fremder Abteilungen; Teamwerte ab drei Personen; vollständige
  Datenschutzverantwortlichen-Auswertung; CSV-Export mit HTTP-403-Prüfung für
  Abteilungsleitungen.
- **E2E API:** Datenschutzverantwortliche weist ein Modul zu; Mitarbeitende
  sehen ihren Status; eine Abteilungsleitung sieht nur Statuswerte ihrer
  Abteilung; Teamwerte erscheinen ab drei Personen und nicht darunter; eine
  abgelaufene Zuweisung wird als `Frist überschritten` angezeigt; ein nach
  Frist bestandener Abschluss als `verspätet erledigt`; die
  Datenschutzverantwortliche exportiert den Schulungsnachweis als CSV und eine
  Abteilungsleitung erhält dafür HTTP 403.
- **Optional Playwright:** Browser-Ablauf für Modulzuweisung, Statusansicht
  und CSV-Export, falls die Zeit für Browser-Tests ausreicht.
