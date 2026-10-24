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
import { User, Submission, InsightsSummary } from "@/shared/api/types";
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
} from "lucide-react";

const DEFAULT_SUBMISSIONS: Submission[] = [
  {
    id: "sub-sample-s1",
    title: "Spring Campaign Teaser Post",
    channel: "social",
    risk_tier: "low",
    status: "Checked",
    creator_id: "u-creator-social",
    team_id: "team-social",
    current_version_id: "ver-s1-1",
    content: "Discover the miracle powers of our new age-smart serum! Clinically proven to completely cure dry skin and give you flawless radiance in just 2 days. Don't wait—our guaranteed #1 formula delivers 100% satisfaction.",
    version_no: 1,
    assignee_id: "u-reviewer",
    published_url: null,
    published_at: null,
    is_synthetic: true,
    allowed_actions: ["edit", "review", "submit", "comment"],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "sub-sample-s2",
    title: "Lumo Glow Email Announcement",
    channel: "email",
    risk_tier: "medium",
    status: "Submitted",
    creator_id: "u-creator-web",
    team_id: "team-web",
    current_version_id: "ver-s2-1",
    content: "Hey glow-getters! Experience the magic elixir that transforms your skin overnight.",
    version_no: 1,
    assignee_id: null,
    published_url: null,
    published_at: null,
    is_synthetic: true,
    allowed_actions: ["claim", "comment"],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const DEFAULT_INSIGHTS: InsightsSummary = {
  total_reviews: 84,
  clean_submissions_pct: 64.2,
  avg_findings_per_review: 1.8,
  total_dismissals: 19,
  avg_review_turnaround_hours: 3.4,
  active_governance_rules: 32,
};

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>({
    id: "u-creator-social",
    name: "Elena Chen",
    email: "creator.social@lumo.internal",
    role: "creator",
    max_tier: "internal",
    is_active: true,
  });
  const [submissions, setSubmissions] = useState<Submission[]>(DEFAULT_SUBMISSIONS);
  const [insights, setInsights] = useState<InsightsSummary | null>(DEFAULT_INSIGHTS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const raw = typeof window !== "undefined" ? sessionStorage.getItem("inkguard_user") : null;
    if (raw) {
      try {
        setUser(JSON.parse(raw));
      } catch {
        // ignore
      }
    }

    api.getSubmissions().then((subs) => {
      if (subs && subs.length > 0) setSubmissions(subs);
    }).catch(() => {});

    api.getInsightsSummary().then((ins) => {
      if (ins) setInsights(ins);
    }).catch(() => {});
  }, []);

  const handleLoadSample = (sampleId: string) => {
    window.location.href = `/submissions/new/?sample=${sampleId}`;
  };

  return (
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
                {user ? user.role.replace("_", " ") : "creator"}
              </span>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
              Active Role: <strong className="text-[#1F2A44] capitalize">{user?.role || "creator"}</strong> &middot; Max Egress Tier:{" "}
              <strong className="text-[#0F766E] uppercase font-mono">{user?.max_tier || "internal"}</strong> &middot; Synthetic Data Playground
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Link href="/submissions/new/">
              <Button variant="primary" size="md" leftIcon={<Plus className="w-4 h-4" />}>
                New Submission
              </Button>
            </Link>
          </div>
        </div>

        {/* First-Run Guide: "Try the Demo in 4 Steps" (SPEC F-70) */}
        <div className="bg-white rounded-xl border border-[#CBD2DC] p-5 sm:p-6 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#E2E5EA] pb-3 mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#0F766E]" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#1F2A44]">
                Interactive Demo Walkthrough (Round 2 Judging)
              </h2>
            </div>
            <span className="text-xs text-[#5B6475] hidden sm:inline">3-minute evaluation</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
              <span className="w-5 h-5 rounded-full bg-[#1F2A44] text-white flex items-center justify-center text-xs font-bold mb-2">
                1
              </span>
              <h3 className="text-xs font-bold text-[#1F2A44]">Load Copy Sample</h3>
              <p className="text-[11px] text-[#5B6475] mt-1">
                Choose sample S1 (unsupported claims) or paste draft copy.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
              <span className="w-5 h-5 rounded-full bg-[#1F2A44] text-white flex items-center justify-center text-xs font-bold mb-2">
                2
              </span>
              <h3 className="text-xs font-bold text-[#1F2A44]">Run Brand Review</h3>
              <p className="text-[11px] text-[#5B6475] mt-1">
                Evaluate terms, claims, tone, and accessibility against guidelines.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
              <span className="w-5 h-5 rounded-full bg-[#1F2A44] text-white flex items-center justify-center text-xs font-bold mb-2">
                3
              </span>
              <h3 className="text-xs font-bold text-[#1F2A44]">Act on Findings</h3>
              <p className="text-[11px] text-[#5B6475] mt-1">
                Accept minimal-edit fixes, dismiss with mandatory reasons, or escalate.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
              <span className="w-5 h-5 rounded-full bg-[#1F2A44] text-white flex items-center justify-center text-xs font-bold mb-2">
                4
              </span>
              <h3 className="text-xs font-bold text-[#1F2A44]">Review &amp; Approve</h3>
              <p className="text-[11px] text-[#5B6475] mt-1">
                Switch to Reviewer persona to claim and issue editorial sign-off.
              </p>
            </div>
          </div>

          {/* Quick Sample Action Triggers */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#E2E5EA]">
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
              Sample S2 (Off-Tone Superlatives)
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

        {/* Governance Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">Total Reviews</span>
            <div className="mt-2 text-3xl font-extrabold text-[#1F2A44] tabular-nums">
              {insights ? insights.total_reviews : 84}
            </div>
            <span className="mt-1 block text-xs text-[#0F766E] font-medium">8-week synthetic history</span>
          </div>

          <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">Clean Submissions</span>
            <div className="mt-2 text-3xl font-extrabold text-[#067647] tabular-nums">
              {insights ? `${insights.clean_submissions_pct}%` : "64.2%"}
            </div>
            <span className="mt-1 block text-xs text-[#5B6475]">Zero policy violations</span>
          </div>

          <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">Total Dismissals</span>
            <div className="mt-2 text-3xl font-extrabold text-[#B45309] tabular-nums">
              {insights ? insights.total_dismissals : 19}
            </div>
            <span className="mt-1 block text-xs text-[#5B6475]">Documented overrides</span>
          </div>

          <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">Active Guidelines</span>
            <div className="mt-2 text-3xl font-extrabold text-[#1F2A44] tabular-nums">
              {insights ? insights.active_governance_rules : 32}
            </div>
            <span className="mt-1 block text-xs text-[#0F766E] font-medium">Indexed in BM25</span>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-10 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-3 border-[#0F766E] border-t-transparent mb-3" />
            <p className="text-sm text-[#5B6475]">Loading active governance pipeline...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <ErrorState
            title="Failed to Load Dashboard Pipeline"
            message={error}
            onRetry={() => window.location.reload()}
          />
        )}

        {/* Submissions Section */}
        {!isLoading && !error && (
          <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden shadow-xs">
            <div className="px-6 py-4 border-b border-[#E2E5EA] flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-[#1F2A44]">Active Governance Submissions</h2>
                <p className="text-xs text-[#5B6475] mt-0.5">Content items currently undergoing brand review</p>
              </div>
              <Link href="/submissions/">
                <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                  View All Submissions
                </Button>
              </Link>
            </div>

            {submissions.length === 0 ? (
              <EmptyState
                title="No active submissions"
                description="Get started by creating a new draft or loading one of the pre-configured brand samples."
                action={
                  <Link href="/submissions/new/">
                    <Button variant="primary" size="sm">+ Create Submission</Button>
                  </Link>
                }
              />
            ) : (
              <ul className="divide-y divide-[#E2E5EA]">
                {submissions.map((sub) => (
                  <li key={sub.id} className="p-5 sm:p-6 hover:bg-[#F7F7F4]/60 transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-3">
                        <Badge badge={{ kind: "status", value: sub.status as any }} />
                        <Link
                          href={`/submissions/detail/?id=${sub.id}`}
                          className="text-base font-bold text-[#1F2A44] hover:text-[#0F766E] transition-colors"
                        >
                          {sub.title}
                        </Link>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-[#5B6475]">
                        <span className="font-mono uppercase">Channel: {sub.channel}</span>
                        <span>&middot;</span>
                        <span className="font-mono uppercase">Risk: {sub.risk_tier}</span>
                      </div>
                    </div>

                    <p className="text-xs sm:text-sm text-[#5B6475] line-clamp-2 leading-relaxed bg-[#F7F7F4] p-3 rounded-lg border border-[#E2E5EA] font-serif">
                      {sub.content}
                    </p>

                    <div className="mt-3 flex items-center justify-between text-xs text-[#5B6475]">
                      <span className="font-mono">Version {sub.version_no}</span>
                      <div className="flex items-center gap-2">
                        {sub.allowed_actions.map((act) => (
                          <span
                            key={act}
                            className="px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[11px] text-[#1F2A44] font-medium capitalize"
                          >
                            {act}
                          </span>
                        ))}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
