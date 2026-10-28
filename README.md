# Inkguard: Pre-Publication Brand Governance Platform

Inkguard is an automated pre-publication brand governance platform that validates marketing and product content against approved brand guidelines, legal disclaimers, tone rules, and visual asset registries. It delivers instant, transparent compliance reviews by explaining every finding with an exact cited source, generating minimal-edit suggestions that preserve creator intent, and enforcing human-in-the-loop editorial sign-offs. Built as a Clean Architecture modular monolith, it operates entirely offline in zero-cost mock mode or connects to modern LLMs with strict data boundaries that prevent confidential leaks.

---

## Quick Links

- **Live Deployment:** [https://inkguard.onrender.com](https://inkguard.onrender.com)
- **Architecture & System Design:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Round 3 Changes & Enhancements:** [docs/ROUND3_CHANGES.md](docs/ROUND3_CHANGES.md)
- **Testing & Quality Assurance Report:** [docs/TESTING.md](docs/TESTING.md)
- **Benchmark Evaluation Harness (84 Docs):** [docs/EVALUATION.md](docs/EVALUATION.md)
- **Guideline Health Intelligence:** [docs/GUIDELINE_HEALTH.md](docs/GUIDELINE_HEALTH.md)
- **Product Roadmap:** [docs/ROADMAP.md](docs/ROADMAP.md)
- **AI Usage & Disclosure:** [docs/AI_USAGE.md](docs/AI_USAGE.md)
- **Free Cloud Deployment Guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## Demo Accounts & Logins (`DEMO_MODE=true`)

The application comes pre-loaded with idempotent demonstration personas for the fictional skincare brand **Lumo**.  
Universal demo password: `LumoDemo2026!`

| Role | Demo Email | Access Tier | Primary Capabilities |
| :--- | :--- | :---: | :--- |
| **Creator (Social)** | `creator.social@lumo.internal` | `internal` | Submits marketing copy, accepts suggestions, dismisses findings |
| **Creator (Web)** | `creator.web@lumo.internal` | `internal` | Manages web articles, uploads DOCX/PDF guidelines |
| **Agency Creator** | `creator.agency@contractor.external` | `public` | Contractor clearance (restricted from confidential/internal guidelines) |
| **Reviewer 1** | `reviewer.sarah@lumo.internal` | `internal` | Claims reviewer queue, comments, requests changes, approves content |
| **Reviewer 2** | `reviewer.alex@lumo.internal` | `internal` | Provides second distinct approval on high-risk press releases |
| **Brand Manager** | `manager.kavita@lumo.internal` | `confidential` | Inspects Guideline Health ambiguity scores, approves rule gap proposals |
| **Administrator** | `admin@lumo.internal` | `confidential` | System settings, user RBAC management, resets demo database |

*One-click role switching is built directly into the header navigation (`Switch Role` dropdown).*

---

## 60-Second Interactive Tour

1. **Sign In**: Navigate to `/` and click the **Elena Chen (Creator - Social)** persona card for instant 1-click login.
2. **Submit Content**: Click **New Submission** in the top navigation or navigate to `/submissions/new`.
3. **Try a Sample**: In the "Try a sample" dropdown, select **Sample 1: Claim Violation**. Notice how title, channel, and copy are populated automatically.
4. **Run Review**: Click **Create Submission & Proceed** $\to$ **Run Brand Review**. Observe the deterministic 5-stage orchestration pipeline in action.
5. **Inspect & Fix Findings**: Notice the highlighted violations with cited guidelines. Click **Accept Fix** on the banned term violation (`serum` $\to$ `concentrate`) to generate **Version 2**.
6. **Submit for Sign-off**: Dismiss any remaining open high-severity findings with a reason code $\to$ click **Submit for Approval**.
7. **Switch to Reviewer**: Click **Switch Role** in the top-right header and select **Sarah Jenkins (Reviewer)**. Navigate to `/reviewer-queue`, claim the submission, and click **Approve**.
8. **Guideline Health**: Switch role to **Kavita Patel (Brand Manager)** and open **Guideline Health** (`/insights/guideline-health`) to explore ambiguity scores, stale rules, and approve draft rule proposals clustered from reviewer comments.

---

## Prerequisites

- **Python**: `3.12+` (tested and verified on Python 3.12, 3.13, and 3.14)
- **Node.js**: `v20+` or `v22+` LTS (npm included)
- **Git**
- *No Docker or Make required to run locally.*

---

## Clone-and-Run in 8 Commands

Inkguard runs out-of-the-box using embedded **SQLite WAL mode** with zero external services and zero API keys required:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/webug.git inkguard
cd inkguard

# 2. Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# 4. Initialize database schema and load idempotent brand seed data
python manage.py seed

# 5. Start backend (port 8000) and frontend (port 3000) dev servers
python manage.py dev
```

*Open [http://localhost:3000](http://localhost:3000) in your browser to start using Inkguard.*

---

## Optional Environment Variables

Create a `.env` file in the repository root to customize behavior:

```ini
# Application Environment (development, staging, production)
APP_ENV=development

# Database: SQLite locally, Neon PostgreSQL on cloud
DATABASE_URL=sqlite:///./data/inkguard.db
# DATABASE_URL=postgresql://user:pass@ep-cool-host.us-east-2.aws.neon.tech/neondb?sslmode=require

# Authentication & Demo Mode
JWT_SECRET=inkguard-insecure-dev-secret-change-in-production-1234567890
DEMO_MODE=true
DEMO_PASSWORD=LumoDemo2026!

# LLM Operating Mode: mock (default), cached, live, rules_only
LLM_MODE=mock
# LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
# LLM_API_KEY=AIzaSy...your-google-ai-studio-key
# LLM_MODEL=gemini-2.5-flash
# LLM_DAILY_CAP=100

# Optional Host OCR for Scanned Images (.png, .jpg)
# If Tesseract is not installed on the host, visual checks and Delta-E palette checks
# still run normally with graceful degradation ("OCR unavailable on this host").
# Ubuntu/Debian: sudo apt-get install -y tesseract-ocr
# macOS: brew install tesseract
```

---

## Testing & Quality Assurance

All test suites run via `python manage.py`:

```bash
# Run the complete test suite (147 automated tests: unit, integration, e2e, eval)
python manage.py test

# Run the 9 End-to-End User Journeys (J1 - J9)
python manage.py e2e

# Run E2E journeys against a running server or cloud deployment
python manage.py e2e --base-url https://inkguard.onrender.com

# Verify Clean Architecture boundaries with import-linter
python manage.py arch

# Run benchmark policy evaluation harness (84 ground-truth marketing copy documents)
python manage.py eval --mode rules_only --verifier off
python manage.py eval --mode cached --verifier on

# Build Next.js production static export
python manage.py build-frontend
```

---

## Deployment to Free Cloud (Neon + Render)

Inkguard is engineered for **100% free-tier cloud deployment** with no credit card required:
- **Neon Serverless PostgreSQL**: Permanent free tier, 1 GB storage, scales compute to zero on idle.
- **Render Web Service**: Hobby free plan serving both FastAPI API (`/api/v1`) and the Next.js static export (`/`) from a single origin.

Follow the step-by-step instructions in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Repository Layout

```
.
├── backend/
│   ├── alembic/              # Database migration versions
│   ├── app/
│   │   ├── adapters/         # DB models, LLM adapters, BM25 retriever, document extractors
│   │   ├── api/              # FastAPI routers, schemas, dependencies, RBAC
│   │   ├── application/      # Review orchestrator and workflow services
│   │   ├── domain/           # Pure Python: state machine, rule engine, a11y, verifier, insights
│   │   ├── eval/             # 84-document evaluation benchmark harness & runner
│   │   ├── ports/            # Abstract protocol interfaces
│   │   ├── prompts/          # Versioned prompt templates (analysis.v1.md, verify.v1.md)
│   │   └── seed/             # Lumo brand rules, facts, terms, and synthetic reviews
│   └── tests/
│       ├── architecture/     # Clean architecture contract linter
│       ├── e2e/              # End-to-end main journey test suite (J1 - J9)
│       ├── eval/             # Evaluation metrics and runner unit tests
│       ├── fixtures/         # Document (.docx, .pdf) and image (.png) fixtures
│       ├── integration/      # FastAPI TestClient API integration tests
│       └── unit/             # Pure domain unit tests
├── contracts/
│   └── openapi.json          # Exported OpenAPI 3.1 specification
├── docs/                     # Architecture, evaluation, deployment, roadmap, and evidence
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router pages (static export compatible)
│   │   ├── features/         # auth, findings, kb, submissions, queue
│   │   └── shared/           # ui, api, a11y, theme
│   └── out/                  # Pre-compiled static export bundle
└── manage.py                 # Cross-platform CLI runner (setup, dev, seed, test, e2e, arch, eval)
```

---

## Limitations

1. **Host OCR Binaries**: Text extraction from digital DOCX and PDF documents runs in pure Python out of the box. Text extraction from scanned raster images requires the host to have `tesseract-ocr` binaries installed; when absent, Inkguard executes visual brand checks and Delta-E palette distance with graceful notification.
2. **Free-Tier AI Rate Limits**: Live Google AI Studio calls are subject to 15 RPM free quotas. Inkguard enforces a configurable daily cap (`LLM_DAILY_CAP=100`) and provides an offline cache for zero-cost reproducible evaluations.
3. **Single-Brand Workspace**: The current demo environment is pre-configured for the Lumo skincare brand. Multi-brand workspace isolation is scheduled on the [Product Roadmap](docs/ROADMAP.md).
