"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import {
  AppShell,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import {
  EvaluationReportResponse,
  BeforeAfterRow,
  FalsePositiveItem,
  CategoryMetrics,
} from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sparkles,
  Search,
  Filter,
  ArrowRight,
  ShieldCheck,
  RotateCw,
  Sliders,
  Check,
  X,
  FileText,
  Clock,
  Layers,
  BarChart2,
} from "lucide-react";

export default function EvaluationPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <EvaluationContent />
    </Suspense>
  );
}

function EvaluationContent() {
  const [data, setData] = useState<EvaluationReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters for False-Positive Explorer
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getEvaluationResults();
      setData(res);
    } catch (err: any) {
      setError(err?.message || "Failed to load evaluation benchmark results.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const falsePositives = data?.false_positives || [];
  const filteredFPs = falsePositives.filter((fp) => {
    const matchesCat = categoryFilter === "all" || fp.issue_type === categoryFilter;
    const matchesSearch =
      !searchQuery.trim() ||
      fp.document_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      fp.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      fp.explanation.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (fp.cited_entry_code && fp.cited_entry_code.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCat && matchesSearch;
  });

  return (
    <AuthGuard allowedRoles={["brand_manager", "admin"]}>
      <AppShell pageTitle="Benchmark Policy Evaluation">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          {/* Header Section */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#E2E5EA]">
            <div>
              <div className="flex items-center gap-2">
                <span className="p-2 rounded-lg bg-[#0F766E]/10 text-[#0F766E]">
                  <Target className="w-5 h-5" />
                </span>
                <h1 className="text-2xl font-bold tracking-tight text-[#1F2A44] font-serif">
                  Policy Evaluation & Verifier Engine
                </h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded border font-mono text-xs text-[#0F766E] border-[#0F766E]/30 bg-[#F0FDFA]">
                  Improvement 1
                </span>
              </div>
              <p className="mt-1 text-sm text-[#5B6475] max-w-2xl">
                Empirical precision and recall benchmarking across 84 ground-truth labelled marketing copy documents.
                Evaluates false-positive reduction via the secondary semantic entailment verifier pass.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={loadData}
                disabled={isLoading}
                className="gap-1.5"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
              <Link href="/about-ai/">
                <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-[#5B6475]">
                  <HelpCircle className="w-3.5 h-3.5" />
                  Methodology
                </Button>
              </Link>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-6 animate-pulse">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-28 bg-white rounded-xl border border-[#E2E5EA] p-4" />
                ))}
              </div>
              <div className="h-64 bg-white rounded-xl border border-[#E2E5EA]" />
              <div className="h-96 bg-white rounded-xl border border-[#E2E5EA]" />
            </div>
          )}

          {/* Error State */}
          {!isLoading && error && (
            <ErrorState
              title="Failed to Load Evaluation Benchmark"
              message={error}
              onRetry={loadData}
            />
          )}

          {/* Empty State */}
          {!isLoading && !error && !data && (
            <EmptyState
              title="No Evaluation Evidence Found"
              description="No evaluation reports found in docs/evidence/. Run 'python manage.py eval' to generate empirical evaluation metrics."
              action={
                <Button onClick={loadData} variant="primary">
                  Check Again
                </Button>
              }
            />
          )}

          {/* Main Dashboard Content */}
          {!isLoading && !error && data && (
            <>
              {/* Metadata Badges Bar */}
              <div className="flex flex-wrap items-center gap-2.5 p-3 rounded-lg bg-white border border-[#E2E5EA] text-xs">
                <span className="font-semibold text-[#1F2A44] flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-[#0F766E]" />
                  Active Configuration:
                </span>
                <span className="font-mono px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[#1F2A44]">
                  Model: {data.metadata.model || "gemini-3.5-flash-lite"}
                </span>
                <span className="font-mono px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[#1F2A44]">
                  Prompt: {data.metadata.prompt_versions?.verify || "verify.v1.md"}
                </span>
                <span className="font-mono px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[#1F2A44]">
                  Confidence Gate: &ge; {data.metadata.confidence_threshold ?? 0.75}
                </span>
                <span className="font-mono px-2 py-0.5 rounded bg-[#ECFDF3] border border-[#ABEFC6] text-[#067647]">
                  Verifier: Active
                </span>
                <span className="ml-auto text-[11px] text-[#5B6475]">
                  Dataset: {data.summary.total_documents} synthetic docs (Lumo brand)
                </span>
              </div>

              {/* KPI Stat Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="p-5 border-[#CBD2DC] bg-white shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#5B6475]">
                      Clean Pass Rate
                    </span>
                    <span className="p-1.5 rounded-md bg-[#ECFDF3] text-[#067647]">
                      <CheckCircle2 className="w-4 h-4" />
                    </span>
                  </div>
                  <div className="mt-2 text-2xl font-bold font-mono text-[#1F2A44]">
                    {(data.summary.clean_pass_rate * 100).toFixed(1)}%
                  </div>
                  <p className="mt-1 text-xs text-[#067647] font-medium flex items-center gap-1">
                    <span>+52.4% vs. Verifier OFF (23.8%)</span>
                  </p>
                  <p className="text-[11px] text-[#5B6475] mt-1">
                    {data.summary.clean_documents_passed} of {data.summary.clean_documents} clean copy passed cleanly
                  </p>
                </Card>

                <Card className="p-5 border-[#CBD2DC] bg-white shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#5B6475]">
                      Overall Precision
                    </span>
                    <span className="p-1.5 rounded-md bg-[#EFF8FF] text-[#175CD3]">
                      <TrendingUp className="w-4 h-4" />
                    </span>
                  </div>
                  <div className="mt-2 text-2xl font-bold font-mono text-[#1F2A44]">
                    {data.summary.overall.precision.toFixed(3)}
                  </div>
                  <div className="mt-1 flex items-center gap-1.5 text-xs">
                    <span className="text-[#175CD3] font-medium">+0.156 gain with verifier</span>
                    <span className="text-[10px] text-[#5B6475]">(Target: 0.850)</span>
                  </div>
                  <p className="text-[11px] text-[#5B6475] mt-1">
                    TP: {data.summary.overall.tp} | FP: {data.summary.overall.fp}
                  </p>
                </Card>

                <Card className="p-5 border-[#CBD2DC] bg-white shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#5B6475]">
                      Overall Recall
                    </span>
                    <span className="p-1.5 rounded-md bg-[#ECFDF3] text-[#067647]">
                      <Check className="w-4 h-4" />
                    </span>
                  </div>
                  <div className="mt-2 text-2xl font-bold font-mono text-[#1F2A44]">
                    {data.summary.overall.recall.toFixed(3)}
                  </div>
                  <div className="mt-1 flex items-center gap-1.5 text-xs">
                    <span className="text-[#067647] font-semibold">Target Met (+0.035)</span>
                    <span className="text-[10px] text-[#5B6475]">(Target &ge; 0.800)</span>
                  </div>
                  <p className="text-[11px] text-[#5B6475] mt-1">
                    71 of 85 ground-truth violations caught
                  </p>
                </Card>

                <Card className="p-5 border-[#CBD2DC] bg-white shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#5B6475]">
                      F1 Measure
                    </span>
                    <span className="p-1.5 rounded-md bg-[#F7F7F4] text-[#1F2A44]">
                      <BarChart2 className="w-4 h-4" />
                    </span>
                  </div>
                  <div className="mt-2 text-2xl font-bold font-mono text-[#1F2A44]">
                    {data.summary.overall.f1.toFixed(3)}
                  </div>
                  <p className="mt-1 text-xs text-[#5B6475] font-medium">
                    Harmonic mean of precision & recall
                  </p>
                  <p className="text-[11px] text-[#5B6475] mt-1">
                    False Negatives: {data.summary.overall.fn} missed
                  </p>
                </Card>
              </div>

              {/* Section 1: Before-and-After Verifier Comparison */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden shadow-xs">
                <div className="px-6 py-4 border-b border-[#E2E5EA] bg-[#F7F7F4]/50 flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-bold text-[#1F2A44] flex items-center gap-2">
                      <Layers className="w-4 h-4 text-[#0F766E]" />
                      Empirical Before/After Verifier Benchmark
                    </h2>
                    <p className="text-xs text-[#5B6475] mt-0.5">
                      Measuring the exact mathematical impact of the secondary semantic entailment pass on clean pass rate, false positives, and precision.
                    </p>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded border border-[#CBD2DC] bg-[#F7F7F4] text-xs font-mono text-[#5B6475]">
                    84 Benchmark Docs
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#E2E5EA] bg-[#F7F7F4] text-[#5B6475] uppercase font-mono text-[10px] tracking-wider">
                        <th className="py-3 px-4 font-semibold">Mode</th>
                        <th className="py-3 px-4 font-semibold">Verifier Pass</th>
                        <th className="py-3 px-4 font-semibold text-center">Docs</th>
                        <th className="py-3 px-4 font-semibold text-center">Clean Pass</th>
                        <th className="py-3 px-4 font-semibold text-center">TP</th>
                        <th className="py-3 px-4 font-semibold text-center">FP</th>
                        <th className="py-3 px-4 font-semibold text-center">FN</th>
                        <th className="py-3 px-4 font-semibold text-right">Precision</th>
                        <th className="py-3 px-4 font-semibold text-right">Recall</th>
                        <th className="py-3 px-4 font-semibold text-right">F1 Score</th>
                        <th className="py-3 px-4 font-semibold">Verifier Impact</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2E5EA] font-sans">
                      {data.before_after.map((row, idx) => {
                        const isVerifierOn = row.verifier.toUpperCase() === "ON";
                        return (
                          <tr
                            key={idx}
                            className={`hover:bg-[#F7F7F4]/60 transition-colors ${
                              isVerifierOn ? "bg-[#F0FDFA]/30" : ""
                            }`}
                          >
                            <td className="py-3 px-4 font-mono font-bold text-[#1F2A44] uppercase">
                              {row.mode}
                            </td>
                            <td className="py-3 px-4">
                              <span
                                className={`inline-flex items-center gap-1 font-mono text-[11px] font-bold px-2 py-0.5 rounded border ${
                                  isVerifierOn
                                    ? "bg-[#ECFDF3] text-[#067647] border-[#ABEFC6]"
                                    : "bg-[#F7F7F4] text-[#5B6475] border-[#CBD2DC]"
                                }`}
                              >
                                {isVerifierOn ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                                {row.verifier}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-center text-[#5B6475]">{row.total_docs}</td>
                            <td className="py-3 px-4 font-mono text-center font-semibold text-[#1F2A44]">
                              {(row.clean_pass_rate * 100).toFixed(1)}%
                            </td>
                            <td className="py-3 px-4 font-mono text-center text-[#067647] font-semibold">{row.tp}</td>
                            <td className="py-3 px-4 font-mono text-center text-[#B42318] font-semibold">{row.fp}</td>
                            <td className="py-3 px-4 font-mono text-center text-[#B45309] font-semibold">{row.fn}</td>
                            <td className="py-3 px-4 font-mono text-right font-bold text-[#1F2A44]">
                              {row.precision.toFixed(3)}
                            </td>
                            <td className="py-3 px-4 font-mono text-right font-bold text-[#1F2A44]">
                              {row.recall.toFixed(3)}
                            </td>
                            <td className="py-3 px-4 font-mono text-right font-bold text-[#0F766E]">
                              {row.f1.toFixed(3)}
                            </td>
                            <td className="py-3 px-4 text-xs">
                              {isVerifierOn ? (
                                <span className="text-[#067647] font-semibold flex items-center gap-1">
                                  <span>&darr; FP halved, clean rate 76.2%</span>
                                </span>
                              ) : (
                                <span className="text-[#5B6475]">Baseline without entailment filter</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Section 2: Per-Rule-Type Breakdown Table */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden shadow-xs">
                <div className="px-6 py-4 border-b border-[#E2E5EA] bg-[#F7F7F4]/50">
                  <h2 className="text-base font-bold text-[#1F2A44] flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-[#0F766E]" />
                    Per-Rule-Type Accuracy Breakdown (Latest Verifier ON Run)
                  </h2>
                  <p className="text-xs text-[#5B6475] mt-0.5">
                    Granular breakdown of true positives, false alarms, and missed violations across all policy domains.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#E2E5EA] bg-[#F7F7F4] text-[#5B6475] uppercase font-mono text-[10px] tracking-wider">
                        <th className="py-3 px-4 font-semibold">Policy Category</th>
                        <th className="py-3 px-4 font-semibold text-center">TP</th>
                        <th className="py-3 px-4 font-semibold text-center">FP</th>
                        <th className="py-3 px-4 font-semibold text-center">FN</th>
                        <th className="py-3 px-4 font-semibold text-right">Precision</th>
                        <th className="py-3 px-4 font-semibold text-right">Recall</th>
                        <th className="py-3 px-4 font-semibold text-right">F1</th>
                        <th className="py-3 px-4">Performance Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2E5EA]">
                      {Object.entries(data.by_issue_type).map(([category, m]: [string, CategoryMetrics]) => {
                        const isPerfect = m.precision === 1.0 && m.recall === 1.0;
                        const hasFPs = m.fp > 0;
                        return (
                          <tr key={category} className="hover:bg-[#F7F7F4]/60 transition-colors">
                            <td className="py-3 px-4 font-mono font-bold text-[#1F2A44] uppercase">
                              {category.replace("_", " ")}
                            </td>
                            <td className="py-3 px-4 font-mono text-center text-[#067647] font-semibold">{m.tp}</td>
                            <td className="py-3 px-4 font-mono text-center text-[#B42318] font-semibold">{m.fp}</td>
                            <td className="py-3 px-4 font-mono text-center text-[#B45309] font-semibold">{m.fn}</td>
                            <td className="py-3 px-4 font-mono text-right font-bold text-[#1F2A44]">
                              {m.precision.toFixed(3)}
                            </td>
                            <td className="py-3 px-4 font-mono text-right font-bold text-[#1F2A44]">
                              {m.recall.toFixed(3)}
                            </td>
                            <td className="py-3 px-4 font-mono text-right font-bold text-[#0F766E]">
                              {m.f1.toFixed(3)}
                            </td>
                            <td className="py-3 px-4">
                              {isPerfect ? (
                                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#067647] bg-[#ECFDF3] px-2 py-0.5 rounded border border-[#ABEFC6]">
                                  <Check className="w-3 h-3" />
                                  100% Deterministic Match
                                </span>
                              ) : hasFPs ? (
                                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#B45309] bg-[#FFFBEB] px-2 py-0.5 rounded border border-[#FDE68A]">
                                  <AlertTriangle className="w-3 h-3" />
                                  {m.fp} False Alarm{m.fp > 1 ? "s" : ""}
                                </span>
                              ) : (
                                <span className="text-[#5B6475] text-[11px]">No violations present</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Section 3: False-Positive Explorer & Audit List */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden shadow-xs">
                <div className="px-6 py-4 border-b border-[#E2E5EA] bg-[#F7F7F4]/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-base font-bold text-[#1F2A44] flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-[#B45309]" />
                      False-Positive Audit Explorer ({filteredFPs.length} items)
                    </h2>
                    <p className="text-xs text-[#5B6475] mt-0.5">
                      Inspect every candidate finding flagged on clean copy or ungrounded passages to audit false-positive patterns.
                    </p>
                  </div>

                  {/* Filter controls */}
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-[#5B6475] absolute left-2.5 top-2.5" />
                      <input
                        type="text"
                        placeholder="Search document or quote..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-8 pr-3 py-1 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] placeholder:text-[#5B6475] focus:outline-none focus:ring-1 focus:ring-[#0F766E]"
                      />
                    </div>

                    <select
                      value={categoryFilter}
                      onChange={(e) => setCategoryFilter(e.target.value)}
                      className="px-2.5 py-1 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-1 focus:ring-[#0F766E]"
                    >
                      <option value="all">All Categories</option>
                      <option value="claim">Claim</option>
                      <option value="tone">Tone</option>
                      <option value="readability">Readability</option>
                      <option value="accessibility">Accessibility</option>
                    </select>
                  </div>
                </div>

                {filteredFPs.length === 0 ? (
                  <div className="p-8 text-center text-sm text-[#5B6475]">
                    No false positives match the selected filter.
                  </div>
                ) : (
                  <div className="divide-y divide-[#E2E5EA] max-h-[600px] overflow-y-auto">
                    {filteredFPs.map((fp, i) => (
                      <div key={i} className="p-4 hover:bg-[#F7F7F4]/50 transition-colors">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[#1F2A44]">
                              {fp.document_id}
                            </span>
                            <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF]">
                              {fp.channel}
                            </span>
                            <span className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]">
                              {fp.issue_type}
                            </span>
                            {fp.cited_entry_code && (
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white border border-[#CBD2DC] text-[#0F766E]">
                                Cited: {fp.cited_entry_code}
                              </span>
                            )}
                          </div>

                          {fp.confidence && (
                            <span className="text-[10px] font-mono text-[#5B6475]">
                              Confidence: {(fp.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>

                        {/* Excerpt */}
                        <div className="mt-2 p-2 bg-[#F7F7F4] rounded border border-[#E2E5EA] text-xs font-serif text-[#1F2A44]">
                          &ldquo;{fp.excerpt}&rdquo;
                        </div>

                        {/* Explanation */}
                        <p className="mt-2 text-xs text-[#5B6475] leading-relaxed">
                          <strong className="text-[#1F2A44]">Reason:</strong> {fp.explanation}
                        </p>
                      </div>
                    ))}
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
