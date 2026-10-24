# AI Usage & Disclosure

## AI Assistance in Development
In accordance with hackathon rules, this codebase was built collaboratively with AI assistance (Google DeepMind Antigravity agentic coding assistant).
- **Architecture & Code Generation**: Antigravity generated the modular monolith structure, domain entities, pipeline stages, and test suites adhering strictly to the Clean Architecture boundaries specified in `AGENTS.md`.
- **Authoring & Verification**: All code, tests, and configuration files were verified with automated test suites (`pytest`), architecture linting (`import-linter`), and static build exports.

## External AI Services in the Product
- **Provider**: Google AI Studio (Free Tier) via its OpenAI-compatible endpoint.
- **Model**: `gemini-2.5-flash` (or local `mock` / `cached` when key is absent or daily cap is reached).
- **Free-Tier Data Policy Notice**:
  - The free tier of Google AI Studio may use inputs for model improvement and human evaluation.
  - To maintain absolute confidentiality and compliance:
    1. Inkguard uses exclusively synthetic brand data for the fictional skincare brand "Lumo".
    2. All PII, phone numbers, emails, and API keys are automatically redacted in `SanitiseStage` before transmission.
    3. Entries marked `confidential` are strictly barred from retrieval and egress by architectural assertions.
    4. An AI disclosure badge (`AIBadge`) and mode chip (`ModeChip`) are displayed on all screens where AI evaluation takes place.

## Product AI Operating Modes
1. `mock` (Default): Fully deterministic offline fixture generator. Zero network calls, zero API key required.
2. `cached`: Evaluates content against local cache keyed by `sha256(content|kb_codes|prompt_version|model)`. Falls back to rules-only on miss.
3. `live`: Connects to Google AI Studio or Ollama endpoint when `LLM_API_KEY` is provided and daily cap has not been exceeded.
4. `rules_only`: Bypasses external calls entirely, running deterministic rule checks, terminology matches, and accessibility evaluations.

## Third-Party Libraries & Licences
- `fastapi`, `uvicorn`, `starlette`: MIT License
- `sqlalchemy`, `alembic`: MIT License
- `pydantic`, `pydantic-settings`: MIT License
- `bcrypt`, `pyjwt`: Apache 2.0 / MIT License
- `httpx`: BSD 3-Clause License
- `import-linter`: BSD 2-Clause License
- `lucide-react`: ISC License
