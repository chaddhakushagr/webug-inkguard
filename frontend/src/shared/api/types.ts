// Generated / synchronized with contracts/openapi.json

export interface DemoUser {
  id: string;
  name: string;
  email: string;
  role: "creator" | "reviewer" | "brand_manager" | "admin";
  max_tier: "public" | "internal" | "confidential";
  team?: string | null;
  description: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: "creator" | "reviewer" | "brand_manager" | "admin";
  max_tier: "public" | "internal" | "confidential";
  team_id?: string | null;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface KBEntry {
  id: string;
  code: string;
  type: "term" | "fact" | "tone" | "rule" | "asset";
  title: string;
  body?: string | null;
  data: Record<string, any>;
  classification: "public" | "internal" | "confidential";
  owner_id?: string | null;
  status: "active" | "retired";
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface KBVersion {
  id: string;
  entry_id: string;
  version: number;
  snapshot: Record<string, any>;
  changed_by: string;
  change_note?: string | null;
  created_at: string;
}

export interface SubmissionVersion {
  id: string;
  submission_id: string;
  version_no: number;
  content: string;
  content_hash: string;
  created_by: string;
  source: string;
  created_at: string;
}

export interface Submission {
  id: string;
  title: string;
  channel: "social" | "email" | "blog" | "web" | "press_release";
  risk_tier: "low" | "medium" | "high";
  status: "Draft" | "Checked" | "Submitted" | "In Review" | "Changes Requested" | "Approved" | "Marked Published";
  creator_id: string;
  team_id?: string | null;
  current_version_id?: string | null;
  content: string;
  version_no: number;
  assignee_id?: string | null;
  published_url?: string | null;
  published_at?: string | null;
  is_synthetic: boolean;
  allowed_actions: string[];
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: string;
  review_id: string;
  submission_version_id: string;
  fingerprint: string;
  source: "rule" | "ai";
  issue_type: "terminology" | "tone" | "claim" | "missing_disclaimer" | "confidential_leak" | "accessibility" | "readability" | "general_note";
  severity: "low" | "medium" | "high";
  confidence: number;
  span_start: number;
  span_end: number;
  excerpt: string;
  cited_entry_id?: string | null;
  cited_entry_code?: string | null;
  cited_entry_version?: number | null;
  claim_verdict?: "Supported" | "Contradicted" | "Unverified" | "Expired" | null;
  is_policy: boolean;
  needs_human_judgment: boolean;
  explanation: string;
  suggested_fix?: string | null;
  verifier_verdict?: string | null;
  verifier_reason?: string | null;
  status: "open" | "accepted" | "dismissed" | "escalated";
  is_synthetic: boolean;
  created_at: string;
  allowed_actions?: string[];
}

export interface Review {
  id: string;
  submission_version_id: string;
  status: "pending" | "extracting" | "rule_checks" | "retrieving" | "analysing" | "finalising" | "completed" | "failed";
  mode: "live" | "cached" | "mock" | "rules_only";
  provider: string;
  model: string;
  prompt_version: string;
  stats?: {
    rules_evaluated?: number;
    kb_retrieved_count?: number;
    findings_count?: number;
    latency_ms?: number;
    [key: string]: any;
  };
  error?: string | null;
  fallback_reason?: string | null;
  started_at: string;
  finished_at?: string | null;
  findings_count: number;
}

export interface DataBoundary {
  review_id: string;
  external_calls_count: number;
  redaction_summary: Record<string, number>;
  tiers_sent: string[];
  confidential_data_sent: boolean;
  tokens_in: number;
  tokens_out: number;
  provider: string;
  model: string;
  purpose?: string | null;
  characters_sent?: number;
  entry_codes_included?: string[];
  highest_tier_sent?: string;
  cache_hit?: boolean;
  message?: string;
}

export interface Comment {
  id: string;
  submission_id: string;
  finding_id?: string | null;
  parent_id?: string | null;
  author_id: string;
  author_name: string;
  body: string;
  created_at: string;
}

export interface InsightsSummary {
  total_reviews: number;
  clean_submissions_pct: number;
  avg_findings_per_review: number;
  total_dismissals: number;
  avg_review_turnaround_hours: number;
  active_governance_rules: number;
  synthetic_reviews_count?: number;
  real_reviews_count?: number;
  is_synthetic_included?: boolean;
}

export interface RecurringIssue {
  issue_type: string;
  rule_code: string;
  rule_title: string;
  count: number;
  team_name: string;
  week: string;
  is_synthetic: boolean;
}

export interface DismissalBreakdown {
  reason_code: string;
  count: number;
  percentage: number;
}

export interface RuleCounter {
  rule_code: string;
  rule_title: string;
  times_triggered: number;
  times_dismissed: number;
  times_accepted: number;
  distinct_dismissers: number;
}

export interface SystemStatus {
  version: string;
  commit?: string;
  ai_mode: string;
  ai_provider: string;
  health?: string;
  daily_quota_limit: number;
  daily_calls_made: number;
  uptime_seconds: number;
  db_connected: boolean;
}

export interface AuditLogItem {
  id: string;
  ts: string;
  actor_id?: string | null;
  actor_role?: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, any>;
  request_id?: string | null;
  prev_hash?: string | null;
  hash: string;
}

export interface OverallMetrics {
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
}

export interface EvalSummary {
  total_documents: number;
  clean_documents: number;
  clean_documents_passed: number;
  clean_pass_rate: number;
  overall: OverallMetrics;
}

export interface CategoryMetrics {
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
}

export interface FalsePositiveItem {
  document_id: string;
  channel: string;
  cited_entry_code?: string | null;
  issue_type: string;
  excerpt: string;
  span: number[];
  claim_verdict?: string | null;
  explanation: string;
  confidence?: number | null;
  verifier_verdict?: string | null;
  verifier_reason?: string | null;
}

export interface BeforeAfterRow {
  mode: string;
  verifier: string;
  total_docs: number;
  clean_pass_rate: number;
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
}

export interface EvaluationReportResponse {
  summary: EvalSummary;
  before_after: BeforeAfterRow[];
  by_issue_type: Record<string, CategoryMetrics>;
  by_claim_verdict: Record<string, CategoryMetrics>;
  false_positives: FalsePositiveItem[];
  false_positives_count: number;
  metadata: Record<string, any>;
}


