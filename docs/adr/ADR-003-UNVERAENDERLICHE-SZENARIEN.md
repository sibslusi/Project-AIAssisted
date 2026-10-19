# ADR-003: Unveränderliche Szenarien und geordnete Module

Status: Accepted
Datum: 2026-10-19
Entschieden von: Projektteam

## Kontext

Historische Antworten müssen auch nach der Korrektur eines Datenschutzfalls
unverändert auswertbar bleiben. Module benötigen genau fünf geordnete aktive
Szenarien.

## Alternativen

- A: `module_scenarios` mit eindeutiger Kombination `(module_id, position)`.
- B: Szenario-Fremdschlüssel direkt auf `Module` oder eine Versionierung.

## Entscheid

Ein Modul verweist über `module_scenarios` auf geordnete Szenarien. Ein Ersatz
stellt die bestehende Zeile auf die neue `scenario_id` um und setzt das alte
Szenario auf `active = false`. Eine neue Runde startet nur bei genau fünf
Positionen mit aktiven Szenarien. `game_round_scenarios` speichert die fünf
Szenario-IDs und Positionen als unveränderlichen Runden-Snapshot.

## Konsequenzen

Ein Szenario kann in mehreren Modulen vorkommen. Alte Runden bleiben gültig;
Deaktivierung und Ersatz verändern keine historischen Snapshots. Eine separate
Szenario-Versionierung ist nicht erforderlich.