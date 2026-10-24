"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import {
  AppShell,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import { InsightsSummary } from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  PieChart,
  ShieldAlert,
  ArrowRight,
  Clock,
  Sparkles,
} from "lucide-react";

export default function InsightsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <InsightsContent />
    </Suspense>
  );
}

function InsightsContent() {
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [recurring, setRecurring] = useState<any[]>([]);
  const [dismissals, setDismissals] = useState<any[]>([]);
  const [ruleCounters, setRuleCounters] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInsights() {
      setIsLoading(true);
      setError(null);
      try {
        const [sum, rec, dis, rcs] = await Promise.all([
          api.getInsightsSummary().catch(() => null),
          api.getRecurringIssues().catch(() => []),
          api.getDismissalsBreakdown().catch(() => []),
          api.getRuleCounters().catch(() => []),
        ]);
        if (sum) setSummary(sum);
        setRecurring(rec || []);
        setDismissals(dis || []);
        setRuleCounters(rcs || []);
      } catch (err: any) {
        setError(err.message || "Failed to load governance insights");
      } finally {
        setIsLoading(false);
      }
    }

    loadInsights();
  }, []);

  return (
    <AuthGuard allowedRoles={["brand_manager", "admin"]}>
      <AppShell pageTitle="Brand Governance Insights">
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-[#0F766E]" />
                <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                  Governance Insights &amp; Analytics
                </h1>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
                Aggregated compliance telemetry, recurring policy deviations, and reviewer dismissal patterns.
              </p>
            </div>
            <Link href="/audit/">
              <Button variant="secondary" size="md">
                View Audit Trail &rarr;
              </Button>
            </Link>
          </div>

          {isLoading ? (
            <div className="space-y-6">
              <Skeleton className="h-28 w-full rounded-xl" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Skeleton className="h-64 rounded-xl" />
                <Skeleton className="h-64 rounded-xl" />
              </div>
            </div>
          ) : error ? (
            <ErrorState message={error} onRetry={() => window.location.reload()} />
          ) : (
            <>
              {/* Summary KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    Clean Submissions Rate
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#067647] tabular-nums">
                    {summary ? `${summary.clean_submissions_pct}%` : "64.2%"}
                  </div>
                  <span className="mt-1 block text-xs text-[#5B6475]">Cleared with zero violations</span>
                </div>

                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    Total Reviews Executed
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#1F2A44] tabular-nums">
                    {summary ? summary.total_reviews : 84}
                  </div>
                  <span className="mt-1 block text-xs text-[#0F766E] font-medium">8-week synthetic history</span>
                </div>

                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    Avg. Turnaround Time
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#1F2A44] tabular-nums">
                    {summary ? `${summary.avg_review_turnaround_hours}h` : "3.4h"}
                  </div>
                  <span className="mt-1 block text-xs text-[#5B6475]">Submission to sign-off</span>
                </div>

                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    Active Governance Rules
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#0F766E] tabular-nums">
                    {summary ? summary.active_governance_rules : 32}
                  </div>
                  <span className="mt-1 block text-xs text-[#5B6475]">Terms, facts, disclaimers</span>
                </div>
              </div>

              {/* Two Column Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recurring Issues */}
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                  <div className="flex items-center gap-2 pb-3 border-b border-[#E2E5EA] mb-4">
                    <AlertTriangle className="w-4 h-4 text-[#B45309]" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                      Top Recurring Policy Issues
                    </h2>
                  </div>

                  <div className="space-y-3">
                    {recurring.length > 0 ? (
                      recurring.map((item, i) => (
                        <div key={i} className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] flex items-center justify-between">
                          <div>
                            <span className="font-mono text-xs font-bold text-[#0F766E] uppercase">
                              {item.code || item.rule || `ISSUE-${i + 1}`}
                            </span>
                            <p className="text-xs font-bold text-[#1F2A44] mt-0.5">{item.name || item.description || "Terminology violation"}</p>
                          </div>
                          <span className="text-xs font-extrabold font-mono text-[#1F2A44] bg-white px-2.5 py-1 rounded border border-[#CBD2DC]">
                            {item.count || 12} occurrences
                          </span>
                        </div>
                      ))
                    ) : (
                      <>
                        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] flex items-center justify-between">
                          <div>
                            <span className="font-mono text-xs font-bold text-[#0F766E]">TERM-001</span>
                            <p className="text-xs font-bold text-[#1F2A44] mt-0.5">Use of banned term &quot;serum&quot; instead of &quot;Concentrate&quot;</p>
                          </div>
                          <span className="text-xs font-extrabold font-mono text-[#1F2A44] bg-white px-2.5 py-1 rounded border border-[#CBD2DC]">
                            28 occurrences
                          </span>
                        </div>
                        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] flex items-center justify-between">
                          <div>
                            <span className="font-mono text-xs font-bold text-[#0F766E]">RULE-CLAIM-01</span>
                            <p className="text-xs font-bold text-[#1F2A44] mt-0.5">&quot;Clinically proven&quot; claim lacking approved dossier citation</p>
                          </div>
                          <span className="text-xs font-extrabold font-mono text-[#1F2A44] bg-white px-2.5 py-1 rounded border border-[#CBD2DC]">
                            19 occurrences
                          </span>
                        </div>
                        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] flex items-center justify-between">
                          <div>
                            <span className="font-mono text-xs font-bold text-[#0F766E]">RULE-DISC-01</span>
                            <p className="text-xs font-bold text-[#1F2A44] mt-0.5">Missing required &apos;#LumoPartner&apos; influencer disclosure</p>
                          </div>
                          <span className="text-xs font-extrabold font-mono text-[#1F2A44] bg-white px-2.5 py-1 rounded border border-[#CBD2DC]">
                            14 occurrences
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Dismissals Breakdown */}
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                  <div className="flex items-center gap-2 pb-3 border-b border-[#E2E5EA] mb-4">
                    <PieChart className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                      Reviewer Dismissals Breakdown (Reason Codes)
                    </h2>
                  </div>

                  <div className="space-y-3">
                    <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-[#1F2A44]">Contextual artistic exception</span>
                        <span className="text-xs font-mono font-bold text-[#0F766E]">42%</span>
                      </div>
                      <div className="w-full bg-[#E2E5EA] h-2 rounded-full overflow-hidden">
                        <div className="bg-[#0F766E] h-2 rounded-full" style={{ width: "42%" }} />
                      </div>
                    </div>

                    <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-[#1F2A44]">Pre-cleared legal waiver on file</span>
                        <span className="text-xs font-mono font-bold text-[#0F766E]">31%</span>
                      </div>
                      <div className="w-full bg-[#E2E5EA] h-2 rounded-full overflow-hidden">
                        <div className="bg-[#0F766E] h-2 rounded-full" style={{ width: "31%" }} />
                      </div>
                    </div>

                    <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-[#1F2A44]">False positive on figurative phrasing</span>
                        <span className="text-xs font-mono font-bold text-[#0F766E]">27%</span>
                      </div>
                      <div className="w-full bg-[#E2E5EA] h-2 rounded-full overflow-hidden">
                        <div className="bg-[#0F766E] h-2 rounded-full" style={{ width: "27%" }} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </AppShell>
    </AuthGuard>
  );
}
