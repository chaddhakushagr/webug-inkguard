# Known Limitations

1. **Client-Side Token Storage**: JWT tokens are stored in `sessionStorage` for demo simplicity. Mitigated via strict HTML escaping, CSP headers, and short token expiration (15 minutes).
2. **Synchronous Polling vs WebSockets**: Background reviews use interval-based client polling (`GET /api/v1/reviews/{id}`) rather than WebSockets or Celery workers to avoid heavy infrastructure dependencies on free tiers.
3. **In-Process BM25 Scale**: Lexical BM25 index is built in-memory. Ideal for up to 10,000 guidelines, fitting typical enterprise brand playbooks without vector database overhead.
4. **Single Approver Multi-Role Override**: While creators cannot approve their own submissions, an admin user can act as both creator and reviewer across different submissions.
5. **Mobile Viewport Split View**: On viewports under 640px, the submission detail screen uses stacked tabs ("Content" and "Findings") rather than side-by-side split pane to prevent horizontal cramping. Clicking an inline highlight switches to the Findings tab and scrolls smoothly to the target card.
6. **Client-Side Notification Toasts**: Action feedback toasts are maintained in volatile client state for high responsiveness; durable change history is preserved in the cryptographic Audit Ledger.
7. **Synthetic History Labels**: 8-week seeded synthetic history entries are flagged via `is_synthetic=True` in SQLite/Postgres and indicated with monospace tags in the UI; analytical counters merge live and synthetic records transparently.
