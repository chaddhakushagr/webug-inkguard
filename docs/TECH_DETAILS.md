# Technology & Implementation Details: Inkguard

**Product:** Inkguard — Intelligent Brand Governance Platform  
**Target:** Free-Tier Cloud Deployment & Local-First Zero-Config Parity  
**Last Updated:** Sat 24 Oct 2026

---

## 1. Technology Stack & Component Versions

| Component | Technology | Exact Version | Purpose & Rationale |
|---|---|---|---|
| **Runtime (Backend)** | Python | `3.12+` (Runtime Linux 3.14, Container `python:3.12-slim`) | Core application environment; strict typing and async support. |
| **Web Framework** | FastAPI | `0.162.0` | High-performance async REST API; auto OpenAPI 3.1 contract generation. |
| **Frontend Framework** | Next.js (App Router, React 19) | `16.4.3` (`react: 19.3.0`, `react-dom: 19.3.0`) | Modern React 19 UI; compiled as static export (`output: 'export'`) for unified single-origin hosting. |
| **ORM / Data Access** | SQLAlchemy | `2.1.6` | Database-agnostic schema with unified support for SQLite (local WAL) and PostgreSQL (Neon cloud). |
| **Database Migrations** | Alembic | `1.20.1` | Transactional schema migrations and PostgreSQL audit trigger provisioning. |
| **Data Validation** | Pydantic & Pydantic Settings | `2.14.1` (`pydantic-settings: 2.16.1`) | Strict runtime boundary validation, env var coercion, and OpenAPI schemas. |
| **Test Runner** | Pytest & Pytest-Asyncio | `9.1.1` (`pytest-asyncio: 1.4.0`) | Unit, integration, workflow state machine, and safety invariant test execution. |
| **Styling** | Tailwind CSS | `v4.3.3` (`@tailwindcss/postcss: ^4.3.3`) | Proofreader's Desk custom design tokens; zero runtime CSS overhead. |
| **Iconography** | Lucide React | `^1.61.0` | Lightweight tree-shakeable accessible SVGs; satisfies "never color alone" constraint. |
| **PostgreSQL Drivers** | `psycopg` (v3) & `psycopg2-binary` | `psycopg: 3.3.6`, `psycopg2-binary: 2.9.13` | Dual-driver support for zero-config compatibility with any PostgreSQL connection string. |
| **Architecture Linter** | `import-linter` | `2.4` | Enforces clean architecture dependency boundaries between domain, application, and adapters. |

---

## 2. Architecture Summary

Inkguard is structured as a **modular monolith adhering strictly to Ports and Adapters (Hexagonal / Clean Architecture)**. Dependency flow is strictly unidirectional:

$$\text{api} \longrightarrow \text{application} \longrightarrow \text{domain}$$
$$\text{adapters} \longrightarrow \text{ports} \quad (\text{adapters implement interfaces defined in } \text{ports/})$$

