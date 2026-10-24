# Security & Privacy Policy

## Invariants
1. **Tier Isolation**: Users with lower maximum classification tiers (e.g. `public` agency writers) cannot view or retrieve `internal` or `confidential` knowledge base entries.
2. **Confidential Egress Boundary**: Confidential entries are hard-filtered in both retrieval and LLM adapter layers. No confidential data ever leaves the machine to external LLMs.
3. **Synthetic Data Baseline**: All demonstrations use the fictional brand "Lumo". No real customer, personal, or proprietary data is stored.
4. **Append-Only Auditing**: Every state transition, comment, review run, and finding resolution is cryptographically hash-chained (`hash = sha256(prev_hash + payload)`).
5. **Prompt Injection Hardening**: Submissions are treated strictly as untrusted data wrapped in delimiters and inspected for system override phrasing.
6. **Rate Limiting & Egress Controls**: In-memory rate limiting and daily LLM quota enforcement prevent resource exhaustion.
