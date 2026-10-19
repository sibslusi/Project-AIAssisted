# UC-001: Szenario-Runde spielen

## Intent

Mitarbeitende der Gemeinde Grenchen trainieren Datenschutzsituationen aus ihrer
Abteilung und erhalten einen nachvollziehbaren Schulungsstatus.

## Actors

**Primary**  
Angemeldete Mitarbeitende der Gemeinde Grenchen

**Secondary**  
Abteilungsleitung, Datenschutzverantwortliche, Anwendung

## Preconditions

- Die Person ist angemeldet und einer Abteilung sowie einer Rolle zugeordnet.
- Die E-Mail-Adresse wurde bei der Registrierung als hinterlegte
  `@grenchen.ch`-Adresse erkannt.
- Der Person ist ein Modul ihrer eigenen Abteilung zugewiesen.
- Das Modul enthält fünf veröffentlichte Datenschutzfälle.
- Jeder Fall ist veröffentlicht und aktiv und besitzt drei bis vier
  Antwortmöglichkeiten, genau eine richtige Antwort, eine Erklärung und eine
  Rechtsgrundlage.

## Flow

1. Die Mitarbeitende öffnet ein ihr zugewiesenes Modul.
2. Die Anwendung startet eine neue `GameRound` mit der nächsten
  `attempt_number` und verwendet die aktuell aktiven, veröffentlichten Fälle.
3. Die Anwendung zeigt nacheinander die fünf Fälle und die jeweiligen
   Antwortmöglichkeiten.
4. Die Mitarbeitende wählt eine Antwort und bestätigt sie.
5. Die Anwendung speichert eine `RoundAnswer` mit ausgewählter Antwort und
  Zeitpunkt.
6. Die Anwendung zeigt sofort, ob die Antwort richtig war, sowie Erklärung und
   Rechtsgrundlage des Falls.
7. Nach dem fünften Fall berechnet die Anwendung die Punktzahl und speichert
   sie zusammen mit dem Bestehensstatus auf `GameRound`.
8. Der Versuch gilt ab 80 Prozent richtigen Antworten als bestanden.
9. Die Anwendung zeigt Punktzahl, Bestehensstatus und den bisherigen
   Schulungsfortschritt an.
10. Die Mitarbeitende kann das Modul später erneut spielen. Für den
    Schulungsstatus zählt der beste Versuch; frühere Versuche bleiben erhalten.
11. Ist die Frist des `Assignment` abgelaufen, darf die Mitarbeitende das Modul
  weiterhin spielen. Der Abschluss wird zusätzlich als `verspätet` markiert;
  Bewertung und Bestehensgrenze bleiben unverändert.
12. Schliesst die Mitarbeitende den Browser während der Runde, bleibt die
  `GameRound` mit dem Status `offen` gespeichert. Bereits gespeicherte
  Antworten bleiben erhalten. Beim nächsten Öffnen wird die Runde an der
  offenen Stelle fortgesetzt und erst nach der letzten Antwort abgeschlossen
  und bewertet.

## Errors

- Nicht angemeldet: Zugriff auf das Modul wird verweigert.
- Falsche Rolle: Abteilungsleitung oder Datenschutzverantwortliche können keine
  Mitarbeitenden-Runde starten.
- Fremde Abteilung: Ein Modul einer anderen Abteilung wird nicht angezeigt und
  kann auch über eine direkte Anfrage nicht gestartet werden.
- Ungültige Antwort: Eine Antwort ausserhalb der angebotenen Optionen wird
  abgelehnt und nicht als `RoundAnswer` gespeichert.
- Doppelte Antwort: Eine bereits beantwortete Frage kann in derselben Runde
  nicht nochmals bewertet werden.
- Nicht gefunden: Ein unbekanntes Modul oder ein unbekannter Fall führt zu
  einer kontrollierten Fehlermeldung.
- Nicht veröffentlichter Fall: Ein Modul mit einem nicht veröffentlichten oder
  unvollständigen Fall kann nicht gestartet werden.

## Acceptance

### AC-001: Zugewiesenes Modul starten

**Given** eine angemeldete Mitarbeitende mit einem Modul ihrer Abteilung  
**When** sie das Modul öffnet  
**Then** startet die Anwendung eine neue `GameRound` mit fünf veröffentlichten
Fällen und der nächsten `attempt_number`.

### AC-002: Nur eigene Abteilung

**Given** eine angemeldete Mitarbeitende mit einem Modul ihrer Abteilung  
**When** sie verfügbare Module abfragt  
**Then** sieht sie nur Module, die ihrer eigenen Abteilung zugewiesen sind.

### AC-003: Antwort speichern

**Given** eine laufende Runde und ein noch nicht beantworteter Fall  
**When** die Mitarbeitende eine angebotene Antwort bestätigt  
**Then** speichert die Anwendung eine `RoundAnswer` mit Antwort und Zeitpunkt.

