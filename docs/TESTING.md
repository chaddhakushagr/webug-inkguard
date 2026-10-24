# Testing Strategy & Test Suites

## Hierarchy
1. **Domain Unit Tests** (`backend/tests/unit/`):
   - Fast, in-memory, zero database/network dependencies.
   - State machine validity transitions.
   - Guardrails, claim verdict evaluation, accessibility analyzers, and suggestion validators.
2. **API Integration Tests** (`backend/tests/integration/`):
   - FastAPI `TestClient` with in-memory SQLite.
   - RBAC enforcement, `allowed_actions`, and audit log creation.
   - Safety tests: confidential leak prevention, drop unverified citations, negative status codes (403, 409, 413, 422).
3. **Architecture Contract Tests** (`backend/tests/architecture/`):
   - `import-linter` contract verification via `python manage.py arch`.
4. **End-to-End Golden Path** (`backend/tests/e2e/`):
   - Automated script executing GP-1 through GP-8 against local or cloud URL.
