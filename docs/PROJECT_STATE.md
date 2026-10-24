# Project State: Inkguard

**Current Phase:** Phase 1 (Core Domain & Monolith Implementation)  
**Last Updated:** Sat 24 Oct 2026, 13:20 IST  
**Current Gate:** Pre-Gate 1 (Target: 17:30 IST)  
**Lane Active:** ALL (Sparsh [BE], Kushagra [AI], Apurrv [FE])

## Active Milestones
- [x] Initial repository audit and folder isolation under `WeBug/`
- [x] `AGENTS.md`, `docs/SPEC.md`, and headed documentation skeletons created
- [x] Phase 0: Backend foundation, SQLAlchemy models, modular monolith structure
- [x] Phase 0: OpenAPI 3.1 specification generation (`contracts/openapi.json`) & stub routers
- [x] Phase 0: Next.js static export frontend setup, layout shell, and demo login page
- [x] Phase 0: Architecture validation (`manage.py arch`), 11 passing tests, and CLI wiring
- [x] Phase 0: Tag `p0` verified and committed
- [x] Prompt 0: UI design system, "proofreader's desk" palette, typed UI components, AppShell, login overhaul, /dev/ui component gallery, and evidence screenshots (`docs/evidence/ui-*.png`) [FE]
- [ ] Prompt 1A: Backend real implementation (Auth, RBAC, KB CRUD & versioning, Submissions & diff, State machine & queue, Audit hash chaining, Seed loader) [BE]
- [ ] Prompt 1B: AI domain, seed data, adapters (Lumo seed content, synthetic history, Sanitise/Rules/A11y/Guardrails/Suggest, BM25 retriever, Mock/OpenAI/Cached LLM adapters) [AI]
- [ ] Prompt 1C: Core screens on the design system (KB, Submissions, Reviewer Queue, Submission Detail shell) [FE]
- [ ] Gate G1: Full Draft -> Approved -> Marked Published walkthrough & tracer deploy [ALL]

## Completed Verification
- `manage.py setup`: Virtualenv creation, dependency installation, Alembic migration, and seeding verified.
- `manage.py test`: 11 passing tests (domain unit tests, API integration tests, architecture contract tests).
- `manage.py arch`: 2 import-linter contracts kept (domain purity, application isolation).
- `manage.py build-frontend`: Static export compilation successful with 0 warnings.
- `manage.py e2e`: Live server `/api/v1/health` connectivity verified.
- Prompt 0 Verification:
  - Contrast check: All text/background pairs $\ge 4.5:1$ (WCAG 2.1 AA).
  - Component gallery: `/dev/ui` displaying all components and variants.
  - Screenshots: `docs/evidence/ui-login.png`, `docs/evidence/ui-gallery.png`, `docs/evidence/ui-dashboard.png`.

