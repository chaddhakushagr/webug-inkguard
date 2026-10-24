# System Architecture: Inkguard

## Overview
Inkguard is built as a modular monolith adhering to Clean Architecture / Ports and Adapters principles.
The backend enforces a strict one-way dependency direction:
```
api -> application -> domain
adapters -> ports (adapters implement domain ports)
```

## Directory Structure
```
backend/app/
  main.py            # App factory, middleware, static file serving
  config.py          # Pydantic Settings
  api/               # Routers, schemas, error envelope, RBAC dependencies
  application/       # Use cases (review orchestration, workflow, auth, kb, findings)
  domain/            # Pure Python: state machine, policies, rule engine, a11y, guardrails
  ports/             # Protocol interfaces: LLMClient, Retriever, Repositories, Clock, AuditSink
  adapters/          # Implementations: DB (SQLAlchemy), LLM, BM25 retriever, Security
  prompts/           # Versioned prompt templates (analysis.v1.md, suggest.v1.md)
  seed/              # Synthetic seed data for Lumo brand
contracts/
  openapi.json       # Generated OpenAPI spec
frontend/
  src/
    app/             # Next.js App Router (static export friendly)
    features/        # auth, kb, submissions, findings, comments, insights, audit, admin
    shared/          # ui, api, a11y, lib
```

## Import Linting Boundaries
The architecture is verified automatically via `import-linter` (`python manage.py arch`):
- `domain` must NEVER import from `application`, `adapters`, `api`, `sqlalchemy`, `fastapi`, `httpx`, or concrete `ports` implementations.
- `application` must NEVER import from `adapters` or `api`.
- `ports` defines abstract interfaces without database or web dependencies.
