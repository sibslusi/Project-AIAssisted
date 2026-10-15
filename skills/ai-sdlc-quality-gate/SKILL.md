---
name: ai-sdlc-quality-gate
description: Check a phase's output against the capstone grading criteria before its status is set to done. Run at the end of every phase.
---

# QUALITY GATE — end of every phase

## Goal

Verify the current phase output against the checklist below and the capstone
grading criteria, then report to the user. Never set STATUS to done yourself:
done needs the user's confirmation.

---

## Procedure

1. Read `docs/TASKS.md` (current PHASE and UC) and `docs/PROJECT.md`.
2. Go through **Always** and the section for the current phase.
3. Check each item against the repository (files, test runs, git log), not from memory.
4. Fix what you can fix within the current phase. Do not start the next phase.
5. Report to the user:

   | # | Check | Result (✓ / ✗ / n/a) | Evidence (file, command output, commit) |

6. List **open questions** for the user: anything unclear, assumed, or legally uncertain.
7. Propose the AI-LOG line for this session (date, phase/UC, agent + model, task, result, correction, lesson).
8. Ask: "Soll ich STATUS auf done setzen?" Wait for the answer.

---

## Always

- Only the current phase's work was done; nothing invented beyond the UC or PROJECT.md.
- Natural-language artifacts are in German.
- No secrets in the repo (`git grep -iE "sk-|api[_-]?key\s*=\s*['\"][^'\"]+"` finds nothing real).
- Only fictional data; no real names or real data of Stadt Grenchen.
- `docs/TASKS.md` reflects PHASE, STATUS and current UC.
- Decisions with consequences have an ADR in `docs/adr/` (status Proposed until the user accepts).

## Phase 0 — Bootstrap

- `docs/PROJECT.md` has purpose, users, in/out of scope, architecture with dependency direction, entities with relations, roles and permissions, domain rules, commands, configuration variable names.
- At least 5 entities; Rundenantwort, Modul and Zuweisung are present.
- Folders exist: `src/app/{domain,application,interfaces,infrastructure}`, `tests/{unit,integration,e2e}`.
- `requirements.txt` covers the stack; `.env.example` exists; `.env` is gitignored.
- Backlog in `docs/TASKS.md` lists UC-001 to UC-003.
- No application code written.

## Phase 1 — Specify

- `docs/specs/UC-NNN-NAME.md` follows `UC-TEMPLATE.md`.
- Every acceptance criterion is Given/When/Then and independently testable.
- Errors cover: not logged in, wrong role, other department, invalid input, not found.
- Role rules from PROJECT.md are reflected (aggregates only for groups ≥ 3, department leads see status only per person).
- Tests section maps each criterion to unit, integration or E2E.
- No code or tests written.

## Phase 2 — Design

- Components listed per layer; no layer depends outward.
- Repository ports defined in `application`, adapters in `infrastructure`.
- E2E test cases described in the UC's Tests section.
- PROJECT.md updated only if needed; architecture diagram (Mermaid) present.
- No implementation code.

## Phase 3 — Develop

- Git log shows TDD: `test:` commit before the matching `feat:` commit, then optional `refactor:`.
- Integration tests and unit tests exist for every acceptance criterion and domain rule.
- All unit and integration tests pass (show the command output).
- `src/app/domain` imports no fastapi, sqlalchemy, jinja2 or httpx (import-linter passes once configured).
- No `datetime.now()` in domain or application; the date comes from a clock port or parameter.
- Code is minimal; no unused files or speculative features.

## Phase 4 — Validate

- Unit, integration and E2E tests pass locally; coverage reported.
- Dockerfile builds; the app starts in the container and `/health` answers.
- `ci.yml` runs lint, import-linter, unit and integration tests, pip-audit; under 10 minutes.
- `release.yml` builds the container, runs E2E tests and publishes the artifact.
- Omitted checks are recorded with a reason in `docs/TASKS.md`.

## Phase 5 — Deploy

- `cd.yml` triggers on release only and uses the Render deploy hook from a GitHub Secret.
- Database on Neon; only secret names documented, never values.
- Smoke test against the public URL after deploy.
- README has the live URL and demo logins per role.

---

## Before the final submission (29.10.)

- README: purpose, live URL, demo logins, Mermaid architecture, local start with Docker, tests, CI/CD, AI tooling (agents, models and why, MCP servers with permissions), limits ("fiktive Daten, keine Rechtsberatung").
- `docs/AI-LOG.md` has entries for every phase and the model comparison.
- All ADRs are Accepted or Superseded.
- Every UC is linked from its PR; `main` is green.
