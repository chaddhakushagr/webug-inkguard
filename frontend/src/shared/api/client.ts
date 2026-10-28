import {
  AuthResponse,
  DemoUser,
  User,
  KBEntry,
  Submission,
  Finding,
  Review,
  DataBoundary,
  Comment,
  InsightsSummary,
  RecurringIssue,
  DismissalBreakdown,
  RuleCounter,
  SystemStatus,
  AuditLogItem,
  EvaluationReportResponse,
  GuidelineHealthItem,
  StaleRuleResponse,
  GapProposalResponse,
  GapActionResponse,
  NotificationItem,
} from "./types";

let hasCompletedFirstRequest = false;

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    // In production (Render, Docker, or any port other than Next.js dev server 3000),
    // use same-origin /api/v1 with zero CORS.
    if (window.location.port !== "3000") {
      return "/api/v1";
    }
  }
  return process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";
}

class ApiError extends Error {
  code: string;
  details?: any;
  status: number;

  constructor(status: number, code: string, message: string, details?: any) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const apiBase = getApiBase();
  const url = `${apiBase}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  let token = typeof window !== "undefined" ? sessionStorage.getItem("inkguard_token") : null;
  if (!token && typeof window !== "undefined" && sessionStorage.getItem("inkguard_logout") !== "true") {
    const params = new URLSearchParams(window.location.search);
    const demoParam = params.get("demo") || "creator";
    const demoId =
      demoParam === "manager"
        ? "u-manager"
        : demoParam === "admin"
        ? "u-admin"
        : demoParam === "reviewer"
        ? "u-reviewer"
        : demoParam === "agency"
        ? "u-creator-agency"
        : "u-creator-social";
    token = `demo-token-${demoId}`;
    sessionStorage.setItem("inkguard_token", token);
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let coldStartTimer: any = null;
  let didTriggerColdStart = false;

  if (!hasCompletedFirstRequest && typeof window !== "undefined") {
    coldStartTimer = setTimeout(() => {
      didTriggerColdStart = true;
      window.dispatchEvent(
        new CustomEvent("inkguard:cold_start", {
          detail: { waking: true, message: "Waking the server, this can take about a minute" },
        })
      );
    }, 2000);
  }

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errBody: any = {};
      try {
        errBody = await res.json();
      } catch {
        errBody = { message: res.statusText };
      }
      if (res.status === 401) {
        if (typeof window !== "undefined") {
          sessionStorage.removeItem("inkguard_token");
          window.dispatchEvent(
            new CustomEvent("inkguard:unauthorized", {
              detail: { message: errBody.message || "Your session has expired. Please sign in again." },
            })
          );
        }
      }
      throw new ApiError(
        res.status,
        errBody.code || `HTTP_${res.status}`,
        errBody.message || "An error occurred",
        errBody.details
      );
    }
    return (await res.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    const isNetwork =
      err?.name === "TypeError" ||
      err?.message === "Failed to fetch" ||
      err?.message?.toLowerCase().includes("fetch") ||
      err?.message?.toLowerCase().includes("network");
    const readableMsg = isNetwork
      ? "Unable to reach the Inkguard backend API. Please ensure the server is running at http://localhost:8000."
      : err?.message || "Network request failed";
    throw new ApiError(0, "NETWORK_ERROR", readableMsg);
  } finally {
    if (coldStartTimer) clearTimeout(coldStartTimer);
    if (didTriggerColdStart && typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("inkguard:cold_start", {
          detail: { waking: false, message: "Server is awake and ready" },
        })
      );
    }
    hasCompletedFirstRequest = true;
  }
}

export const api = {
  // Auth & System
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getDemoUsers: () => request<DemoUser[]>("/auth/demo-users"),
  getMe: () => request<User>("/auth/me"),
  getHealth: () => request<{ status: string; version: string; ai_mode: string }>("/health"),
  getSystemStatus: () => request<SystemStatus>("/system/status"),
  getSettings: () => request<any>("/settings"),

  // Knowledge Base
  getKBEntries: (type?: string, status?: string, classification?: string, expiringSoonOnly?: boolean) => {
    const params = new URLSearchParams();
    if (type && type !== "all") params.append("type", type);
    if (status && status !== "all") params.append("status", status);
    if (classification && classification !== "all") params.append("classification", classification);
    if (expiringSoonOnly) params.append("expiring_soon_only", "true");
    const qs = params.toString();
    return request<KBEntry[]>(`/kb/entries${qs ? `?${qs}` : ""}`);
  },
  getKBEntry: (id: string) => request<KBEntry>(`/kb/entries/${id}`),
  createKBEntry: (entry: { code: string; type: string; title: string; body?: string; data?: any; classification: string }) =>
    request<KBEntry>("/kb/entries", { method: "POST", body: JSON.stringify(entry) }),
  updateKBEntry: (id: string, entry: { title?: string; body?: string; data?: any; classification?: string; change_note?: string }) =>
    request<KBEntry>(`/kb/entries/${id}`, { method: "PUT", body: JSON.stringify(entry) }),
  retireKBEntry: (id: string) =>
    request<KBEntry>(`/kb/entries/${id}/retire`, { method: "POST" }),
  getKBEntryVersions: (id: string) => request<any[]>(`/kb/entries/${id}/versions`),

  // Submissions
  getSubmissions: (status?: string, channel?: string, riskTier?: string) => {
    const params = new URLSearchParams();
    if (status && status !== "all") params.append("status", status);
    if (channel && channel !== "all") params.append("channel", channel);
    if (riskTier && riskTier !== "all") params.append("risk_tier", riskTier);
    const qs = params.toString();
    return request<Submission[]>(`/submissions${qs ? `?${qs}` : ""}`);
  },
  getSubmission: (id: string) => request<Submission>(`/submissions/${id}`),
  createSubmission: (data: { title: string; channel: string; content: string; team_id?: string }) =>
    request<Submission>("/submissions", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  uploadSubmission: (formData: FormData) =>
    request<Submission>("/submissions/upload", {
      method: "POST",
      body: formData,
    }),
  updateContent: (id: string, content: string) =>
    request<Submission>(`/submissions/${id}/content`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
  getVersions: (id: string) => request<any[]>(`/submissions/${id}/versions`),
  getDiff: (id: string, fromV: number, toV: number) =>
    request<any>(`/submissions/${id}/diff?from=${fromV}&to=${toV}`),

  // Workflow
  submit: (id: string) => request<Submission>(`/submissions/${id}/submit`, { method: "POST" }),
  claim: (id: string) => request<Submission>(`/submissions/${id}/claim`, { method: "POST" }),
  unclaim: (id: string) => request<Submission>(`/submissions/${id}/unclaim`, { method: "POST" }),
  approve: (id: string, note?: string) =>
    request<Submission>(`/submissions/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ note: note || "Editorial review approval" }),
    }),
  requestChanges: (id: string, note: string) =>
    request<Submission>(`/submissions/${id}/request-changes`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),
  markPublished: (id: string, url?: string) =>
    request<Submission>(`/submissions/${id}/mark-published`, {
      method: "POST",
      body: JSON.stringify({ url: url || "https://brand.lumo.skincare/published" }),
    }),

  // Review & Findings
  triggerReview: (submissionId: string) =>
    request<Review>(`/submissions/${submissionId}/review`, { method: "POST" }),
  getReview: (reviewId: string) => request<Review>(`/reviews/${reviewId}`),
  getReviewBoundary: (reviewId: string) => request<DataBoundary>(`/reviews/${reviewId}/boundary`),
  getFindings: (submissionId: string) =>
    request<Finding[]>(`/submissions/${submissionId}/findings`),
  acceptFinding: (findingId: string) =>
    request<Finding>(`/findings/${findingId}/accept`, { method: "POST" }),
  dismissFinding: (findingId: string, reasonCode: string, reasonText: string) =>
    request<Finding>(`/findings/${findingId}/dismiss`, {
      method: "POST",
      body: JSON.stringify({ reason_code: reasonCode, reason_text: reasonText }),
    }),
  escalateFinding: (findingId: string, note?: string) =>
    request<Finding>(`/findings/${findingId}/escalate`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),

  // Comments
  getComments: (submissionId: string) =>
    request<Comment[]>(`/submissions/${submissionId}/comments`),
  postComment: (submissionId: string, body: string, findingId?: string, parentId?: string) =>
    request<Comment>(`/submissions/${submissionId}/comments`, {
      method: "POST",
      body: JSON.stringify({ body, finding_id: findingId, parent_id: parentId }),
    }),

  // Insights, Audit & Status
  getInsightsSummary: () => request<InsightsSummary>("/insights/summary"),
  getRecurringIssues: () => request<RecurringIssue[]>("/insights/recurring"),
  getDismissalsBreakdown: () => request<DismissalBreakdown[]>("/insights/dismissals"),
  getRuleCounters: () => request<RuleCounter[]>("/insights/rules"),
  getAuditLog: (params?: {
    actor_id?: string;
    action?: string;
    entity_type?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.actor_id) qs.append("actor_id", params.actor_id);
    if (params?.action && params.action !== "all") qs.append("action", params.action);
    if (params?.entity_type && params.entity_type !== "all") qs.append("entity_type", params.entity_type);
    if (params?.from_date) qs.append("from_date", params.from_date);
    if (params?.to_date) qs.append("to_date", params.to_date);
    if (params?.limit) qs.append("limit", String(params.limit));
    const query = qs.toString();
    return request<AuditLogItem[]>(`/audit${query ? `?${query}` : ""}`);
  },
  getAuditExportUrl: (params?: {
    actor_id?: string;
    action?: string;
    entity_type?: string;
    from_date?: string;
    to_date?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.actor_id) qs.append("actor_id", params.actor_id);
    if (params?.action && params.action !== "all") qs.append("action", params.action);
    if (params?.entity_type && params.entity_type !== "all") qs.append("entity_type", params.entity_type);
    if (params?.from_date) qs.append("from_date", params.from_date);
    if (params?.to_date) qs.append("to_date", params.to_date);
    const query = qs.toString();
    return `${getApiBase()}/audit/export${query ? `?${query}` : ""}`;
  },

  // Evaluation Benchmarks & Metrics
  getEvaluationResults: () => request<EvaluationReportResponse>("/evaluation/results"),

  // Guideline Health (Improvement 2)
  getGuidelineHealth: () => request<GuidelineHealthItem[]>("/insights/guideline-health"),
  getStaleRules: () => request<StaleRuleResponse[]>("/insights/stale"),
  getGapProposals: () => request<GapProposalResponse[]>("/insights/gaps"),
  approveGapProposal: (gapId: string) =>
    request<GapActionResponse>(`/insights/gaps/${gapId}/approve`, { method: "POST" }),
  rejectGapProposal: (gapId: string, reason: string) =>
    request<GapActionResponse>(`/insights/gaps/${gapId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  // In-App Notifications (F-26)
  getNotifications: () => request<NotificationItem[]>("/notifications"),
  markNotificationRead: (id: string) =>
    request<NotificationItem>(`/notifications/${id}/read`, { method: "POST" }),
  markAllNotificationsRead: () =>
    request<{ status: string; marked_read: number }>("/notifications/read-all", { method: "POST" }),

  // Admin / Demo Reset (F-67 / G-13)
  resetDemo: () => request<{ status: string; message: string }>("/admin/reset-demo", { method: "GET" }),
  resetDemoPost: () => request<{ status: string; message: string }>("/admin/reset-demo", { method: "POST" }),
};

