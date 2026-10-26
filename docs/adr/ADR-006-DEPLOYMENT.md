# ADR-006: Deployment als geprüftes Image auf Render mit Neon

Status: Accepted (26.10.2026, nach erfolgreichem Release v0.1.1)
Datum: 2026-10-22
Entschieden von: Sibslusi (Zielbild vorgegeben), umgesetzt mit Claude Code

## Kontext
Phase 5 verlangt ein Deployment auf Render mit einer PostgreSQL-Datenbank auf
Neon und einem Smoke-Test gegen die öffentliche URL. Das, was live läuft, soll
genau das Artefakt sein, das vorher getestet wurde. Secrets dürfen nie ins
Repository. Die Demo braucht Seed-Daten, und Render Free bietet keine Shell
für einmalige Befehle.

## Alternativen
- A: Render baut selbst aus dem Git-Repository (Dockerfile-Build bei Render).
  Einfach, aber das live laufende Image ist ein anderer Build als der im
  Release-Job getestete, und jeder Push auf main kann deployen.
- B: Render Auto-Deploy auf neue Image-Tags. Weniger Kontrolle, kein
  Smoke-Test als Teil der Pipeline, Tags sind veränderlich.
- C: Image in GitHub Actions bauen und mit PostgreSQL testen, nach GHCR pushen
  und Render per Deploy Hook mit dem Image-Digest auslösen; danach Smoke-Test
  gegen die Live-URL.

## Entscheid
Variante C. Render läuft als image-backed Web Service mit Auto-Deploy aus.
`release.yml` übergibt `ghcr.io/sibslusi/project-aiassisted@sha256:…` an
`cd.yml`, das den Deploy Hook mit `imgURL` aufruft und danach
`scripts/smoke_test.py` gegen `RENDER_SERVICE_URL` laufen lässt, bis `/health`
die neue Version meldet. Die Datenbank ist Neon. Der Container migriert bei
jedem Start und lädt mit `RUN_SEED=true` die Seed-Daten, ohne bestehende
Szenarien und Zuweisungen zu überschreiben (ADR-003).

## Konsequenzen
- Live läuft nachweisbar das getestete Image; ein Rollback ist ein erneuter
  Hook-Aufruf mit einem älteren Digest (`cd.yml` per `workflow_dispatch`).
- Das GHCR-Paket muss öffentlich sein oder Render braucht Registry-Zugangsdaten.
- Einrichtung von Hand: Neon, Render-Service, GitHub-Environment `production`
  mit Secrets `RENDER_DEPLOY_HOOK_URL`, `DEMO_PASSWORD` und Variablen
  `CD_ENABLED`, `RENDER_SERVICE_URL`, `SMOKE_EMAIL`.
- Bis `CD_ENABLED=true` gesetzt ist, endet ein Release ohne Deploy, bleibt
  aber grün.
- PROJECT.md, Abschnitt „CI/CD and deployment“, beschreibt den Ablauf.
