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

## Decision 007: Review Quota, Content Size Guards, and Headless Auth Support (Gate G2)
- **Date:** 2026-10-24
- **Decision:** Enforce 413 on content exceeding `MAX_CONTENT_CHARS` (20,000 characters), 429 on review rate limit (`RATE_LIMIT_REVIEWS_PER_HOUR=60`), and support `demo-token-` authorization prefix in `DEMO_MODE`.
- **Rationale:** Hardens API boundaries against denial-of-service, verifies SPEC section 12 negative safety requirements, and enables headless browser screenshot capture without fragile session cookie setups.
- **Free Tier Justification:** In-memory tracking and stateless HTTP enforcement; zero cloud infrastructure dependencies.

## Decision 008: Cloud Deployment Strategy - Permanent Neon PostgreSQL + Render Single Web Service
- **Date:** 2026-10-24
- **Decision:** Pair a free Neon serverless PostgreSQL database with a single Render Web Service serving both the FastAPI REST API and the pre-built Next.js static export under one unified origin (`/api/v1` and `/`).
- **Official Documentation Limits Checked on 2026-10-24:**
  - **Neon Serverless PostgreSQL** ([Neon Plans Documentation](https://neon.tech/docs/introduction/plans#free-tier)):
    - *Storage:* 1 GB storage per project.
    - *Compute:* 100 Compute Unit (CU)-hours/month, autoscaling up to 2 CU (8 GB RAM).
    - *Card Requirement:* **No credit card required**.
    - *Database Expiry:* **Permanent** (does not expire).
    - *Idle Suspension:* Computes automatically scale down to zero after 5 minutes of inactivity.
    - *Mitigation:* Implemented `wait_for_db(max_retries=5, initial_delay=1.0)` with exponential backoff on app startup and `pool_pre_ping=True` on SQLAlchemy engine to seamlessly wake Neon compute.
  - **Render Web Service (Hobby Plan)** ([Render Free Tier Documentation](https://render.com/docs/free)):
    - *Compute:* 512 MB RAM, 0.1 CPU.
    - *Hours:* 750 free instance hours/month per workspace (sufficient for one continuous service).
    - *Card Requirement:* **No credit card required**.
    - *Filesystem:* Ephemeral filesystem; local storage resets on restart/redeploy (architecture is strictly stateless; all persistent data is in Neon).
    - *Idle Suspension:* Spins down after 15 minutes of inactivity; takes ~50-60s to wake on the next inbound request.
    - *Mitigation:* Frontend `ColdStartBanner` automatically displays *"Waking the server, this can take about a minute"* if initial request takes >2s. Optional GitHub Actions cron workflow (`.github/workflows/keep_alive.yml`) pings `/api/v1/health` every 10 minutes.
    - *Provider Rejection:* Render's free PostgreSQL was explicitly **rejected** because Render deletes free databases after 30 days. Neon's free database is permanent.
- **Packaging Path Decision:**
  - Provided a multi-stage [Dockerfile](file:///home/redpanda/Documents/WeBug/Dockerfile) (Node 20 static builder + Python 3.12 slim runner).
  - Also committed the built Next.js export into `backend/app/static/` and provided [render.yaml](file:///home/redpanda/Documents/WeBug/render.yaml) for Render's native Python runtime. This eliminates Node compilation overhead on Render's 512MB build environment while preserving multi-stage Docker deployment parity.
  - `NEXT_PUBLIC_API_BASE` dynamically defaults to same-origin `/api/v1` in production, completely eliminating CORS configuration issues.