### AC-004: Sofortiges Feedback

**Given** eine gespeicherte Antwort auf einen Fall  
**When** die Antwort bewertet wurde  
**Then** zeigt die Anwendung sofort richtig oder falsch, die Erklärung und die
Rechtsgrundlage an.

### AC-005: Versuch bestanden

**Given** eine abgeschlossene Runde mit mindestens vier von fünf richtigen
Antworten  
**When** die Anwendung die Runde abschliesst  
**Then** speichert sie die Punktzahl und den Bestehensstatus `bestanden` auf
`GameRound`.

### AC-006: Versuch nicht bestanden

**Given** eine abgeschlossene Runde mit höchstens drei von fünf richtigen
Antworten  
**When** die Anwendung die Runde abschliesst  
**Then** speichert sie die Punktzahl und den Bestehensstatus `nicht bestanden`
auf `GameRound`.

### AC-007: Besten Versuch verwenden

**Given** eine Mitarbeitende hat dasselbe Modul mehrmals gespielt  
**When** der Schulungsstatus angezeigt wird  
**Then** verwendet die Anwendung den besten Versuch und verändert die früheren
Versuche nicht.

### AC-008: Ungültige Antwort ablehnen

**Given** eine laufende Runde  
**When** eine Antwort übermittelt wird, die nicht zu den angebotenen Optionen
gehört  
**Then** lehnt die Anwendung die Antwort ab und speichert keine
`RoundAnswer`.

### AC-009: Fremde Abteilung schützen

**Given** eine angemeldete Mitarbeitende aus Abteilung A  
**When** sie ein Modul von Abteilung B direkt anfordert  
**Then** verweigert die Anwendung den Zugriff ohne Inhalte oder Ergebnisse des
fremden Moduls preiszugeben.

### AC-010: Modul nach Fristabschluss spielen

**Given** ein der Mitarbeitenden zugewiesenes Modul mit abgelaufener Frist  
**When** sie das Modul startet und abschliesst  
**Then** bewertet die Anwendung die Runde normal, markiert den Abschluss als
`verspätet` und wendet weiterhin die Bestehensgrenze von 80 Prozent an.

### AC-011: Offene Runde fortsetzen

**Given** eine offene `GameRound` mit bereits gespeicherten Antworten  
**When** die Mitarbeitende das Modul erneut öffnet  
**Then** setzt die Anwendung dieselbe Runde bei der ersten unbeantworteten
Frage fort und bewertet sie erst nach der letzten Antwort.

### AC-012: Deaktiviertes Szenario nicht verwenden

**Given** ein einem Modul zugeordnetes Szenario ist deaktiviert  
**When** eine neue Runde startet  
**Then** wird das deaktivierte Szenario nicht verwendet.

### AC-013: Veröffentlichtes Szenario unveränderlich

**Given** ein veröffentlichtes Szenario mit Antwortoptionen  
**When** eine Änderung oder Löschung des Szenarios angefordert wird  
**Then** weist die Anwendung die Änderung ab; der Fall wird bei Bedarf
deaktiviert und durch ein neues Szenario ersetzt.

## Tests

- **Unit:** Bewertung von richtigen Antworten und Punktzahl; Bestehensgrenze
  von 80 Prozent; Status aus dem besten Versuch; `attempt_number`; Nutzung nur
  aktiver Szenarien; Unveränderlichkeit veröffentlichter Szenarien; Friststatus
  `verspätet`; Zugriffsregeln für eigene und fremde Abteilungen; Rollen;
  Validierung angebotener Antwortoptionen.
- **Integration:** Start einer Runde über den FastAPI-TestClient; Persistenz
  von `GameRound` und `RoundAnswer`; sofortiges Feedback mit Erklärung und
  Rechtsgrundlage; Abschluss mit gespeicherter Punktzahl; Wiederholung und
  Auswahl des besten Versuchs; Friststatus `verspätet`; Fortsetzung einer
  offenen Runde; Ausschluss deaktivierter Szenarien; Zugriffsschutz auf
  Repository- und Application-Ebene.
- **E2E API:** angemeldete Mitarbeitende starten ein eigenes Modul,
  beantworten fünf Fälle, erhalten Feedback und sehen den Bestehensstatus;
  ein Versuch mit vier richtigen Antworten ist bestanden; ein Versuch mit
  drei richtigen Antworten ist nicht bestanden; eine direkte Anfrage auf ein
  fremdes Modul wird abgelehnt; eine Wiederholung verwendet den besten Versuch;
  eine offene Runde wird nach dem erneuten Aufruf fortgesetzt.
- **Optional Playwright:** Browser-Ablauf für Login, UC-001-Runde, Feedback
  und Ergebnisanzeige, falls die Zeit für Browser-Tests ausreicht.
