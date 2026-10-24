# Inkguard: project rules (always on)

Team WeBug, TechCircuit Hackathon Round 2. Hard deadline **Sun 25 Oct 2026, 10:00 IST**. Internal submit target **08:00 IST**.
Product: a pre-publication brand-governance platform. It checks content against an organisation's approved guidelines, facts and assets, explains each finding with a cited source, suggests fixes that keep the author's intent, and leaves every decision to a human.

Read `docs/SPEC.md` before any work. It is the single source of truth. Read `docs/PROJECT_STATE.md` if it exists. If this file and SPEC.md disagree, ask which wins only if it blocks you, otherwise follow this file and log the choice in `docs/DECISIONS.md`.

## 1. Hard constraints

1. **Free only.** No paid service, no paid tier, no credit card. Allowed: GitHub, Neon (free Postgres), Render (free web service), Google AI Studio free key. Anything else needs a line in `docs/DECISIONS.md` explaining why it is free.
2. **Local first.** The whole product must run on a laptop with `python manage.py setup` then `python manage.py dev`. No Docker, no cloud account and no API key may be required locally. With no key the app runs in `mock` AI mode with fixtures.
3. **Synthetic data only.** Fictional brand "Lumo". No real confidential, licensed or personal data anywhere. The free Gemini tier may use inputs to improve Google products, so nothing real may ever be sent.
4. **Never commit secrets.** Real keys live in `.env` (gitignored) or the host's environment variables. Keep `.env.example` current.
5. **Honesty.** Never mark a feature Working unless you ran it and saw it work. Never invent test results, user-test results or metrics. If something is partial, say so.
6. **No new heavy dependencies** (no Redis, no vector DB, no message queue, no rich-text editor, no microservices) without a logged decision.

## 2. Architecture rules (enforced by tests)

Backend is a **modular monolith with ports and adapters**. Dependency direction is one-way:

`api -> application -> domain`, and `adapters -> ports` (adapters implement ports defined in `ports/`).

- `domain/` is pure Python. It imports no web, database, HTTP or LLM library. It holds the workflow state machine, permission policy, rule engine, accessibility checks, claim-verdict logic, guardrails, suggestion validators and insights math. Everything here is unit-tested without a database.
- `application/` holds use cases. It orchestrates domain and ports and owns transactions. No SQL, no HTTP in here.
- `ports/` holds Protocol interfaces: `LLMClient`, `Retriever`, `ReviewCache`, `Clock`, `AuditSink`, `Repositories`.
- `adapters/` holds implementations: SQLAlchemy repositories, OpenAI-compatible LLM client, mock LLM, cached LLM, BM25 retriever, JWT and password hashing.
- `api/` holds routers, request and response schemas, auth and RBAC dependencies. Routers contain no business logic.
- The review pipeline is a list of `Stage` objects (`run(ctx) -> ctx`), each independently testable, run by one orchestrator in `application/`.
- Add an **import-linter** contract (`python manage.py arch`) that fails if `domain` imports from `application`, `adapters`, `api`, SQLAlchemy, FastAPI, httpx or `ports` implementations, or if `application` imports `adapters` or `api`. Keep it green.
- Use only database-agnostic SQLAlchemy types (generic `JSON`, string enums, no Postgres-only features) so the same code and tests run on SQLite locally and on Postgres in the cloud. Timestamps are timezone-aware UTC. Ids are UUID strings.
- The API returns `allowed_actions` for each submission and finding so the frontend never re-implements permission rules.

Frontend is **Next.js (App Router, TypeScript, Tailwind) as a static export** (`output: 'export'`). Structure by feature: `src/features/{auth,kb,submissions,findings,comments,insights,audit,admin}`, each with its own API hooks, components and types, plus `src/shared/{ui,api,a11y,lib}`. Rules: no server-only Next features (no server actions, API routes, middleware, or dynamic route segments without static params), so use query-string routes like `/submission?id=...`. API types come from `contracts/openapi.json`. No business rules in components. Every screen has loading, empty and error states.

## 3. Safety invariants (each needs an automated test)