- **`domain/` (Pure Python Core)**:
  - Zero imports from web, database, HTTP, or LLM libraries (`FastAPI`, `SQLAlchemy`, `httpx`, `openai` forbidden).
  - Contains:
    - Workflow state machine ([WorkflowStateMachine](file:///home/redpanda/Documents/WeBug/backend/app/domain/workflow/state_machine.py)).
    - RBAC clearance policies and `allowed_actions` calculation ([permissions.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/workflow/permissions.py)).
    - Deterministic rule engine for terms, claims, and leaks ([rule_engine.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/rule_engine.py)).
    - Text accessibility and Flesch-Kincaid readability checks ([accessibility.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/accessibility.py)).
    - Guardrails dropping hallucinated citations and mismatched excerpts ([guardrails.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/guardrails.py)).
    - Suggestion validators enforcing $\le 60\%$ character edit distance ([pipeline.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/pipeline.py)).
  - Enforced continuously by `python manage.py arch` (`Domain layer purity KEPT`).
- **`application/` (Use Cases & Orchestration)**:
  - Orchestrates domain entities and port interfaces within clean transactions.
  - Owns review pipeline execution ([ReviewOrchestrator](file:///home/redpanda/Documents/WeBug/backend/app/application/review.py)), stage progression (`extracting`, `rule_checks`, `retrieving`, `analysing`, `finalising`), and fallback degradation.
  - Enforced continuously by `python manage.py arch` (`Application layer isolation KEPT`).
- **`ports/` (Protocol Interfaces)**:
  - Python typing `Protocol` definitions: `LLMClient`, `RetrieverPort`, `ReviewStorePort`, `AuditSink`, `Clock`.
- **`adapters/` (Infrastructure Implementations)**:
  - Database: SQLAlchemy models, Alembic migrations, session management with connection pool pre-pinging.
  - LLM: `OpenAICompatibleLLMAdapter`, `MockLLMAdapter`, `CachedLLMAdapter`.
  - Retrieval: In-process `BM25Retriever` with classification tier boundaries.
  - Security: Bcrypt password hashing and PyJWT token issuance.
- **`api/` (Presentation & Transport)**:
  - Thin FastAPI routers (`/auth`, `/users`, `/kb`, `/submissions`, `/findings`, `/comments`, `/insights`, `/audit`, `/settings`).
  - Standardized error response envelope (`{code, message, details}`).

---

## 3. AI Integration & Telemetry

### Model & Protocol
- **Primary LLM**: `gemini-2.5-flash` via Google AI Studio's OpenAI-compatible REST endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`).
- Standardized OpenAI protocol allows seamless drop-in of local Ollama (`http://localhost:11434/v1`) without modifying code.

### Execution Modes
1. **`mock` (Default)**: Fully offline deterministic pipeline using curated Lumo brand fixtures. Requires zero network access and zero API keys.
2. **`cached`**: In-memory and database-backed hash response cache for instant, zero-cost evaluation of repeated content.
3. **`live`**: Direct structured JSON generation from Google AI Studio.
4. **`rules_only`**: Fast rule-based checks, regex matching, terminology lookup, accessibility metrics, and guardrail validation with zero outbound AI calls.

### Fallback Chain & Guardrails
- **Administrative "No External AI" Switch**: Setting `no_external_ai = True` in system settings immediately halts all outbound model requests, cleanly routing reviews through `rules_only`.
- **Daily Call Cap (`LLM_DAILY_CAP`)**: Tracks live LLM requests per calendar day; automatically degrades to `rules_only` once the cap is reached, presenting a clear explanation in the UI.
- **Data Boundary Log**: Every review records an immutable telemetry block (`GET /api/v1/reviews/{id}/boundary`) detailing provider, model, characters sent (strictly 0 in mock mode), redaction counts, included entry codes, and maximum clearance tier transmitted.
- **Confidential Egress Boundary**: Confidential entries and seeded secrets are hard-filtered before retrieval and asserted absent before payload transmission.

---

## 4. Free-Tier Cloud Deployment Target

| Resource | Provider & Plan | Tier Limits | Architecture Mitigation |
|---|---|---|---|
| **Managed Database** | **Neon Serverless PostgreSQL** (Permanent Free Tier) | 1 GB storage, 100 CU-hrs/mo, no credit card required. Scales to zero after 5 min idle. | `pool_pre_ping=True` and `wait_for_db(max_retries=5)` with exponential backoff on startup wake compute smoothly without request failures. |
| **Web Service** | **Render Web Service** (Hobby Free Plan) | 512 MB RAM, 0.1 CPU, 750 free instance hrs/mo, no credit card required. Ephemeral filesystem. Spins down after 15 min idle. | Next.js built as static export (`output: 'export'`) served directly by FastAPI (`uvicorn`) under single origin. `<ColdStartBanner />` displays *"Waking the server, this can take about a minute"*. Optional `.github/workflows/keep_alive.yml` pings `/api/v1/health` every 10 min. |
| **LLM Inference** | **Google AI Studio** (Free Tier) | 15 RPM, 1,500 RPD, free API key. | In-app 100 daily cap (`LLM_DAILY_CAP`), response caching, and automatic fallback to `rules_only` and `mock`. |

---

## 5. Free-Tier Constraints & Mitigations

1. **Expiring Free Databases**:
   - *Constraint*: Render deletes free PostgreSQL instances after 30 days.
   - *Mitigation*: Rejected Render PostgreSQL; paired Render Web Service with permanent Neon Serverless PostgreSQL.
2. **Low-Memory Build Environment (512 MB RAM)**:
   - *Constraint*: Running `next build` inside Docker on Render's 512 MB environment can trigger out-of-memory errors.
   - *Mitigation*: Pre-compiled static export committed into `backend/app/static/`, enabling fast, low-memory native Python builds via [render.yaml](file:///home/redpanda/Documents/WeBug/render.yaml) while retaining multi-stage [Dockerfile](file:///home/redpanda/Documents/WeBug/Dockerfile) for environments with sufficient memory.
3. **CORS & Dual-Host Cold-Start Latency**:
   - *Constraint*: Hosting frontend on Vercel and backend on Render introduces dual cold starts and complex CORS configurations.
   - *Mitigation*: Single web service serves both the API (`/api/v1`) and the static frontend (`/`) under the same origin with zero cross-origin latency.
