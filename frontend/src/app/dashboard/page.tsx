"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  AppShell,
  Badge,
  Button,
  Card,
  CardHeader,
  CardContent,
  EmptyState,
  ErrorState,
  Skeleton,
  Banner,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import { User, Submission, InsightsSummary, KBEntry } from "@/shared/api/types";
import {
  Plus,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Clock,
  BookOpen,
  FileText,
  AlertTriangle,
  Play,
  CheckSquare,
  BarChart3,
  Shield,
  Eye,
  AlertCircle,
  Calendar,
  X,
} from "lucide-react";
import { AuthGuard } from "@/features/auth/AuthGuard";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window !== "undefined") {
      const raw = sessionStorage.getItem("inkguard_user");
      if (raw) {
        try {
          return JSON.parse(raw);
        } catch {
          // ignore
        }
      }
    }
    return {
      id: "u-creator-social",
      name: "Elena Chen",
      email: "creator.social@lumo.internal",
      role: "creator",
      max_tier: "internal",
      team_id: "Team Social",
      is_active: true,
    };
  });

  const [submissions, setSubmissions] = useState<Submission[]>([
    {
      id: "sub-sample-s1",
      title: "S1: Spring Hydration Campaign (Unsupported & Contradicted Claims)",
      channel: "social",
      risk_tier: "low",
      status: "Checked",
      creator_id: "u-creator-social",
      team_id: "Team Social",
      current_version_id: "ver-s1-1",
      content:
        "Discover the miracle powers of our new age-smart serum! Clinically proven to completely cure dry skin and give you flawless radiance in just 2 days.",
      version_no: 1,
      assignee_id: "u-reviewer-1",
      published_url: null,
      published_at: null,
      is_synthetic: true,
      allowed_actions: ["edit", "submit", "review"],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "sub-sample-s2",
      title: "S2: Product Teaser Email (Off-Tone Copy)",
      channel: "email",
      risk_tier: "medium",
      status: "Draft",
      creator_id: "u-creator-social",
      team_id: "Team Social",
      current_version_id: "ver-s2-1",
      content:
        "Hey tired glow-getters! Your damaged face is crying out for an urgent intervention.",
      version_no: 1,
      assignee_id: null,
      published_url: null,
      published_at: null,
      is_synthetic: true,
      allowed_actions: ["edit", "submit"],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);

  const [insights, setInsights] = useState<InsightsSummary | null>({
    total_reviews: 84,
    clean_submissions_pct: 64.2,
    avg_findings_per_review: 1.8,
    total_dismissals: 19,
    avg_review_turnaround_hours: 3.4,
    active_governance_rules: 32,
  });

  const [expiringFacts, setExpiringFacts] = useState<KBEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGuideDismissed, setIsGuideDismissed] = useState<boolean>(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const dismissed = localStorage.getItem("inkguard_first_run_dismissed") === "true";
      setIsGuideDismissed(dismissed);
    }
  }, []);

  const handleDismissGuide = () => {
    setIsGuideDismissed(true);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("inkguard_first_run_dismissed", "true");
      } catch {}
    }
  };

  useEffect(() => {
    // 1. Sync user from session
    if (typeof window !== "undefined") {
      const raw = sessionStorage.getItem("inkguard_user");
      if (raw) {
        try {
          setUser(JSON.parse(raw));
        } catch {
          // ignore
        }
      }
    }

    // 2. Load submissions, insights, and expiring facts from API
    async function loadDashboardData() {
      setIsLoading(true);
      setError(null);
      try {
        const [subs, ins, facts] = await Promise.all([
          api.getSubmissions().catch(() => []),
          api.getInsightsSummary().catch(() => null),
          api.getKBEntries("fact", "active", undefined, true).catch(() => []),
        ]);
        setSubmissions(subs || []);
        if (ins) setInsights(ins);
        setExpiringFacts(facts || []);
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const role = user?.role || "creator";
  const isCreator = role === "creator";
  const isReviewer = role === "reviewer";
  const isManagerOrAdmin = role === "brand_manager" || role === "admin";

  // Data subsets for role views
  const myDrafts = submissions.filter((s) => s.status === "Draft" && s.creator_id === user?.id);
  const itemsNeedingAction = submissions.filter(
    (s) => (s.status === "Changes Requested" || s.status === "Checked") && s.creator_id === user?.id
  );
  const unassignedQueue = submissions.filter((s) => s.status === "Submitted");
  const myClaimedItems = submissions.filter(
    (s) => s.status === "In Review" && (s.assignee_id === user?.id || !s.assignee_id)
  );

  // Status counts for Manager & Admin
  const statusCounts = {
    Draft: submissions.filter((s) => s.status === "Draft").length,
    Checked: submissions.filter((s) => s.status === "Checked").length,
    Submitted: submissions.filter((s) => s.status === "Submitted").length,
    InReview: submissions.filter((s) => s.status === "In Review").length,
    ChangesRequested: submissions.filter((s) => s.status === "Changes Requested").length,
    Approved: submissions.filter((s) => s.status === "Approved").length,
    MarkedPublished: submissions.filter((s) => s.status === "Marked Published").length,
  };

  // User submissions for first-run evaluation
  const userSubmissions = submissions.filter((s) => s.creator_id === user?.id);
  const showFirstRunGuide = !isLoading && userSubmissions.length === 0 && !isGuideDismissed;

  const handleLoadSample = (sampleId: string) => {
    window.location.href = `/submissions/new/?sample=${sampleId}`;
  };

  return (
    <AuthGuard>
      <AppShell pageTitle="Brand Governance Dashboard">
        <div className="space-y-8">
          {/* User Greeting & Persona Banner */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                  Welcome, {user ? user.name : "Brand Collaborator"}
                </h1>
                <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#F7F7F4] text-[#1F2A44] border border-[#CBD2DC] font-semibold">
                  {role.replace("_", " ")}
                </span>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
                Active Role: <strong className="text-[#1F2A44] capitalize">{role.replace("_", " ")}</strong> &middot; Max Egress Tier:{" "}
                <strong className="text-[#0F766E] uppercase font-mono">{user?.max_tier || "internal"}</strong> &middot; Synthetic Data Playground
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              {isCreator && (
                <Link href="/submissions/new/">
                  <Button variant="primary" size="md" leftIcon={<Plus className="w-4 h-4" />}>
                    New Submission
                  </Button>
                </Link>
              )}
              {isReviewer && (
                <Link href="/queue/">
                  <Button variant="primary" size="md" leftIcon={<CheckSquare className="w-4 h-4" />}>
                    Open Reviewer Queue
                  </Button>
                </Link>
              )}
              {isManagerOrAdmin && (
                <div className="flex items-center gap-2">
                  <Link href="/kb/">
                    <Button variant="secondary" size="md" leftIcon={<BookOpen className="w-4 h-4" />}>
                      Manage KB
                    </Button>
                  </Link>
                  <Link href="/insights/">
                    <Button variant="primary" size="md" leftIcon={<BarChart3 className="w-4 h-4" />}>
                      View Insights
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* First-Run Guide Welcome Card (Phase 7.1) */}
          {showFirstRunGuide && (
            <div
              id="first-run-welcome-card"
              role="region"
              aria-label="Welcome and first-run guide"
              className="relative overflow-hidden bg-gradient-to-br from-white via-[#F0FDFA]/40 to-[#F7F7F4] rounded-2xl border-2 border-[#0F766E]/40 p-6 sm:p-8 shadow-sm"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
                <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0F766E]/10 text-[#0F766E] text-xs font-bold uppercase tracking-wider mb-2 border border-[#0F766E]/20">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>First-Run Guide</span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold text-[#1F2A44] tracking-tight">
                    Submit content &rarr; Review findings &rarr; Approve or fix
                  </h2>
                  <p className="text-xs sm:text-sm text-[#5B6475] mt-1 max-w-2xl">
                    Get started with automated pre-publication brand governance. Evaluate your marketing copy against brand tone, banned terms, and clinical claim verification in three simple steps:
                  </p>
                </div>
                <button
                  type="button"
                  id="dismiss-first-run-guide-btn"
                  onClick={handleDismissGuide}
                  className="px-3 py-1.5 rounded-lg border border-[#CBD2DC] bg-white hover:bg-[#F7F7F4] text-xs font-semibold text-[#5B6475] hover:text-[#1F2A44] transition-colors flex items-center gap-1.5 flex-shrink-0 shadow-xs"
                  title="Dismiss this guide permanently"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Dismiss permanently</span>
                </button>
              </div>

              {/* Three-Step Flow */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Step 1: Submit Content */}
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5 shadow-xs flex flex-col justify-between hover:border-[#0F766E] transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="w-8 h-8 rounded-full bg-[#0F766E] text-white flex items-center justify-center font-bold text-sm shadow-xs">
                        1
                      </span>
                      <span className="text-[10px] font-mono font-bold uppercase text-[#0F766E] px-2 py-0.5 rounded bg-[#F0FDFA] border border-[#ABEFC6]">
                        Step 1
                      </span>
                    </div>
                    <h3 className="font-bold text-sm text-[#1F2A44] mb-1.5">
                      Submit content
                    </h3>
                    <p className="text-xs text-[#5B6475] leading-relaxed">
                      Paste marketing copy directly or upload a document (.docx, .pdf) or image (.png, .jpg) to begin pre-publication governance.
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E2E5EA]">
                    <Link href="/submissions/new/">
                      <Button variant="primary" size="sm" className="w-full justify-center">
                        Start New Submission &rarr;
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Step 2: Review Findings */}
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5 shadow-xs flex flex-col justify-between hover:border-[#0F766E] transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="w-8 h-8 rounded-full bg-[#1F2A44] text-white flex items-center justify-center font-bold text-sm shadow-xs">
                        2
                      </span>
                      <span className="text-[10px] font-mono font-bold uppercase text-[#1F2A44] px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC]">
                        Step 2
                      </span>
                    </div>
                    <h3 className="font-bold text-sm text-[#1F2A44] mb-1.5">
                      Review findings
                    </h3>
                    <p className="text-xs text-[#5B6475] leading-relaxed">
                      Automated pipeline scans against brand tone guidelines, banned terms, accessibility contrast, and cited clinical evidence.
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E2E5EA]">
                    <span className="text-xs font-semibold text-[#5B6475] block text-center">
                      Every finding cites exact sources
                    </span>
                  </div>
                </div>

                {/* Step 3: Approve or Fix */}
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5 shadow-xs flex flex-col justify-between hover:border-[#0F766E] transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="w-8 h-8 rounded-full bg-[#067647] text-white flex items-center justify-center font-bold text-sm shadow-xs">
                        3
                      </span>
                      <span className="text-[10px] font-mono font-bold uppercase text-[#067647] px-2 py-0.5 rounded bg-[#ECFDF3] border border-[#ABEFC6]">
                        Step 3
                      </span>
                    </div>
                    <h3 className="font-bold text-sm text-[#1F2A44] mb-1.5">
                      Approve or fix
                    </h3>
                    <p className="text-xs text-[#5B6475] leading-relaxed">
                      Accept 1-click suggested replacements, dismiss with documented rationale, or advance through reviewer workflow stages.
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E2E5EA]">
                    <span className="text-xs font-semibold text-[#067647] block text-center">
                      Human in the loop always
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {error && <ErrorState message={error} onRetry={() => window.location.reload()} />}

          {/* ========================================================================= */}
          {/* ROLE 1: CREATOR VIEW                                                      */}
          {/* ========================================================================= */}
          {isCreator && (
            <div className="space-y-8">
              {/* First-Run Checklist: "Try the Demo in 4 Steps" */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-5 sm:p-6 shadow-xs">
                <div className="flex items-center justify-between border-b border-[#E2E5EA] pb-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-sm font-bold uppercase tracking-wider text-[#1F2A44]">
                      Try the Demo in 4 Steps (Creator Evaluation)
                    </h2>
                  </div>
                  <span className="text-xs text-[#5B6475] hidden sm:inline">Progress: 1 of 4 Completed</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div className="p-3.5 rounded-lg bg-[#0F766E]/5 border border-[#0F766E]/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="w-5 h-5 rounded-full bg-[#0F766E] text-white flex items-center justify-center text-xs font-bold">
                        1
                      </span>
                      <span className="text-[10px] font-bold uppercase text-[#0F766E]">Active</span>
                    </div>
                    <h3 className="text-xs font-bold text-[#1F2A44]">Load Copy Sample</h3>
                    <p className="text-[11px] text-[#5B6475] mt-1">
                      Choose sample S1 (unsupported claims) or paste your own draft copy.
                    </p>
                  </div>

                  <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
                    <span className="w-5 h-5 rounded-full bg-[#CBD2DC] text-[#1F2A44] flex items-center justify-center text-xs font-bold mb-2">
                      2
                    </span>
                    <h3 className="text-xs font-bold text-[#1F2A44]">Run Brand Review</h3>
                    <p className="text-[11px] text-[#5B6475] mt-1">
                      Evaluate terms, claims, tone, and accessibility against approved facts.
                    </p>
                  </div>

                  <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
                    <span className="w-5 h-5 rounded-full bg-[#CBD2DC] text-[#1F2A44] flex items-center justify-center text-xs font-bold mb-2">
                      3
                    </span>
                    <h3 className="text-xs font-bold text-[#1F2A44]">Act on Findings</h3>
                    <p className="text-[11px] text-[#5B6475] mt-1">
                      Accept minimal-edit fixes, dismiss with mandatory reasons, or escalate.
                    </p>
                  </div>

                  <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
                    <span className="w-5 h-5 rounded-full bg-[#CBD2DC] text-[#1F2A44] flex items-center justify-center text-xs font-bold mb-2">
                      4
                    </span>
                    <h3 className="text-xs font-bold text-[#1F2A44]">Submit for Approval</h3>
                    <p className="text-[11px] text-[#5B6475] mt-1">
                      Send cleared submission to the reviewer queue for final editorial sign-off.
                    </p>
                  </div>
                </div>

                {/* 3 Quick Sample Content Buttons */}
                <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-[#E2E5EA]">
                  <span className="text-xs font-semibold text-[#5B6475] mr-1">One-Click Test Samples:</span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleLoadSample("S1")}
                    leftIcon={<Play className="w-3.5 h-3.5 text-[#0F766E]" />}
                  >
                    Sample S1 (Unsupported Claims &amp; Banned Terms)
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleLoadSample("S2")}
                    leftIcon={<Play className="w-3.5 h-3.5 text-[#0F766E]" />}
                  >
                    Sample S2 (Off-Tone Copy)
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleLoadSample("S4")}
                    leftIcon={<Play className="w-3.5 h-3.5 text-[#0F766E]" />}
                  >
                    Sample S4 (Confidential Leak Check)
                  </Button>
                </div>
              </div>

              {/* Items Needing Action Table */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden">
                <div className="p-5 border-b border-[#E2E5EA] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-[#B45309]" />
                    <h2 className="text-sm font-bold uppercase tracking-wider text-[#1F2A44]">
                      Items Needing Action ({itemsNeedingAction.length})
                    </h2>
                  </div>
                  <span className="text-xs text-[#5B6475]">Requires review action or revisions</span>
                </div>

                {isLoading ? (
                  <div className="p-6 space-y-3">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : itemsNeedingAction.length === 0 ? (
                  <div className="p-8 text-center text-xs text-[#5B6475]">
                    No submissions currently blocked or pending your action.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                          <th className="py-2.5 px-4">Title</th>
                          <th className="py-2.5 px-4">Channel</th>
                          <th className="py-2.5 px-4">Risk Tier</th>
                          <th className="py-2.5 px-4">Status</th>
                          <th className="py-2.5 px-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E2E5EA]">
                        {itemsNeedingAction.map((s) => (
                          <tr key={s.id} className="hover:bg-[#F7F7F4]/60">
                            <td className="py-3 px-4 font-bold text-[#1F2A44]">{s.title}</td>
                            <td className="py-3 px-4 font-mono capitalize">{s.channel}</td>
                            <td className="py-3 px-4">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                s.risk_tier === "high" ? "bg-[#FEF3F2] text-[#B42318]" : "bg-[#F7F7F4] text-[#1F2A44]"
                              }`}>
                                {s.risk_tier}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <Badge status={s.status} />
                            </td>
                            <td className="py-3 px-4 text-right">
                              <Link href={`/submission/?id=${s.id}`}>
                                <Button variant="secondary" size="xs">
                                  Review Item
                                </Button>
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* My Drafts Table */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden">
                <div className="p-5 border-b border-[#E2E5EA] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-sm font-bold uppercase tracking-wider text-[#1F2A44]">
                      My Drafts ({myDrafts.length})
                    </h2>
                  </div>
                  <Link href="/submissions/">
                    <Button variant="ghost" size="xs">
                      View All Submissions &rarr;
                    </Button>
                  </Link>
                </div>

                {isLoading ? (
                  <div className="p-6 space-y-3">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : myDrafts.length === 0 ? (
                  <div className="p-8 text-center text-xs text-[#5B6475]">
                    No active drafts. Click &quot;New Submission&quot; or choose a test sample above.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                          <th className="py-2.5 px-4">Title</th>
                          <th className="py-2.5 px-4">Channel</th>
                          <th className="py-2.5 px-4">Version</th>
                          <th className="py-2.5 px-4">Status</th>
                          <th className="py-2.5 px-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E2E5EA]">
                        {myDrafts.map((s) => (
                          <tr key={s.id} className="hover:bg-[#F7F7F4]/60">
                            <td className="py-3 px-4 font-bold text-[#1F2A44]">{s.title}</td>
                            <td className="py-3 px-4 font-mono capitalize">{s.channel}</td>
                            <td className="py-3 px-4 font-mono">v{s.version_no}</td>
                            <td className="py-3 px-4">
                              <Badge status={s.status} />
                            </td>
                            <td className="py-3 px-4 text-right">
                              <Link href={`/submission/?id=${s.id}`}>
                                <Button variant="secondary" size="xs">
                                  Edit &amp; Check
                                </Button>
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* ROLE 2: REVIEWER VIEW                                                     */}
          {/* ========================================================================= */}
          {isReviewer && (
            <div className="space-y-8">
              {/* Reviewer KPI Overview */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    Unassigned Queue
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#1F2A44] tabular-nums">
                    {unassignedQueue.length}
                  </div>
                  <span className="mt-1 block text-xs text-[#0F766E] font-medium">Awaiting editorial claim</span>
                </div>

                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    My Claimed Items
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#0F766E] tabular-nums">
                    {myClaimedItems.length}
                  </div>
                  <span className="mt-1 block text-xs text-[#5B6475]">In Review state</span>
                </div>

                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    Average Turnaround
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#1F2A44] tabular-nums">
                    {insights ? `${insights.avg_review_turnaround_hours}h` : "3.4h"}
                  </div>
                  <span className="mt-1 block text-xs text-[#5B6475]">Target &lt; 4.0h</span>
                </div>
              </div>

              {/* My Claimed Items Table */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden">
                <div className="p-5 border-b border-[#E2E5EA] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckSquare className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-sm font-bold uppercase tracking-wider text-[#1F2A44]">
                      My Claimed Reviews ({myClaimedItems.length})
                    </h2>
                  </div>
                  <Link href="/queue/">
                    <Button variant="primary" size="xs">
                      Claim Next Item &rarr;
                    </Button>
                  </Link>
                </div>

                {isLoading ? (
                  <div className="p-6 space-y-3">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : myClaimedItems.length === 0 ? (
                  <div className="p-8 text-center text-xs text-[#5B6475]">
                    You have no claimed submissions in review. Open the Reviewer Queue to claim an unassigned submission.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                          <th className="py-2.5 px-4">Title</th>
                          <th className="py-2.5 px-4">Channel</th>
                          <th className="py-2.5 px-4">Risk Tier</th>
                          <th className="py-2.5 px-4">Status</th>
                          <th className="py-2.5 px-4 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E2E5EA]">
                        {myClaimedItems.map((s) => (
                          <tr key={s.id} className="hover:bg-[#F7F7F4]/60">
                            <td className="py-3 px-4 font-bold text-[#1F2A44]">{s.title}</td>
                            <td className="py-3 px-4 font-mono capitalize">{s.channel}</td>
                            <td className="py-3 px-4">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                s.risk_tier === "high" ? "bg-[#FEF3F2] text-[#B42318]" : "bg-[#F7F7F4] text-[#1F2A44]"
                              }`}>
                                {s.risk_tier}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <Badge status={s.status} />
                            </td>
                            <td className="py-3 px-4 text-right">
                              <Link href={`/submission/?id=${s.id}`}>
                                <Button variant="primary" size="xs">
                                  Complete Review
                                </Button>
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* ROLE 3: MANAGER & ADMIN VIEW                                              */}
          {/* ========================================================================= */}
          {isManagerOrAdmin && (
            <div className="space-y-8">
              {/* Status Distribution Counts */}
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#5B6475] mb-3">
                  Workflow Status Distribution
                </h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                  <div className="bg-white rounded-lg border border-[#CBD2DC] p-3 text-center">
                    <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Draft</span>
                    <span className="text-2xl font-extrabold text-[#1F2A44] mt-1 block">{statusCounts.Draft}</span>
                  </div>
                  <div className="bg-white rounded-lg border border-[#CBD2DC] p-3 text-center">
                    <span className="text-[10px] font-bold uppercase text-[#0F766E] block">Checked</span>
                    <span className="text-2xl font-extrabold text-[#0F766E] mt-1 block">{statusCounts.Checked}</span>
                  </div>
                  <div className="bg-white rounded-lg border border-[#CBD2DC] p-3 text-center">
                    <span className="text-[10px] font-bold uppercase text-[#1F2A44] block">Submitted</span>
                    <span className="text-2xl font-extrabold text-[#1F2A44] mt-1 block">{statusCounts.Submitted}</span>
                  </div>
                  <div className="bg-white rounded-lg border border-[#CBD2DC] p-3 text-center">
                    <span className="text-[10px] font-bold uppercase text-[#0F766E] block">In Review</span>
                    <span className="text-2xl font-extrabold text-[#0F766E] mt-1 block">{statusCounts.InReview}</span>
                  </div>
                  <div className="bg-white rounded-lg border border-[#CBD2DC] p-3 text-center">
                    <span className="text-[10px] font-bold uppercase text-[#B42318] block">Changes Req.</span>
                    <span className="text-2xl font-extrabold text-[#B42318] mt-1 block">{statusCounts.ChangesRequested}</span>
                  </div>
                  <div className="bg-white rounded-lg border border-[#CBD2DC] p-3 text-center">
                    <span className="text-[10px] font-bold uppercase text-[#067647] block">Approved</span>
                    <span className="text-2xl font-extrabold text-[#067647] mt-1 block">{statusCounts.Approved}</span>
                  </div>
                  <div className="bg-white rounded-lg border border-[#CBD2DC] p-3 text-center">
                    <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Published</span>
                    <span className="text-2xl font-extrabold text-[#5B6475] mt-1 block">{statusCounts.MarkedPublished}</span>
                  </div>
                </div>
              </div>

              {/* Expiring Facts Alert Box */}
              <div className="bg-[#FFFBEB] rounded-xl border border-[#FDE68A] p-5 shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-[#B45309]" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-[#B45309]">
                      Expiring &amp; Expired Facts Alert ({expiringFacts.length})
                    </h2>
                  </div>
                  <Link href="/kb/?type=fact">
                    <span className="text-xs font-semibold text-[#B45309] hover:underline">
                      View all in KB &rarr;
                    </span>
                  </Link>
                </div>

                <p className="text-xs text-[#92400E] mb-3">
                  Claims citing expired facts automatically receive an &quot;Expired&quot; verdict by code guardrails.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {expiringFacts.slice(0, 3).map((f) => {
                    const validUntil = f.data?.valid_until || "Expired";
                    return (
                      <div key={f.id} className="p-3 bg-white rounded-lg border border-[#FDE68A]">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-mono text-xs font-bold text-[#1F2A44]">{f.code}</span>
                          <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-[#FEF3F2] text-[#B42318]">
                            Expired
                          </span>
                        </div>
                        <p className="text-xs text-[#1F2A44] font-medium line-clamp-1">{f.title}</p>
                        <p className="text-[11px] text-[#5B6475] mt-1">Valid Until: {validUntil}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Quick Jump to Insights & Audit Log */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 bg-white border border-[#CBD2DC] rounded-xl flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-[#1F2A44]">Brand Governance Insights</h3>
                    <p className="text-xs text-[#5B6475] mt-1">
                      Inspect clean submission rates, recurring issue breakdown, and rule dismissals.
                    </p>
                  </div>
                  <Link href="/insights/">
                    <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                      Open Insights
                    </Button>
                  </Link>
                </div>

                <div className="p-5 bg-white border border-[#CBD2DC] rounded-xl flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-[#1F2A44]">Cryptographic Audit Trail</h3>
                    <p className="text-xs text-[#5B6475] mt-1">
                      Verify append-only hash chains, review execution traces, and state transitions.
                    </p>
                  </div>
                  <Link href="/audit/">
                    <Button variant="secondary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                      Open Audit Log
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </AppShell>
    </AuthGuard>
  );
}
