# Checkpoints & Gates Log

## Gate Schedule & Status

| Gate | Target Time (IST) | Status | Commit / Tag | Summary & Evidence |
|---|---|---|---|---|
| **Phase 0 (Exit)** | Sat 13:45 | **DONE** | `p0` | Monolith scaffold, contracts/openapi.json, 15 models, stubs, 11 tests, Next.js static export |
| **G1** | Sat 17:30 | In Progress | `g1` (target) | Core workflow end-to-end, domain rules, tracer deploy |
| **G2** | Sat 22:00 | Planned | `g2` | Review engine integrated, golden path GP-1..GP-6 local, screenshots |
| **G3** | Sun 01:00 | Planned | `g3` | Free-cloud deployment verified, GP-1..GP-8 live incognito, insights |
| **G5** | Sun 07:30 | Planned | `v0.2.0-round2` | Hardening, audit logs, doc pack complete, ready for submission |

### Phase 0 Verification Notes
- CLI: `python manage.py setup`, `test`, `arch`, `openapi`, `build-frontend`, and `e2e` verified.
- Backend: Modular monolith structure created; 15 SQLAlchemy models with Alembic initial migration.
- Clean Architecture: `import-linter` contracts enforced via `manage.py arch`.
- Frontend: Next.js 16 static export built cleanly with TypeScript and Tailwind CSS; typed API client configured.
- Invariants: Creator cannot approve own submission enforced in domain tests.