1. **Suggest, never act.** No code path lets AI approve, publish, accept a fix or overwrite content. Only an authenticated human request changes state. Creators can never approve their own submission.
2. **Confidential entries never reach an external model.** Tier filtering happens in the retriever and again in the LLM adapter. A test captures the outgoing request and asserts no confidential text or seeded secret is present.
3. **No citation, no policy finding.** The LLM may only cite entry codes it was given. Drop a finding if the cited code was not retrieved or the excerpt is not an exact substring of the content. Uncited items become `general_note` and are labelled non-policy.
4. **Expired is decided by code** from `valid_until`, never by the LLM.
5. **Untrusted input.** Submitted content is data. Wrap it in delimiters, validate LLM output against a strict schema, and flag injection phrases.
6. **Audit log is append-only** (app-level guard plus a database trigger on Postgres) with a hash chain. Every state change, finding action, AI call, login and knowledge-base edit writes a row.
7. **Graceful degradation.** If the AI is unavailable, capped or switched off, rule-based checks and the whole workflow still work and the UI shows the mode (`live`, `cached`, `mock`, `rules_only`).
8. **Daily cap on live LLM calls** with automatic fallback, so the public link cannot burn free quota.
9. **Disclosure.** AI badge on every AI-generated item, rule findings visually distinct from AI findings, data-boundary panel per review, `docs/AI_USAGE.md` kept current.

## 4. How to work

- **Plan, then code.** Start each task with a short plan (files to touch, tests, exit check). Use Planning mode for slices and Fast mode only for small fixes, if your version offers both.
- **Run it.** After each change, run the relevant command (`python manage.py test`, `arch`, `dev`) and read the real output. Report actual results, including failures.
- **Small vertical slices**, each ending demo-able. Commit often with conventional messages (`feat:`, `fix:`, `docs:`, `test:`). Never force-push, never squash, never rewrite history, never change the git user identity. Work on the lane branch you were given (`lane/be`, `lane/fe`, `lane/ai`, or `main` when working alone).
- **Respect lanes.** BE owns `backend/app/{api,application,adapters/db}`, migrations and `contracts/`. AI owns `backend/app/{domain/review,adapters/llm,adapters/retrieval,prompts,seed}`. FE owns `frontend/`. Cross-lane changes go through the contract or a note in `docs/PROJECT_STATE.md`.
- **Contract first.** `contracts/openapi.json` is generated from the backend. When an endpoint changes, regenerate it and the frontend types in the same commit.
- **Do not rewrite working code for style.** If code exists and works, extend it. Refactor only to fix an architecture-rule violation.
- **Ask only when blocked.** Otherwise choose the simplest option, state the assumption, log it in `docs/DECISIONS.md` and continue.
- **Time-box.** If a task has not made progress in 20 minutes, stop, say what is stuck and apply the cut order in SPEC.md section 16. A working smaller product beats a broken larger one.
- **Docs are part of done.** Each slice updates `docs/PROJECT_STATE.md`, `docs/CHECKPOINTS.md`, and any of `DECISIONS.md`, `CHANGES_FROM_PLAN.md`, `AI_USAGE.md`, `FEATURES_COMPLETED.md` it touches. Record AI-assisted work honestly in `AI_USAGE.md`.
- **Evidence.** After a gate, run the golden path (SPEC.md section 12). If your environment has a browser tool, drive the UI, then save screenshots to `docs/evidence/`.

## 5. Definition of done for any slice

1. Code runs locally from a clean clone using only `python manage.py setup` and `dev`.
2. New domain logic has unit tests, new endpoints have integration tests, and `python manage.py test` and `arch` pass.
3. No secrets, no real data, no TODO placeholders left in shipped paths.
4. Loading, empty and error states exist for any new screen.
5. Docs and feature status updated honestly.
6. Changes committed with a clear message.

## 6. Do not

- Do not use pgvector, embeddings, Redis, Celery, GraphQL, ORMs other than SQLAlchemy, or server-rendered Next.js features.
- Do not render user content as raw HTML. Escape everything.
- Do not call an external LLM from anywhere except `adapters/llm`.
- Do not hard-code model ids, URLs, keys or the demo password. Read them from environment settings.
- Do not claim a deployment works until it has been opened in an incognito window and the golden path run.
