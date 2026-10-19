# ADR-005: Antworten für fremde Abteilungen

Status: Accepted
Datum: 2026-10-19
Entschieden von: Projektteam

## Kontext

Rollen dürfen keine Daten fremder Abteilungen sehen. Die API muss zwischen
Informationsschutz und einem bekannten Organisationsbereich unterscheiden.

## Alternativen

- A: UC-001 antwortet mit 404; UC-002 antwortet mit 403.
- B: Einheitlich 403 oder einheitlich 404 für alle Use Cases.

## Entscheid

UC-001 verwendet 404 für ein Modul einer fremden Abteilung, damit niemand
erfährt, ob dieses Modul existiert. UC-002 verwendet 403 für den Zugriff auf
eine fremde Abteilung, weil die Abteilungen als Organisationsbereiche bekannt
sind und nur der Zugriff verboten ist.

## Konsequenzen

Die Fehlerverträge unterscheiden sich bewusst nach Use Case. Die Begründung
wird in den jeweiligen E2E-Fällen und API-Dokumentationen sichtbar gemacht.