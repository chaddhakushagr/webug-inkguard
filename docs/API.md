# API Reference

All API routes are served under `/api/v1`. Consistent error response format:
```json
{
  "code": "ERROR_CODE",
  "message": "Human readable explanation",
  "details": {}
}
```

## Route Index
- **Auth & System**:
  - `POST /api/v1/auth/login`: Authenticate and receive JWT
  - `GET /api/v1/auth/me`: Current user context and permissions
  - `GET /api/v1/auth/demo-users`: List of demo accounts
  - `GET /api/v1/health`: System health and readiness
  - `GET /api/v1/system/status`: AI provider status, daily quota, version (`0.2.0`), commit hash (`05fbbb2`), and health status
  - `GET /api/v1/settings`: Fetch current app settings
  - `PUT /api/v1/settings`: Update settings (admin only)
- **Users & Teams**:
  - `GET /api/v1/users`: List users (admin only)
  - `POST /api/v1/users`: Create user (admin only)
  - `PATCH /api/v1/users/{id}`: Modify user attributes
  - `GET /api/v1/teams`: List teams
- **Knowledge Base**:
  - `GET /api/v1/kb/entries`: Filtered by caller's classification tier
  - `POST /api/v1/kb/entries`: Create guideline / fact / rule (manager/admin)
  - `GET /api/v1/kb/entries/{id}`: Single entry details
  - `PUT /api/v1/kb/entries/{id}`: Update entry (creates version snapshot)
  - `POST /api/v1/kb/entries/{id}/retire`: Retire entry
  - `GET /api/v1/kb/entries/{id}/versions`: Version history
  - `POST /api/v1/kb/import/bulk`: Bulk import entries
- **Submissions & Workflow**:
  - `POST /api/v1/submissions`: Create submission
  - `GET /api/v1/submissions`: List submissions (role-filtered)
  - `GET /api/v1/submissions/{id}`: Detail view + `allowed_actions`
  - `PUT /api/v1/submissions/{id}/content`: Update text (creates new version, voids approvals, resets to Draft)
  - `GET /api/v1/submissions/{id}/versions`: Version list
  - `GET /api/v1/submissions/{id}/diff`: Diff two versions
  - `POST /api/v1/submissions/{id}/review`: Trigger review pipeline in background (supports `?sync=true` for testing). Returns review record immediately with progress status (`extracting`). Automatically transitions submission to `Checked` upon completion.
  - `GET /api/v1/reviews/{id}`: Fetch review progress, latency, findings count, error details, and `fallback_reason`.
  - `GET /api/v1/reviews/{id}/boundary`: Data boundary telemetry (provider, model, purpose, characters sent, redaction summary, entry codes included, highest tier sent, cache hit, and offline transparency notice).
  - `POST /api/v1/submissions/{id}/submit`: Submit to reviewer queue
  - `POST /api/v1/submissions/{id}/claim`: Reviewer claims submission
  - `POST /api/v1/submissions/{id}/approve`: Reviewer approves version (high-risk requires 2 approvals; returns 409 if not in `In Review`)
  - `POST /api/v1/submissions/{id}/request-changes`: Reviewer requests edits
  - `POST /api/v1/submissions/{id}/mark-published`: Mark content as published
- **Findings Triage**:
  - `GET /api/v1/submissions/{id}/findings`: List findings for submission active version with context-sensitive `allowed_actions` (`accept`, `dismiss`, `escalate`).
  - `POST /api/v1/findings/{id}/accept`: Apply suggested replacement. Creates a new submission content version, resets workflow state to `Draft`, voids prior approvals, and supersedes findings from older versions. Returns `409 Conflict` if the text span changed or if no suggestion exists.
  - `POST /api/v1/findings/{id}/dismiss`: Dismiss finding. Requires `reason_code` and `reason_text` in payload; returns `422 Unprocessable Entity` if either is omitted or empty.
  - `POST /api/v1/findings/{id}/escalate`: Escalate finding with a note. Posts a finding action, links an escalation comment, and updates finding status to `escalated`.
- **Comments & Discussions**:
  - `GET /api/v1/submissions/{id}/comments`: Threaded discussions
  - `POST /api/v1/submissions/{id}/comments`: Add threaded comment
- **Insights & Governance Analytics**:
  - `GET /api/v1/insights/summary`: Executive governance metrics aggregated over real data and labelled 8-week synthetic history across 4 teams (total reviews, clean submissions rate %, avg findings per review, total dismissals, turnaround hours, active rules, synthetic vs real breakdown).
  - `GET /api/v1/insights/recurring`: Recurring issues aggregated by issue type, rule code/title, team name, and ISO calendar week.
  - `GET /api/v1/insights/dismissals`: Reviewer dismissal and override reasons breakdown with occurrence counts and percentage distributions.
  - `GET /api/v1/insights/rules`: Per-rule raw performance counters (times triggered, times accepted, times dismissed, distinct dismissers). Labeled as "basic counters" without ambiguity scoring (Round 3 capability).
- **Audit Ledger**:
  - `GET /api/v1/audit`: Append-only audit logs with SHA-256 hash chain verification. Filterable via query parameters: `actor_id`, `action`, `entity_type`, `entity_id`, `from_date`, `to_date`. Restricted to managers and admins.
  - `GET /api/v1/audit/export`: CSV export of filtered audit records with headers `Timestamp (UTC)`, `Actor ID`, `Actor Role`, `Action`, `Entity Type`, `Entity ID`, `Details JSON`, and `SHA-256 Block Hash`. Restricted to managers and admins.

