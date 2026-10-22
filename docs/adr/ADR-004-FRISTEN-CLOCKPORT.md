# ADR-004: Fristen über ClockPort und Europe/Zurich

Status: Accepted
Datum: 2026-10-19
Entschieden von: Projektteam

## Kontext

Statusberechnungen müssen deterministisch testbar sein und Schweizer lokale
Fristen berücksichtigen.

## Alternativen

- A: Lokales Fristdatum in `Europe/Zurich` bis 23:59:59 Uhr mit `ClockPort`.
- B: Direkter Systemzeitaufruf oder Speicherung eines UTC-Zeitpunkts als Frist.

## Entscheid

Domain und Application erhalten den aktuellen Zeitpunkt über `ClockPort`. Das
Fristdatum gilt in `Europe/Zurich` bis einschliesslich 23:59:59 Uhr. Der
Abschlusszeitpunkt des ersten bestandenen Versuchs bestimmt den Friststatus;
für die Punktzahl zählt weiterhin der beste Versuch. (Präzisiert am 22.10.2026
nach dem Code-Review: Wer rechtzeitig bestanden hat, bleibt `erledigt`, auch
wenn ein späterer Versuch besser ist; vgl. UC-002 AC-006.)

## Konsequenzen

Zeitgrenzen können mit kontrollierten Zeitpunkten getestet werden. Infrastructure
implementiert die Systemuhr; Domain und Application bleiben frei von direkten
Systemzeitaufrufen.