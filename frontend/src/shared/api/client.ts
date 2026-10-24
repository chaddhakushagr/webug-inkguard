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
  AuditLogItem,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

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
  const url = `${API_BASE}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const token = typeof window !== "undefined" ? sessionStorage.getItem("inkguard_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
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
    throw new ApiError(0, "NETWORK_ERROR", err.message || "Network request failed");
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
  getSystemStatus: () => request<any>("/system/status"),
  getSettings: () => request<any>("/settings"),

  // Knowledge Base
  getKBEntries: (type?: string) =>
    request<KBEntry[]>(`/kb/entries${type ? `?type=${type}` : ""}`),
  getKBEntry: (id: string) => request<KBEntry>(`/kb/entries/${id}`),
  getKBEntryVersions: (id: string) => request<any[]>(`/kb/entries/${id}/versions`),

  // Submissions
  getSubmissions: (status?: string) =>
    request<Submission[]>(`/submissions${status ? `?status=${status}` : ""}`),
  getSubmission: (id: string) => request<Submission>(`/submissions/${id}`),
  createSubmission: (data: { title: string; channel: string; content: string; team_id?: string }) =>
    request<Submission>("/submissions", {
      method: "POST",
      body: JSON.stringify(data),
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
  approve: (id: string, note?: string) =>
    request<Submission>(`/submissions/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),
  requestChanges: (id: string, note: string) =>
    request<Submission>(`/submissions/${id}/request-changes`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),
  markPublished: (id: string, url?: string) =>
    request<Submission>(`/submissions/${id}/mark-published`, {
      method: "POST",
      body: JSON.stringify({ url }),
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

  // Insights & Audit
  getInsightsSummary: () => request<InsightsSummary>("/insights/summary"),
  getRecurringIssues: () => request<any[]>("/insights/recurring"),
  getDismissalsBreakdown: () => request<any[]>("/insights/dismissals"),
  getRuleCounters: () => request<any[]>("/insights/rules"),
  getAuditLog: () => request<AuditLogItem[]>("/audit"),
};
