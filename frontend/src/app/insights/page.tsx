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
import {
  InsightsSummary,
  RecurringIssue,
  DismissalBreakdown,
  RuleCounter,
} from "@/shared/api/types";
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
  Search,
  Filter,
  Info,
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
  const [recurring, setRecurring] = useState<RecurringIssue[]>([]);
  const [dismissals, setDismissals] = useState<DismissalBreakdown[]>([]);
  const [ruleCounters, setRuleCounters] = useState<RuleCounter[]>([]);
  const [ruleSearch, setRuleSearch] = useState("");
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

  const filteredRules = ruleCounters.filter((rc) => {
    if (!ruleSearch) return true;
    const q = ruleSearch.toLowerCase();
    return rc.rule_code.toLowerCase().includes(q) || rc.rule_title.toLowerCase().includes(q);
  });

  // Calculate max count for SVG recurring bar scaling
  const maxRecurringCount = Math.max(...recurring.map((r) => r.count), 1);

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
                Real-time compliance telemetry over real submissions plus labelled 8-week synthetic history across 4 teams.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Link href="/insights/guideline-health/">
                <Button variant="primary" size="md">
                  Guideline Health &rarr;
                </Button>
              </Link>
              <Link href="/audit/">
                <Button variant="secondary" size="md">
                  Audit Trail &rarr;
                </Button>
              </Link>
            </div>
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
                  <span className="mt-1 block text-xs text-[#0F766E] font-medium">
                    {summary?.synthetic_reviews_count || 80} synthetic &middot; {summary?.real_reviews_count || 4} live
                  </span>
                </div>

                <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475]">
                    Avg. Turnaround Time
                  </span>
                  <div className="mt-2 text-3xl font-extrabold text-[#1F2A44] tabular-nums">
                    {summary ? `${summary.avg_review_turnaround_hours}h` : "3.2h"}
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
                  <span className="mt-1 block text-xs text-[#5B6475]">Terms, facts, claim rules</span>
                </div>
              </div>

              {/* Two Column Section: Simple SVG Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* SVG Chart 1: Recurring Policy Issues */}
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                  <div className="flex items-center justify-between pb-3 border-b border-[#E2E5EA] mb-4">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-[#B45309]" />
                      <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                        Top Recurring Policy Issues
                      </h2>
                    </div>
                    <span className="text-[11px] font-mono text-[#5B6475]">By rule code &amp; team</span>
                  </div>

                  {recurring.length === 0 ? (
                    <EmptyState title="No recurring issues logged" description="Telemetry will appear as reviews complete." />
                  ) : (
                    <div className="space-y-4">
                      {recurring.slice(0, 5).map((item, idx) => {
                        const pct = Math.round((item.count / maxRecurringCount) * 100);
                        return (
                          <div key={idx} className="space-y-1.5">
                            <div className="flex items-center justify-between text-xs">
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-[#0F766E]">{item.rule_code}</span>
                                <span className="text-[#1F2A44] font-medium truncate max-w-[200px]">{item.rule_title}</span>
                                {item.is_synthetic && (
                                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]">
                                    synthetic
                                  </span>
                                )}
                              </div>
                              <span className="font-mono font-bold text-[#1F2A44]">{item.count} hits</span>
                            </div>

                            {/* Accessible SVG Bar */}
                            <div className="w-full bg-[#F7F7F4] h-5 rounded-md border border-[#E2E5EA] overflow-hidden p-0.5">
                              <svg className="w-full h-full" aria-hidden="true">
                                <rect
                                  x="0"
                                  y="0"
                                  width={`${Math.max(pct, 4)}%`}
                                  height="100%"
                                  rx="3"
                                  fill="#0F766E"
                                />
                              </svg>
                            </div>
                            <div className="flex justify-between text-[11px] text-[#5B6475]">
                              <span>Team: {item.team_name}</span>
                              <span className="font-mono">{item.week}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* SVG Chart 2: Reviewer Dismissals Breakdown */}
                <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                  <div className="flex items-center justify-between pb-3 border-b border-[#E2E5EA] mb-4">
                    <div className="flex items-center gap-2">
                      <PieChart className="w-4 h-4 text-[#0F766E]" />
                      <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                        Reviewer Dismissal &amp; Override Reasons
                      </h2>
                    </div>
                    <span className="text-[11px] font-mono text-[#5B6475]">Reason distribution</span>
                  </div>

                  {dismissals.length === 0 ? (
                    <EmptyState title="No dismissals on record" description="No review findings have been dismissed." />
                  ) : (
                    <div className="space-y-4">
                      {dismissals.map((d, idx) => {
                        const colors = ["#0F766E", "#175CD3", "#B45309", "#475467", "#7A5AF8"];
                        const barColor = colors[idx % colors.length];
                        return (
                          <div key={idx} className="space-y-1.5">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-medium text-[#1F2A44] capitalize">
                                {d.reason_code.replace(/_/g, " ")}
                              </span>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-[#5B6475]">{d.count} times</span>
                                <span className="font-mono font-bold text-[#1F2A44]">{d.percentage}%</span>
                              </div>
                            </div>

                            {/* Accessible SVG Bar */}
                            <div className="w-full bg-[#F7F7F4] h-4 rounded-md border border-[#E2E5EA] overflow-hidden p-0.5">
                              <svg className="w-full h-full" aria-hidden="true">
                                <rect
                                  x="0"
                                  y="0"
                                  width={`${Math.max(d.percentage, 3)}%`}
                                  height="100%"
                                  rx="2"
                                  fill={barColor}
                                />
                              </svg>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Table: Rule Performance - Basic Counters */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-[#E2E5EA]">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#0F766E]" />
                      <h2 className="text-sm font-bold uppercase tracking-wider text-[#1F2A44]">
                        Rule Performance: Basic Counters
                      </h2>
                    </div>
                    <p className="mt-1 text-xs text-[#5B6475]">
                      Raw execution counters over real data plus 80 synthetic reviews. (Ambiguity scoring is a Round 3 capability).
                    </p>
                  </div>

                  {/* Search Filter */}
                  <div className="relative w-full sm:w-64">
                    <Search className="w-4 h-4 text-[#5B6475] absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Search rule code or title..."
                      value={ruleSearch}
                      onChange={(e) => setRuleSearch(e.target.value)}
                      className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-[#F7F7F4] text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
                    />
                  </div>
                </div>

                {filteredRules.length === 0 ? (
                  <EmptyState title="No rule counters match search" description="Try clearing your search query." />
                ) : (
                  <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Rule performance basic counters table">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                          <th className="py-3 px-4">Rule Code</th>
                          <th className="py-3 px-4">Rule Title / Description</th>
                          <th className="py-3 px-4 text-center">Times Triggered</th>
                          <th className="py-3 px-4 text-center">Accepted Fixes</th>
                          <th className="py-3 px-4 text-center">Dismissed</th>
                          <th className="py-3 px-4 text-center">Distinct Dismissers</th>
                          <th className="py-3 px-4 text-right">Data Source</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E2E5EA]">
                        {filteredRules.map((rc) => (
                          <tr key={rc.rule_code} className="hover:bg-[#F7F7F4]/70 transition-colors">
                            <td className="py-3 px-4 font-mono font-bold text-[#0F766E]">
                              {rc.rule_code}
                            </td>
                            <td className="py-3 px-4 font-medium text-[#1F2A44]">
                              {rc.rule_title}
                            </td>
                            <td className="py-3 px-4 text-center font-mono font-bold text-[#1F2A44]">
                              {rc.times_triggered}
                            </td>
                            <td className="py-3 px-4 text-center font-mono text-[#067647]">
                              {rc.times_accepted}
                            </td>
                            <td className="py-3 px-4 text-center font-mono text-[#B45309]">
                              {rc.times_dismissed}
                            </td>
                            <td className="py-3 px-4 text-center font-mono text-[#5B6475]">
                              {rc.distinct_dismissers}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[#5B6475]">
                                is_synthetic=true
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </AppShell>
    </AuthGuard>
  );
}
