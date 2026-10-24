# Architectural & Technical Decisions Log

This document records key technical decisions, rationale, alternatives considered, and free-tier justifications.

## Decision 001: Local-First Storage & Cloud Database
- **Date:** 2026-10-24
- **Decision:** Use SQLite in WAL mode locally (`sqlite:///./data/inkguard.db`) and Neon Serverless PostgreSQL in cloud (`DATABASE_URL`).
- **Rationale:** Allows complete local zero-config testing without Docker or internet connection. Generic SQLAlchemy types (JSON, UTC timestamps, UUID strings) ensure parity across SQLite and Postgres.
- **Free Tier Justification:** SQLite is embedded. Neon's free tier provides 1GB permanent storage without requiring a credit card.

## Decision 002: In-Process BM25 Retrieval instead of pgvector
- **Date:** 2026-10-24
- **Decision:** Implement pure in-process BM25 lexical ranking for the ~50 entry knowledge base rather than pgvector or external vector databases.
- **Rationale:** A ~50-entry brand guideline set is small, high-precision, and deterministic. Avoids cloud vector DB costs, vendor lock-in, and complex vector indexing while running fast in-memory.
- **Free Tier Justification:** In-process Python algorithm, 100% free, runs anywhere.

## Decision 003: Single Web Service Deployment (Render + Next.js Static Export)
- **Date:** 2026-10-24
- **Decision:** Build Next.js with `output: 'export'` and have FastAPI serve static assets in production, exposing `/api/v1` and static client routes under one origin.
- **Rationale:** Render's free tier provides 1 web service without CORS complexity, eliminating two separate wake-up latencies.
- **Free Tier Justification:** Uses Render's single free Web Service quota (750 free instance hours/month).

## Decision 004: LLM Integration via Google AI Studio OpenAI-Compatible Endpoint
- **Date:** 2026-10-24
- **Decision:** Standardize external LLM calls using the OpenAI-compatible endpoint format provided by Google AI Studio (`https://generativelanguage.googleapis.com/v1beta/openai/`) using model `gemini-2.5-flash` (with fallback to `mock` when no key is present).
- **Rationale:** Google AI Studio provides free RPM/RPD API keys for prototyping. OpenAI protocol allows dropping in local Ollama (`http://localhost:11434/v1`) without changing code.
- **Free Tier Justification:** Google AI Studio free tier tier is used with strict in-app daily caps (100 calls/day) and cache persistence to protect quotas.

## Decision 005: Lucide React Icons for Accessible Governance UI
- **Date:** 2026-10-24
- **Decision:** Use `lucide-react` for lightweight, tree-shakeable SVG icons across the design system.
- **Rationale:** Strictly avoids external icon fonts or CDN image requests. Required to satisfy the accessibility constraint "never color alone" by providing distinct iconography for findings, statuses, verdicts, and source types.
- **Free Tier Justification:** Open-source MIT package bundled locally.

## Decision 006: Offline Review Pipeline Execution for Pre-Deployment Verification (Gate G1)
- **Date:** 2026-10-24
- **Decision:** Drive the Gate G1 golden path transition (Draft -> Checked) using the deterministic offline mock engine (`LLM_MODE=mock`) with zero external network egress.
- **Rationale:** Aligns with hard constraint 2 ("Local first - no cloud account or API key required locally") and enables complete end-to-end multi-role state machine verification before wiring live external AI credentials.
- **Free Tier Justification:** 100% offline, zero external LLM calls or cloud usage.
