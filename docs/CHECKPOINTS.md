# Checkpoints & Gates Log

## Gate Schedule & Status

| Gate | Target Time (IST) | Status | Commit / Tag | Summary & Evidence |
|---|---|---|---|---|
| **Phase 0 (Exit)** | Sat 13:45 | **DONE** | `p0` | Monolith scaffold, contracts/openapi.json, 15 models, stubs, 11 tests, Next.js static export |
| **Prompt 0 (UI)** | Sat 14:15 | **DONE** | `839cece` | Proofreader design system, typed UI components, AppShell, login overhaul, gallery, evidence screenshots |
| **Prompt 1A (BE)** | Sat 14:50 | **DONE** | `0dfb8b3` | Real JWT auth, RBAC domain, immutable KB versioning, Submissions & diff, Table-driven workflow, Hash-chained audit, Seed loader |
| **Prompt 1B (AI)** | Sat 15:15 | **DONE** | `fabf445` | AI review pipeline, BM25 retriever, LLM adapters, Lumo seed content, synthetic history, 10 offline tests |
| **Prompt 1C (FE)** | Sat 15:45 | **DONE** | `2aac793` | Core screens on design system, role dashboards, KB diff, submissions shell, reviewer queue, static export |
| **G1** | Sat 19:30 | **DONE** | `g1` | Full workflow verified: Draft -> Approved -> Marked Published, 2-reviewer requirement, fact v2, agency isolation, self-approval refusal, SHA-256 audit chaining |
| **G2** | Sat 22:00 | Planned | `g2` | Review engine integrated, golden path GP-1..GP-6 local, screenshots |
| **G3** | Sun 01:00 | Planned | `g3` | Free-cloud deployment verified, GP-1..GP-8 live incognito, insights |
| **G5** | Sun 07:30 | Planned | `v0.2.0-round2` | Hardening, audit logs, doc pack complete, ready for submission |

### Phase 0 Verification Notes
- CLI: `python manage.py setup`, `test`, `arch`, `openapi`, `build-frontend`, and `e2e` verified.
- Backend: Modular monolith structure created; 15 SQLAlchemy models with Alembic initial migration.
- Clean Architecture: `import-linter` contracts enforced via `manage.py arch`.
- Frontend: Next.js 16 static export built cleanly with TypeScript and Tailwind CSS; typed API client configured.
- Invariants: Creator cannot approve own submission enforced in domain tests.

### Prompt 0 (UI Design System & App Shell) Notes
- Design Tokens: Light theme "Proofreader's desk" palette (Ink Navy #1F2A44, Teal #0F766E, Paper #F7F7F4, Surface #FFFFFF, Border #E2E5EA, Muted #5B6475; High #B42318, Medium #B45309, Low #175CD3, Success #067647).
- WCAG AA: Contrast ratios verified $\ge 4.5:1$ across all text/background pairs.
- Typed Components: Button, Input, Textarea, Select, Badge, Card, Tabs, Dialog, Toast, Tooltip, Table, EmptyState, ErrorState, Skeleton, Banner, StatusStepper, DiffView, HighlightedText (solid for Rule vs wavy dotted for AI), PageHeader, AIBadge, ModeChip.
- AppShell: Sidebar (collapses under 1024px), top bar with ModeChip and demo role switcher, skip-to-content, teal focus rings.
- Login Redesign: 2-column layout with 5 demo-user cards and manual fallback.
- Component Gallery: `/dev/ui` showing all component variants.
- Static export: `npm run build` succeeds cleanly. Evidence screenshots saved in `docs/evidence/ui-*.png`.

