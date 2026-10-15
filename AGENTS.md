# AGENTS.md — AI-SDLC Router

Repository state lives in:

docs/TASKS.md

Maintain `docs/TASKS.md`: PHASE = selected phase; STATUS = ready, in-progress,
done or blocked. Set in-progress on entry, done only after the phase output is
verified, or blocked with a reason. Keep PHASE on completion; an explicitly
selected next phase starts as ready. Changes to this router require human review.

---

Phases may be **skipped or repeated**.

Typical iteration:

SPECIFY → DESIGN → DEVELOP → VALIDATE  
VALIDATE → SPECIFY (iteration)  
DEPLOY → SPECIFY (feedback)

---

## Fast Track

- Small corrections only; no feature, API, data, security, dependency or architecture changes.
- Record scope, reason, acceptance and checks in the existing UC or `docs/TASKS.md`.
- Shorten SPECIFY; skip DESIGN with a reason. Scope grows → regular flow.
- Keep required CI and review. Release/deployment still require authorization.

## Collaboration

- Human-approved decisions → ADR; current architecture → `docs/PROJECT.md`.
- Durable rules + ADR links → `AGENTS.md`, with human approval/review.
- Update related files together; preserve decision history and reconcile parallel changes.

## Context Load Order

1. docs/TASKS.md  
2. docs/PROJECT.md  
3. docs/specs/UC-[NNN]-[NAME].md (or the eligible Fast Track task entry)

---

## Phase → Skill

0 → skills/ai-sdlc-0-bootstrap  
1 → skills/ai-sdlc-1-specify  
2 → skills/ai-sdlc-2-design  
3 → skills/ai-sdlc-3-develop  
4 → skills/ai-sdlc-4-validate  
5 → skills/ai-sdlc-5-deploy  
End of every phase → skills/ai-sdlc-quality-gate (before STATUS done)  

---

## Commands

Use the project-specific install, test, run and release commands documented in
`docs/PROJECT.md`.

---

## Rules

- Use the language of the current user prompt for all communication and all
  natural-language artifacts. Do not default to the language of earlier
  messages.
- Update existing artifacts; create only what is missing.
- Keep artifacts **minimal**.
- Avoid unnecessary comments in code.
- Follow **TDD** (tests before code).
- Respect **Clean Architecture**  
  domain ← application ← interfaces ← infrastructure
- Prefer **small vertical slices** (one UC end-to-end).
- Read the [canonical AI-SDLC documentation](https://docs.aisl.science/learning-and-resources/ai-sdlc)
  when terminology or lifecycle responsibilities are unclear.

If requirements or architecture are unclear → ask the user.

---

## Project Rules — Datenschutzszenarien in der Gemeinde

- Product, roles, entities and stack: `docs/PROJECT.md`. Decisions: `docs/adr/`.
- `src/app/domain` must not import fastapi, sqlalchemy, jinja2 or httpx; enforced by import-linter in CI.
- TDD visible in Git: separate commits `test:` (red) → `feat:` (green) → `refactor:`.
- Access rules are business logic in `application`, covered by unit tests:
  employees see only their own results; department leads see only their department,
  per-person status only, scores aggregated; data protection officers see all.
- Domain rules with unit tests: team aggregates only for groups of 3 or more;
  current date passed in (clock port), never `datetime.now()` in domain/application;
  scenario edits create a new version, answered rounds keep their version.
- Fictional data only. No real names, no real data of Stadt Grenchen.
- Login: passwords hashed with bcrypt/argon2, secure session cookie, CSRF protection on forms.
- Secrets only in `.env` (gitignored) or GitHub Secrets; keep `.env.example` with placeholders.
- LLM calls (UC-003) only via the `infrastructure` adapter to LiteLLM; tests use a fake adapter.
- End every phase with `skills/ai-sdlc-quality-gate`: report checks with evidence, ask open questions, set STATUS done only after the user confirms.
- Every agent session that changes code or docs: add one entry to `docs/AI-LOG.md`.
- MCP servers in use and their permissions: see README section "KI-Tooling".
