# Completed Features Tracking Table

| ID | Feature | Tier | Status | How a Judge Verifies It | Evidence / Notes |
|---|---|---|---|---|---|
| F-01 | Email and password login, JWT with short expiry, hashed passwords, `/auth/me` | M | Planned | Log in via API or UI with credentials | |
| F-02 | One-click demo login per role (DEMO_MODE) and synthetic demo banner | M | Planned | Click role buttons on login page | |
| F-03 | Server-side RBAC, tier filtering, `allowed_actions` | M | Planned | Inspect `/submissions/{id}` payload for `allowed_actions` | |
| F-04 | User management by admin | C | Planned | Admin settings tab | |
| F-05 | Teams | M | Planned | Team assignment on users and submissions | |
| F-10 | Knowledge-base entries (create, edit, retire) | M | Planned | KB dashboard view and mutations | |
| F-11 | Immutable versions, history view, review recording | M | Planned | Edit a KB entry and inspect versions table | |
| F-12 | Classification tiers on every entry | M | Planned | Public writer blocked from confidential entries | |
| F-13 | Fact validity dates, "expiring soon" and "expired" badges | M | Planned | Badges displayed on KB entry cards | |
| F-14 | Guideline document import (.txt/.md heuristic) | C | Planned | Heuristic candidate parser | |
| F-15 | Terminology: banned, preferred, match type, severity | M | Planned | Run review with banned term "serum" | |
| F-16 | Bulk JSON import and seed loader | M | Planned | `python manage.py seed` loads 50+ entries | |
| F-20 | Create submission: title, channel, text, auto risk tier | M | Planned | Create post with high-risk channel | |
| F-21 | Content versions with inline diff | M | Planned | View diff tab on submission screen | |
| F-22 | State machine with 409 on invalid transitions | M | Planned | Attempt unauthorized status jump | |
| F-23 | Risk tiers and approvals (1 low/medium, 2 high) | M | Planned | High risk requires 2 distinct approvers | |
| F-24 | Threaded comments on submission and findings | M | Planned | Post comment on finding span | |
| F-25 | Reviewer queue with claim | M | Planned | Claim submission in reviewer dashboard | |
| F-26 | In-app notifications | C | Planned | Alert on state changes | |
| F-27 | Mark Published by a human, optional URL | M | Planned | Mark published after final approval | |
| F-28 | Append-only hash-chained audit log with filterable UI | M | Planned | Audit viewer verifying SHA256 chain | |
| F-29 | Role-specific dashboard | M | Planned | Distinct widgets for Creator, Reviewer, Manager | |
| F-30 | Review orchestration as background job / polled progress | M | Planned | Polling review status with progress indicator | |
| F-31 | Sanitise and redact before external call, redaction log | M | Planned | Verify redaction log count and type | |
| F-32 | Prompt-injection hardening and flagging | M | Planned | Review sample S5 and observe safety flag | |
| F-33 | Rule checks: terms, disclaimers, regex, confidential leak | M | Planned | Verify rule-based findings badges | |
| F-34 | Text accessibility & readability metrics | M | Planned | Reading score & ALL-CAPS flagged | |
| F-35 | Retrieval: in-process BM25 over knowledge base | M | Planned | Tier-filtered guideline relevance ranking | |
| F-36 | LLM analysis returning strict JSON | M | Planned | Semantic claims & tone evaluation | |
| F-37 | Guardrails in code (citations & substring check) | M | Planned | Hallucinated citation pruned by engine | |
| F-38 | Minimal-edit suggestions with change cap | M | Planned | Suggestion diff < 60% span replacement | |
| F-39 | LLM adapter (live, cached, mock, rules_only) | M | Planned | Switch modes via settings or env | |
| F-40 | Response cache table and `warm-cache` command | M | Planned | Cache hit flag on repeated queries | |
| F-41 | Data-boundary log per external call | M | Planned | Review boundary tab reveals payload metadata | |
| F-42 | Versioned prompt files | M | Planned | Prompts saved in `prompts/` | |
| F-43 | Findings model with rich classification | M | Planned | Cards with type, severity, confidence | |
| F-44 | Finding actions: accept, dismiss, escalate | M | Planned | Accept applies fix, dismiss logs reason | |
| F-45 | Re-check carrying over dismissed findings | C | Planned | Fingerprint preserved across runs | |
| F-46 | Highlighted findings in content, keyboard operable | M | Planned | Click text highlight to focus finding card | |
| F-50 | Recurring issues analytics by type, rule, team, week | M | Planned | Visual trend charts on Insights page | |
| F-51 | Dismissal and override reasons breakdown | M | Planned | Pie/bar breakdown of dismissal rationales | |
| F-52 | Per-rule raw counters | S | Planned | Rule trigger frequency counts | |
| F-53 | Synthetic history seed (80 reviews, 8 weeks) | M | Planned | Pre-populated historical trendlines | |
| F-60 | AI-disclosure badge and "About AI" page | M | Planned | Header badge and dedicated disclosure route | |
| F-61 | Rule findings and AI findings visually distinct | M | Planned | Green/Blue badge styling distinction | |
| F-62 | Data-boundary panel on review screen | M | Planned | Dedicated boundary telemetry tab | |
| F-63 | Admin egress policy and "no external AI" switch | M | Planned | Instant killswitch to `rules_only` | |
| F-64 | Security basics (CSP, rate limiting, escaping) | M | Planned | HTTP security headers and sanitization | |
| F-66 | Daily cap on live LLM calls with automatic fallback | M | Planned | Cap counter threshold triggers fallback | |
| F-67 | Admin "reset demo data" | C | Planned | One-click seed restoration | |
| F-70 | First-run guide, 5 sample submissions, empty states | M | Planned | Samples S1..S5 one-click loader | |
| F-71 | Accessible, responsive UI (WCAG 2.1 AA) | M | Planned | Screen-reader friendly, 4.5:1 contrast | |
| F-72 | Loading, empty and error states everywhere | M | Planned | Verified across all feature screens | |
| F-73 | Status page: version, AI mode, health | S | Planned | `/system/status` diagnostic view | |
| F-80 | Tests: domain unit, API integration, golden-path e2e | M | Planned | `python manage.py test` passes | |
| F-82 | Local run via `python manage.py` | M | Planned | Zero make/docker setup works | |
| F-83 | Health endpoint, request ids, structured logs | S | Planned | `/health` endpoint & UUID correlation ids | |
| F-85 | Architecture tests with import-linter | M | Planned | `python manage.py arch` passes | |
| F-86 | Free-cloud deployment (Neon + Render) | M | Planned | Public URL live verification | |
