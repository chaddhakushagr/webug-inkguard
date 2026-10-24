# Inkguard: Pre-Publication Brand Governance Platform

Team WeBug | TechCircuit Hackathon Round 2

Inkguard is an automated brand governance platform that checks pre-publication marketing and product content against approved brand guidelines, facts, tone rules, and asset registries. It explains every finding with a cited source, generates intent-preserving minimal-edit suggestions, and ensures humans retain full editorial control.

## Quick Links
- **Live Deployment:** [TBD - Post Gate G3 Deployment]
- **AI & Data Boundary Disclosure:** See [docs/AI_USAGE.md](docs/AI_USAGE.md) and [docs/SECURITY_PRIVACY.md](docs/SECURITY_PRIVACY.md)
- **Architecture Overview:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Round 2 Submission Pack:** [docs/SUBMISSION_R2.md](docs/SUBMISSION_R2.md)

## Team
- **Sparsh** - Backend Lead (Domain, Application, API, Database, Workflows)
- **Kushagra** - AI/Governance Lead (Pipelines, LLM Integration, Guardrails, Retrieval)
- **Apurrv** - Frontend Lead (UI/UX, Dashboards, Review Studio, Accessibility)

## Demo Accounts (DEMO_MODE=true)
Default password: `LumoDemo2026!` (configured via `DEMO_PASSWORD`)
- **Creator (Team Social):** `creator.social@lumo.internal` (Tier: Internal)
- **Creator (Team Web):** `creator.web@lumo.internal` (Tier: Internal)
- **Agency Creator:** `creator.agency@contractor.external` (Tier: Public)
- **Reviewer:** `reviewer.sarah@lumo.internal` (Tier: Internal)
- **Brand Manager:** `manager.elena@lumo.internal` (Tier: Confidential)
- **Administrator:** `admin@lumo.internal` (Tier: Confidential)

## Running Locally

### Prerequisites
- Python 3.12+ (tested on Python 3.14)
- Node.js LTS (v20+ / v22+)
- Git

### Setup and Start
```bash
# 1. Setup virtualenv, install python/node dependencies, run migrations and seed database
python manage.py setup

# 2. Run backend (port 8000) and frontend (port 3000) concurrently
python manage.py dev
```

### Other Commands
```bash
python manage.py test           # Run all unit and integration tests
python manage.py arch           # Run import-linter architecture boundary tests
python manage.py seed           # Idempotent seed loading
python manage.py warm-cache     # Warm cache for sample fixtures
python manage.py openapi        # Export contracts/openapi.json and update frontend types
python manage.py build-frontend # Build Next.js static export
python manage.py e2e            # Run end-to-end golden path verification
```
