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
  - `GET /api/v1/system/status`: AI provider status, daily quota, version
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
  - `PUT /api/v1/submissions/{id}/content`: Update text (creates new version)
  - `GET /api/v1/submissions/{id}/versions`: Version list
  - `GET /api/v1/submissions/{id}/diff`: Diff two versions
  - `POST /api/v1/submissions/{id}/review`: Trigger review pipeline
  - `GET /api/v1/reviews/{id}`: Review progress and stats
  - `GET /api/v1/reviews/{id}/boundary`: Data boundary telemetry
  - `POST /api/v1/submissions/{id}/submit`: Submit to reviewer queue
  - `POST /api/v1/submissions/{id}/claim`: Reviewer claims submission
  - `POST /api/v1/submissions/{id}/approve`: Reviewer approves version
  - `POST /api/v1/submissions/{id}/request-changes`: Reviewer requests edits
  - `POST /api/v1/submissions/{id}/mark-published`: Mark content as published
- **Findings**:
  - `GET /api/v1/submissions/{id}/findings`: List findings for active version
  - `POST /api/v1/findings/{id}/accept`: Apply suggested fix (creates new version)
  - `POST /api/v1/findings/{id}/dismiss`: Dismiss finding (reason required)
  - `POST /api/v1/findings/{id}/escalate`: Escalate finding to brand manager
- **Comments & Insights & Audit**:
  - `GET/POST /api/v1/submissions/{id}/comments`: Threaded discussions
  - `GET /api/v1/insights/summary`: Executive governance metrics
  - `GET /api/v1/insights/recurring`: Recurring issues by type/team/week
  - `GET /api/v1/insights/dismissals`: Dismissal & override breakdown
  - `GET /api/v1/insights/rules`: Raw per-rule counter analytics
  - `GET /api/v1/audit`: Append-only audit logs with hash chain verification
