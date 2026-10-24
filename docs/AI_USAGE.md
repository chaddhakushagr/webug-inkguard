# AI Usage & Disclosure

## External AI Disclosure
- **Provider**: Google AI Studio (Free Tier) / OpenAI-compatible endpoint.
- **Model**: `gemini-2.5-flash` / `gemini-1.5-flash` (or local `mock` / `cached` when key is absent).
- **Data Policy Note**: The free tier of Google Gemini may store and review prompt inputs for product improvement. Therefore:
  - Inkguard strictly runs on synthetic brand data ("Lumo").
  - Content is redacted and masked prior to sending.
  - Zero confidential entries are transmitted outside the system.
  - An in-app AI disclosure badge is rendered on every AI-assisted finding and review screen.

## AI Modes
1. `live`: Connects to configured LLM endpoint if quota permits.
2. `cached`: Uses pre-recorded hash fixtures for demo samples.
3. `mock`: Fully deterministic offline fixture generator.
4. `rules_only`: Bypasses external calls entirely, running deterministic regex, term, and accessibility engines.
