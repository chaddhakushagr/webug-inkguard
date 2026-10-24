# Deviations & Changes From Original Plan

**Project:** Inkguard — Intelligent Brand Governance Platform  
**Document Status:** Complete (Phase 4B Verified)  
**Last Updated:** Sat 24 Oct 2026

---

## 1. Architectural Deviations From Round 1 Plan

### 1. In-Process BM25 Lexical Ranking instead of Vector DB (`pgvector`)
- **Original Plan**: External PostgreSQL database provisioned with the `pgvector` extension for semantic guideline and rule retrieval.
- **Change**: Built a pure, in-process BM25 lexical ranking engine ([bm25.py](file:///home/redpanda/Documents/WeBug/backend/app/adapters/retrieval/bm25.py)).
- **Rationale**: 
  - A typical brand guideline set contains ~50–100 curated, high-precision rules, terms, and claims.
  - In-process BM25 executes in $<5\text{ ms}$, eliminates cloud vector database hosting costs, avoids vendor lock-in, and guarantees 100% deterministic local-first testing without network calls or external daemon dependencies.
- **Logged Decision**: [Decision 002](file:///home/redpanda/Documents/WeBug/docs/DECISIONS.md#decision-002-in-process-bm25-retrieval-instead-of-pgvector).

### 2. Unified Static-Export Single Web Service instead of Dual Hosting
- **Original Plan**: Separate deployment with frontend hosted on Vercel and backend API hosted on Render.
- **Change**: Next.js App Router compiled as a static export (`output: 'export'`) and mounted directly onto FastAPI's ASGI static file server.
- **Rationale**:
  - Eliminates cross-origin resource sharing (CORS) complexity and headers.
  - Prevents double cold-start delays on free-tier hosting (users only wait for one service to wake, not two).
  - Stays strictly within Render's single free Web Service quota (750 free instance hours/month).
- **Logged Decision**: [Decision 003](file:///home/redpanda/Documents/WeBug/docs/DECISIONS.md#decision-003-single-web-service-deployment-render--nextjs-static-export).

### 3. Permanent Neon Serverless PostgreSQL instead of Render Postgres
- **Original Plan**: Use Render's free managed PostgreSQL database.
- **Change**: Deployed against **Neon Serverless PostgreSQL** ([Neon Documentation](https://neon.tech/docs/introduction/plans#free-tier)).
- **Rationale**:
  - Official provider review on 24 Oct 2026 confirmed Render deletes free PostgreSQL databases after 30 days. Relying on an expiring database violates the hard constraint *"Do not rely on a free database that expires"*.
  - Neon provides a permanent free plan with 1 GB storage, 100 CU-hrs/month, and no credit card required.
- **Mitigation for Idle Suspension**: Neon compute suspends after 5 minutes of inactivity. Implemented `wait_for_db(max_retries=5, initial_delay=1.0)` with exponential backoff on startup and `pool_pre_ping=True` on the SQLAlchemy engine.
- **Logged Decision**: [Decision 008](file:///home/redpanda/Documents/WeBug/docs/DECISIONS.md#decision-008-cloud-deployment-strategy---permanent-neon-postgresql--render-single-web-service).

### 4. Dual-Path Deployment Packaging (Docker + Committed Static Assets)
- **Original Plan**: Rely exclusively on cloud Docker builds from git repository.
- **Change**: Maintained a production-grade multi-stage [Dockerfile](file:///home/redpanda/Documents/WeBug/Dockerfile) while also pre-compiling the Next.js static export into `backend/app/static/` and providing a native Python [render.yaml](file:///home/redpanda/Documents/WeBug/render.yaml) blueprint.
- **Rationale**:
  - Render free-tier instances allocate only 512 MB of RAM during build time. Running Next.js compilation inside Docker on free hardware can trigger Out-Of-Memory (OOM) failures.
  - Committing the static export enables instant native Python builds (`pip install -r backend/requirements.txt` + `uvicorn app.main:app`) without build memory bottlenecks.

### 5. OpenAI-Compatible Standardized Protocol for Google AI Studio
- **Original Plan**: Direct integration with Google Generative AI Python SDK (`google-generativeai`).
- **Change**: Standardized external LLM communication through Google AI Studio's OpenAI-compatible REST endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`) using model `gemini-2.5-flash`.
- **Rationale**:
  - Decouples application logic from vendor-specific SDKs.
  - Allows seamless switching between Google AI Studio in production and local Ollama (`http://localhost:11434/v1`) without changing code.
- **Logged Decision**: [Decision 004](file:///home/redpanda/Documents/WeBug/docs/DECISIONS.md#decision-004-llm-integration-via-google-ai-studio-openai-compatible-endpoint).

---

## 2. Feature Cut Order Adjustments (SPEC Section 16)

To respect the competition time-box and ensure zero compromise on safety invariants, RBAC, and audit immutability, the following non-critical C-tier features were cut or deferred:

1. **F-14: Unstructured Guideline Document Import (.txt/.md)**:
   - *Status*: **Not Built** (Deferred to Round 3).
   - *Alternative Provided*: Fully implemented structured bulk JSON guideline import and automated seed loader (`manage.py seed` / `POST /api/v1/kb/bulk-import`).
2. **F-26: Real-Time In-App Push Notifications**:
   - *Status*: **Not Built** (Deferred to Round 3).
   - *Alternative Provided*: Real-time UI status stepper, live review progress ticker, role queue counts, and global toast notifications provide full workflow observability.
3. **Round 3 Guideline Ambiguity Scoring**:
   - *Status*: Basic raw performance counters implemented (times triggered, accepted, dismissed, distinct dismissers). Complex ambiguity scoring and rule deprecation workflows reserved for Round 3.
