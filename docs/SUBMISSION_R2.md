# Hackathon Round 2 Submission Pack: Team WeBug

## 1. Working Link and Demo Accounts
- **Public URL**: `[Pending Deployment at Gate G3]`
- **Demo Mode**: Enabled (`DEMO_MODE=true` banner visible on all pages)
- **Demo Accounts**:
  - `creator.social@lumo.internal` (Creator, Team Social, Internal Tier)
  - `creator.agency@contractor.external` (Agency Creator, External, Public Tier)
  - `reviewer.sarah@lumo.internal` (Reviewer, Internal Tier)
  - `manager.elena@lumo.internal` (Brand Manager, Confidential Tier)
  - `admin@lumo.internal` (System Admin, Confidential Tier)
  - Password for all: `LumoDemo2026!`

## 2. Repository Link
- **GitHub Repository**: `[Pending Remote Push]`

## 3. Project PDF Content & Architecture Overview
- **Product Overview**: Inkguard is a pre-publication brand-governance engine that checks marketing copy against organizational guidelines, tone, facts, and legal rules. It offers cited justifications, intent-preserving minimal fixes, and leaves all authority with humans.
- **Architecture**: Modular monolith with Clean Architecture:
  `api -> application -> domain`, and `adapters -> ports`.
- **Plan vs Delivery**: Core pipeline, full state machine, RBAC, hash-chained audit logging, BM25 retrieval, and Next.js static export frontend delivered per specification.

## 4. Completed Features
See [docs/FEATURES_COMPLETED.md](FEATURES_COMPLETED.md) for the verified status table and verification steps.

## 5. Technology & Implementation Details
- **Backend**: Python 3.14 / 3.12, FastAPI, SQLAlchemy 2.0, Pydantic V2, Alembic, SQLite WAL / Neon PostgreSQL.
- **Frontend**: Next.js 14+ App Router (TypeScript, Tailwind CSS) static export (`output: 'export'`).
- **AI / NLP**: In-process BM25 lexical retriever, OpenAI-compatible Google AI Studio integration (`gemini-2.5-flash`), offline mock fixtures, hash-based LLM response cache.
- **Testing**: `pytest`, `httpx` integration tests, `import-linter` architectural contract verification.

## 6. Changes From Original Plan
See [docs/CHANGES_FROM_PLAN.md](CHANGES_FROM_PLAN.md):
1. In-process BM25 replaced pgvector to maintain zero cloud dependency and high deterministic speed.
2. FastAPI single-service static file serving replaced split hosting for reliable free-tier hosting on Render.

## 7. Round 3 Improvements Plan
See [docs/ROUND3_PLAN.md](ROUND3_PLAN.md):
1. **Reliability Engine**: Bidirectional verifier LLM with continuous precision/recall benchmarking.
2. **Guideline Health Intelligence**: Automated ambiguity scoring, uncited comment clustering, and draft rule recommendations.
3. **Multi-Format Review**: Rich PDF/DOCX structural parsing, image OCR, and computer-vision brand asset compliance.

## AI & External Service Disclosure
- External calls use Google AI Studio free tier under strict daily rate limits.
- Zero confidential entries or proprietary user tokens are transmitted externally.
- Synthetic brand data ("Lumo") used exclusively throughout.
