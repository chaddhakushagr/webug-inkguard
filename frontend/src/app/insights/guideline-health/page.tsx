"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import {
  AppShell,
  Badge,
  Button,
  Card,
  Dialog,
  EmptyState,
  ErrorState,
  Input,
  Select,
  Skeleton,
  toast,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import {
  GuidelineHealthItem,
  StaleRuleResponse,
  GapProposalResponse,
  DismissalDetail,
  ClarificationCommentDetail,
} from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  HeartPulse,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  HelpCircle,
  Clock,
  Sparkles,
  Search,
  Filter,
  ArrowRight,
  ShieldCheck,
  Check,
  X,
  FileText,
  Layers,
  MessageSquare,
  BookOpen,
  Edit3,
  ExternalLink,
  ChevronRight,
  TrendingDown,
  Info,
  Users,
  ShieldAlert,
  Calendar,
  RotateCw,
} from "lucide-react";

export default function GuidelineHealthPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <GuidelineHealthContent />
    </Suspense>
  );
}

function GuidelineHealthContent() {
  const [activeTab, setActiveTab] = useState<"ambiguous" | "stale" | "gaps">("ambiguous");

  // Data states
  const [ambiguousRules, setAmbiguousRules] = useState<GuidelineHealthItem[]>([]);
  const [staleItems, setStaleItems] = useState<StaleRuleResponse[]>([]);
  const [gapProposals, setGapProposals] = useState<GapProposalResponse[]>([]);

  // Loading & Error states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [ambigSearch, setAmbigSearch] = useState("");
  const [ambigFilter, setAmbigFilter] = useState<"all" | "high" | "evaluated" | "not_enough_data">("all");
  const [staleSearch, setStaleSearch] = useState("");
  const [staleFilter, setStaleFilter] = useState<"all" | "high" | "medium" | "low">("all");

  // Drilldown Modal for Ambiguous Rule
  const [drilldownRule, setDrilldownRule] = useState<GuidelineHealthItem | null>(null);
  const [isDrilldownOpen, setIsDrilldownOpen] = useState(false);

  // Reject Gap Modal
  const [rejectingGap, setRejectingGap] = useState<GapProposalResponse | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [isRejectSubmitting, setIsRejectSubmitting] = useState(false);

  // Edit & Approve Gap Modal
  const [editingGap, setEditingGap] = useState<GapProposalResponse | null>(null);
  const [editCode, setEditCode] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");
  const [editClassification, setEditClassification] = useState("internal");
  const [isApproveSubmitting, setIsApproveSubmitting] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [ambigRes, staleRes, gapsRes] = await Promise.all([
        api.getGuidelineHealth().catch((err) => {
          console.error("Failed to load guideline health:", err);
          return [];
        }),
        api.getStaleRules().catch((err) => {
          console.error("Failed to load stale rules:", err);
          return [];
        }),
        api.getGapProposals().catch((err) => {
          console.error("Failed to load gap proposals:", err);
          return [];
        }),
      ]);

      setAmbiguousRules(ambigRes || []);
      setStaleItems(staleRes || []);
      setGapProposals(gapsRes || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load guideline health intelligence.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered ambiguous rules
  const filteredAmbigRules = ambiguousRules.filter((r) => {
    if (ambigFilter === "high") {
      if (r.status !== "evaluated" || (r.ambiguity_score || 0) < 40) return false;
    } else if (ambigFilter === "evaluated") {
      if (r.status !== "evaluated") return false;
    } else if (ambigFilter === "not_enough_data") {
      if (r.status !== "not_enough_data") return false;
    }

    if (!ambigSearch) return true;
    const q = ambigSearch.toLowerCase();
    return (
      r.rule_code.toLowerCase().includes(q) ||
      r.rule_title.toLowerCase().includes(q) ||
      (r.contributing_factors && r.contributing_factors.some((f) => f.toLowerCase().includes(q)))
    );
  });

  // Filtered stale items
  const filteredStaleItems = staleItems.filter((item) => {
    if (staleFilter !== "all" && item.severity !== staleFilter) return false;
    if (!staleSearch) return true;
    const q = staleSearch.toLowerCase();
    return (
      item.code.toLowerCase().includes(q) ||
      item.title.toLowerCase().includes(q) ||
      item.stale_reasons.some((r) => r.toLowerCase().includes(q))
    );
  });

  // High ambiguity count
  const highAmbigCount = ambiguousRules.filter(
    (r) => r.status === "evaluated" && (r.ambiguity_score || 0) >= 40
  ).length;

  // Actions on Gap Proposals
  const handleApproveGap = async (gap: GapProposalResponse) => {
    try {
      setIsApproveSubmitting(true);
      const res = await api.approveGapProposal(gap.id);
      if (res.success) {
        toast(`Draft rule ${gap.code} approved and added to Knowledge Base.`, "success");
        setGapProposals((prev) => prev.filter((p) => p.id !== gap.id));
      } else {
        toast(res.message || "Failed to approve gap proposal.", "error");
      }
    } catch (err: any) {
      toast(err?.message || "Error approving proposal.", "error");
    } finally {
      setIsApproveSubmitting(false);
    }
  };

  const openEditAndApprove = (gap: GapProposalResponse) => {
    setEditingGap(gap);
    setEditCode(gap.code);
    setEditTitle(gap.title);
    setEditBody(gap.body);
    setEditClassification(gap.classification || "internal");
  };

  const handleSaveEditAndApprove = async () => {
    if (!editingGap) return;
    try {
      setIsApproveSubmitting(true);
      // First promote proposal
      const res = await api.approveGapProposal(editingGap.id);
      if (res.success && res.entry_id) {
        // If user changed title, body or classification, update entry
        if (
          editTitle !== editingGap.title ||
          editBody !== editingGap.body ||
          editClassification !== editingGap.classification
        ) {
          await api.updateKBEntry(res.entry_id, {
            title: editTitle,
            body: editBody,
            classification: editClassification,
            change_note: "Customized during gap proposal approval by Brand Manager",
          });
        }
        toast(`Draft rule ${editCode} approved and customized in Knowledge Base.`, "success");
        setGapProposals((prev) => prev.filter((p) => p.id !== editingGap.id));
        setEditingGap(null);
      } else {
        toast(res.message || "Failed to approve gap proposal.", "error");
      }
    } catch (err: any) {
      toast(err?.message || "Failed to save and approve proposal.", "error");
    } finally {
      setIsApproveSubmitting(false);
    }
  };

  const openRejectDialog = (gap: GapProposalResponse) => {
    setRejectingGap(gap);
    setRejectReason("");
  };

  const handleConfirmReject = async () => {
    if (!rejectingGap) return;
    if (rejectReason.trim().length < 3) {
      toast("Please provide a substantive rejection reason (at least 3 characters).", "error");
      return;
    }
    try {
      setIsRejectSubmitting(true);
      const res = await api.rejectGapProposal(rejectingGap.id, rejectReason.trim());
      if (res.success) {
        toast(`Proposal ${rejectingGap.code} rejected with audit record.`, "success");
        setGapProposals((prev) => prev.filter((p) => p.id !== rejectingGap.id));
        setRejectingGap(null);
      } else {
        toast(res.message || "Failed to reject proposal.", "error");
      }
    } catch (err: any) {
      toast(err?.message || "Error rejecting proposal.", "error");
    } finally {
      setIsRejectSubmitting(false);
    }
  };

  return (
    <AuthGuard allowedRoles={["brand_manager", "admin"]}>
      <AppShell pageTitle="Guideline Health">
        <div className="space-y-6">
          {/* Header Banner */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-sm">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-[#0F766E]/10 text-[#0F766E]">
                    <HeartPulse className="w-6 h-6" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                      Guideline Health &amp; Evolution
                    </h1>
                    <p className="text-xs sm:text-sm text-[#5B6475] mt-0.5">
                      Brand Manager Intelligence · Turn creator dismissals, reviewer overrides, and uncodified feedback into guideline improvements.
                    </p>
                  </div>
                </div>
              </div>

              {/* Synthetic History & Refresh Button */}
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFFBEB] border border-[#FDE68A] text-xs font-semibold text-[#B45309]">
                  <span className="w-2 h-2 rounded-full bg-[#B45309] animate-pulse" aria-hidden="true" />
                  Synthetic Demo History (8 Weeks)
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={loadData}
                  disabled={isLoading}
                >
                  <RotateCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              </div>
            </div>

            {/* Quick KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-5 border-t border-[#CBD2DC]/60">
              <div className="bg-[#F7F7F4] rounded-lg p-3.5 border border-[#CBD2DC]/60">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#5B6475]">
                    High Ambiguity Rules
                  </span>
                  <AlertOctagon className="w-4 h-4 text-[#BE123C]" />
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-2xl font-extrabold text-[#1F2A44] tabular-nums">
                    {highAmbigCount}
                  </span>
                  <span className="text-xs text-[#5B6475]">
                    of {ambiguousRules.filter((r) => r.status === "evaluated").length} evaluated
                  </span>
                </div>
              </div>

              <div className="bg-[#F7F7F4] rounded-lg p-3.5 border border-[#CBD2DC]/60">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#5B6475]">
                    Stale Guidelines &amp; Facts
                  </span>
                  <Clock className="w-4 h-4 text-[#B45309]" />
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-2xl font-extrabold text-[#1F2A44] tabular-nums">
                    {staleItems.length}
                  </span>
                  <span className="text-xs text-[#5B6475]">
                    expired or inactive &gt; 8 wks
                  </span>
                </div>
              </div>

              <div className="bg-[#F7F7F4] rounded-lg p-3.5 border border-[#CBD2DC]/60">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#5B6475]">
                    Detected Policy Gaps
                  </span>
                  <Sparkles className="w-4 h-4 text-[#0F766E]" />
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-2xl font-extrabold text-[#1F2A44] tabular-nums">
                    {gapProposals.length}
                  </span>
                  <span className="text-xs text-[#5B6475]">
                    uncited comment clusters
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div
            role="tablist"
            aria-label="Guideline Health navigation tabs"
            className="flex items-center gap-2 border-b border-[#CBD2DC] pb-px"
          >
            <button
              role="tab"
              id="tab-ambiguous"
              aria-selected={activeTab === "ambiguous"}
              aria-controls="panel-ambiguous"
              onClick={() => setActiveTab("ambiguous")}
              className={`flex items-center gap-2 px-4 py-3 font-semibold text-sm rounded-t-lg transition-colors border-b-2 -mb-px focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E] ${
                activeTab === "ambiguous"
                  ? "border-[#0F766E] text-[#0F766E] bg-white shadow-sm"
                  : "border-transparent text-[#5B6475] hover:text-[#1F2A44] hover:bg-white/60"
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Ambiguous Rules</span>
              <span
                className={`ml-1 text-xs px-2 py-0.5 rounded-full font-bold ${
                  activeTab === "ambiguous"
                    ? "bg-[#0F766E]/15 text-[#0F766E]"
                    : "bg-[#CBD2DC]/50 text-[#5B6475]"
                }`}
              >
                {ambiguousRules.length}
              </span>
            </button>

            <button
              role="tab"
              id="tab-stale"
              aria-selected={activeTab === "stale"}
              aria-controls="panel-stale"
              onClick={() => setActiveTab("stale")}
              className={`flex items-center gap-2 px-4 py-3 font-semibold text-sm rounded-t-lg transition-colors border-b-2 -mb-px focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E] ${
                activeTab === "stale"
                  ? "border-[#0F766E] text-[#0F766E] bg-white shadow-sm"
                  : "border-transparent text-[#5B6475] hover:text-[#1F2A44] hover:bg-white/60"
              }`}
            >
              <Clock className="w-4 h-4" />
              <span>Stale Rules &amp; Facts</span>
              <span
                className={`ml-1 text-xs px-2 py-0.5 rounded-full font-bold ${
                  activeTab === "stale"
                    ? "bg-[#0F766E]/15 text-[#0F766E]"
                    : "bg-[#CBD2DC]/50 text-[#5B6475]"
                }`}
              >
                {staleItems.length}
              </span>
            </button>

            <button
              role="tab"
              id="tab-gaps"
              aria-selected={activeTab === "gaps"}
              aria-controls="panel-gaps"
              onClick={() => setActiveTab("gaps")}
              className={`flex items-center gap-2 px-4 py-3 font-semibold text-sm rounded-t-lg transition-colors border-b-2 -mb-px focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E] ${
                activeTab === "gaps"
                  ? "border-[#0F766E] text-[#0F766E] bg-white shadow-sm"
                  : "border-transparent text-[#5B6475] hover:text-[#1F2A44] hover:bg-white/60"
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Uncited Comment Gaps</span>
              <span
                className={`ml-1 text-xs px-2 py-0.5 rounded-full font-bold ${
                  activeTab === "gaps"
                    ? "bg-[#0F766E]/15 text-[#0F766E]"
                    : "bg-[#CBD2DC]/50 text-[#5B6475]"
                }`}
              >
                {gapProposals.length}
              </span>
            </button>
          </div>

          {/* Loading / Error states */}
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-12 w-full rounded-xl" />
              <Skeleton className="h-48 w-full rounded-xl" />
              <Skeleton className="h-48 w-full rounded-xl" />
            </div>
          ) : error ? (
            <ErrorState message={error} onRetry={loadData} />
          ) : (
            <>
              {/* TAB 1: AMBIGUOUS RULES */}
              {activeTab === "ambiguous" && (
                <div id="panel-ambiguous" role="tabpanel" aria-labelledby="tab-ambiguous" className="space-y-4">
                  {/* Explanatory callout for Brand Manager */}
                  <div className="bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl p-4 text-xs sm:text-sm text-[#1E3A8A] flex items-start gap-3">
                    <Info className="w-5 h-5 text-[#2563EB] shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-semibold">How Ambiguity is Computed:</strong>
                      <p className="mt-0.5 text-[#1E40AF]">
                        Score (0–100) measures four friction signals: creator dismissals (30%), reviewer overrides (30%), reviewer disagreements (25%), and clarification questions (15%). Rules with fewer than 5 events show{" "}
                        <span className="font-semibold underline">Not Enough Data</span> to prevent premature conclusions.
                      </p>
                    </div>
                  </div>

                  {/* Search and Filters */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-[#CBD2DC]">
                    <div className="relative flex-1 max-w-md">
                      <Search className="w-4 h-4 text-[#5B6475] absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        placeholder="Search rule code, title, or factor..."
                        value={ambigSearch}
                        onChange={(e) => setAmbigSearch(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 text-sm bg-[#F7F7F4] border border-[#CBD2DC] rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <Filter className="w-4 h-4 text-[#5B6475]" />
                      <select
                        aria-label="Filter rules by ambiguity score"
                        value={ambigFilter}
                        onChange={(e: any) => setAmbigFilter(e.target.value)}
                        className="text-sm bg-white border border-[#CBD2DC] rounded-lg px-3 py-2 text-[#1F2A44] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                      >
                        <option value="all">All Rules ({ambiguousRules.length})</option>
                        <option value="high">High Friction (&ge; 40)</option>
                        <option value="evaluated">Evaluated Only</option>
                        <option value="not_enough_data">Not Enough Data (&lt; 5 events)</option>
                      </select>
                    </div>
                  </div>

                  {/* Rules List */}
                  {filteredAmbigRules.length === 0 ? (
                    <EmptyState
                      title="No Ambiguous Rules Found"
                      description="No rules match your filter criteria or have accumulated friction signals."
                    />
                  ) : (
                    <div className="space-y-3">
                      {filteredAmbigRules.map((rule) => {
                        const isEvaluated = rule.status === "evaluated";
                        const score = rule.ambiguity_score;
                        const isHigh = isEvaluated && (score || 0) >= 40;
                        const isMed = isEvaluated && (score || 0) >= 20 && (score || 0) < 40;

                        return (
                          <div
                            key={rule.rule_code}
                            className={`bg-white rounded-xl border p-5 transition-shadow hover:shadow-md ${
                              isHigh
                                ? "border-[#BE123C]/40 bg-gradient-to-r from-[#FFF1F2]/20 to-white"
                                : "border-[#CBD2DC]"
                            }`}
                          >
                            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                              {/* Left Info */}
                              <div className="space-y-1.5 flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#1F2A44]/10 text-[#1F2A44]">
                                    {rule.rule_code}
                                  </span>
                                  <h2 className="text-base font-bold text-[#1F2A44] truncate">
                                    {rule.rule_title}
                                  </h2>
                                  <span className="text-xs uppercase tracking-wider px-2 py-0.5 rounded-full font-medium bg-[#CBD2DC]/40 text-[#5B6475]">
                                    {rule.rule_type}
                                  </span>
                                </div>

                                {/* Plain-words contributing factors */}
                                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                                  <span className="text-xs font-semibold text-[#5B6475]">
                                    Contributing factors:
                                  </span>
                                  {rule.contributing_factors && rule.contributing_factors.length > 0 ? (
                                    rule.contributing_factors.map((factor, idx) => (
                                      <span
                                        key={idx}
                                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                          factor.toLowerCase().includes("dismiss")
                                            ? "bg-[#FFF1F2] text-[#BE123C] border border-[#FECDD3]"
                                            : factor.toLowerCase().includes("disagree") ||
                                              factor.toLowerCase().includes("override")
                                            ? "bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]"
                                            : factor.toLowerCase().includes("clarification")
                                            ? "bg-[#EFF6FF] text-[#1E40AF] border border-[#BFDBFE]"
                                            : "bg-[#F7F7F4] text-[#5B6475] border border-[#CBD2DC]"
                                        }`}
                                      >
                                        {factor.toLowerCase().includes("dismiss") && (
                                          <TrendingDown className="w-3 h-3" />
                                        )}
                                        {factor.toLowerCase().includes("disagree") && (
                                          <Users className="w-3 h-3" />
                                        )}
                                        {factor.toLowerCase().includes("clarification") && (
                                          <HelpCircle className="w-3 h-3" />
                                        )}
                                        {factor}
                                      </span>
                                    ))
                                  ) : (
                                    <span className="text-xs text-[#5B6475] italic">
                                      No friction signals reported.
                                    </span>
                                  )}
                                </div>

                                {/* Recommendation */}
                                {rule.recommendation && (
                                  <p className="text-xs text-[#5B6475] pt-0.5">
                                    <strong className="text-[#1F2A44]">Recommendation:</strong> {rule.recommendation}
                                  </p>
                                )}
                              </div>

                              {/* Right: Score Gauge & Drilldown Action */}
                              <div className="flex items-center gap-5 shrink-0 self-stretch md:self-auto justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-[#CBD2DC]/60">
                                {isEvaluated ? (
                                  <div className="text-right">
                                    <div className="flex items-center gap-2 justify-end">
                                      {isHigh ? (
                                        <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#FFF1F2] text-[#BE123C] border border-[#FECDD3]">
                                          <AlertOctagon className="w-3.5 h-3.5" /> High Ambiguity
                                        </span>
                                      ) : isMed ? (
                                        <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]">
                                          <AlertTriangle className="w-3.5 h-3.5" /> Moderate Friction
                                        </span>
                                      ) : (
                                        <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#ECFDF5] text-[#067647] border border-[#A7F3D0]">
                                          <CheckCircle2 className="w-3.5 h-3.5" /> Clear &amp; Stable
                                        </span>
                                      )}
                                      <span className="text-2xl font-black text-[#1F2A44] tabular-nums">
                                        {score}/100
                                      </span>
                                    </div>
                                    {/* Score bar */}
                                    <div className="w-36 h-2 bg-[#CBD2DC]/40 rounded-full mt-1.5 overflow-hidden ml-auto">
                                      <div
                                        className={`h-full rounded-full ${
                                          isHigh
                                            ? "bg-[#BE123C]"
                                            : isMed
                                            ? "bg-[#B45309]"
                                            : "bg-[#067647]"
                                        }`}
                                        style={{ width: `${Math.min(score || 0, 100)}%` }}
                                      />
                                    </div>
                                    <span className="text-[11px] text-[#5B6475] mt-1 block">
                                      Based on {rule.total_events} review events
                                    </span>
                                  </div>
                                ) : (
                                  <div className="text-right">
                                    <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-[#F7F7F4] text-[#5B6475] border border-[#CBD2DC]">
                                      <Clock className="w-3.5 h-3.5 text-[#5B6475]" /> Not Enough Data
                                    </span>
                                    <span className="text-[11px] text-[#5B6475] block mt-1">
                                      {rule.total_events} of 5 events recorded
                                    </span>
                                  </div>
                                )}

                                <Button
                                  variant="primary"
                                  size="sm"
                                  onClick={() => {
                                    setDrilldownRule(rule);
                                    setIsDrilldownOpen(true);
                                  }}
                                >
                                  Drill-Down
                                  <ChevronRight className="w-4 h-4 ml-1" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: STALE RULES & FACTS */}
              {activeTab === "stale" && (
                <div id="panel-stale" role="tabpanel" aria-labelledby="tab-stale" className="space-y-4">
                  {/* Explanatory callout */}
                  <div className="bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl p-4 text-xs sm:text-sm text-[#1E3A8A] flex items-start gap-3">
                    <Info className="w-5 h-5 text-[#2563EB] shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-semibold">Stale Rule &amp; Fact Detection:</strong>
                      <p className="mt-0.5 text-[#1E40AF]">
                        Surfaces KB entries that create compliance blind spots: rules never or not triggered in the last 8 weeks, facts that have expired or expire within 30 days, entries past their scheduled review date, and rules citing expired facts.
                      </p>
                    </div>
                  </div>

                  {/* Filters */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-[#CBD2DC]">
                    <div className="relative flex-1 max-w-md">
                      <Search className="w-4 h-4 text-[#5B6475] absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        placeholder="Search stale code, title, or reason..."
                        value={staleSearch}
                        onChange={(e) => setStaleSearch(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 text-sm bg-[#F7F7F4] border border-[#CBD2DC] rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <Filter className="w-4 h-4 text-[#5B6475]" />
                      <select
                        aria-label="Filter stale items by severity"
                        value={staleFilter}
                        onChange={(e: any) => setStaleFilter(e.target.value)}
                        className="text-sm bg-white border border-[#CBD2DC] rounded-lg px-3 py-2 text-[#1F2A44] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                      >
                        <option value="all">All Severities ({staleItems.length})</option>
                        <option value="high">High Severity (Expired)</option>
                        <option value="medium">Medium Severity (Past Review Date)</option>
                        <option value="low">Low Severity (Un-triggered)</option>
                      </select>
                    </div>
                  </div>

                  {/* Stale Items Cards */}
                  {filteredStaleItems.length === 0 ? (
                    <EmptyState
                      title="No Stale Rules or Facts Found"
                      description="All active rules and facts have been triggered recently and are within their validity dates."
                    />
                  ) : (
                    <div className="space-y-3">
                      {filteredStaleItems.map((item) => {
                        const isHigh = item.severity === "high";
                        const isMed = item.severity === "medium";

                        return (
                          <div
                            key={item.entry_id}
                            className={`bg-white rounded-xl border p-5 transition-shadow hover:shadow-md ${
                              isHigh
                                ? "border-[#BE123C]/50 bg-gradient-to-r from-[#FFF1F2]/25 to-white"
                                : isMed
                                ? "border-[#B45309]/40 bg-gradient-to-r from-[#FFFBEB]/25 to-white"
                                : "border-[#CBD2DC]"
                            }`}
                          >
                            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                              <div className="space-y-1.5 flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#1F2A44]/10 text-[#1F2A44]">
                                    {item.code}
                                  </span>
                                  <h2 className="text-base font-bold text-[#1F2A44]">
                                    {item.title}
                                  </h2>
                                  <span className="text-xs uppercase tracking-wider px-2 py-0.5 rounded-full font-medium bg-[#CBD2DC]/40 text-[#5B6475]">
                                    {item.type}
                                  </span>
                                  {isHigh ? (
                                    <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#FFF1F2] text-[#BE123C] border border-[#FECDD3]">
                                      <AlertOctagon className="w-3.5 h-3.5" /> High Severity
                                    </span>
                                  ) : isMed ? (
                                    <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]">
                                      <AlertTriangle className="w-3.5 h-3.5" /> Medium Severity
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#F7F7F4] text-[#5B6475] border border-[#CBD2DC]">
                                      <Info className="w-3.5 h-3.5" /> Low Severity
                                    </span>
                                  )}
                                </div>

                                {/* Stale Reasons */}
                                <div className="flex flex-wrap items-center gap-2 pt-1">
                                  <span className="text-xs font-semibold text-[#5B6475]">
                                    Detected Stale Reasons:
                                  </span>
                                  {item.stale_reasons.map((r, i) => (
                                    <span
                                      key={i}
                                      className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-[#FFF1F2] text-[#BE123C] border border-[#FECDD3]"
                                    >
                                      <Clock className="w-3 h-3" />
                                      {r.replace(/_/g, " ")}
                                    </span>
                                  ))}
                                </div>

                                {/* Metadata dates */}
                                <div className="flex flex-wrap items-center gap-4 text-xs text-[#5B6475] pt-1">
                                  {item.valid_until && (
                                    <span className="flex items-center gap-1 font-mono">
                                      <Calendar className="w-3.5 h-3.5 text-[#BE123C]" />
                                      Valid Until: {item.valid_until}
                                    </span>
                                  )}
                                  {item.review_date && (
                                    <span className="flex items-center gap-1 font-mono">
                                      <Calendar className="w-3.5 h-3.5 text-[#B45309]" />
                                      Review Date: {item.review_date}
                                    </span>
                                  )}
                                  <span className="flex items-center gap-1">
                                    Last Triggered:{" "}
                                    {item.last_triggered_at
                                      ? new Date(item.last_triggered_at).toLocaleDateString()
                                      : "Never in recorded window"}
                                  </span>
                                </div>

                                <p className="text-xs text-[#5B6475]">
                                  <strong className="text-[#1F2A44]">Recommendation:</strong> {item.recommendation}
                                </p>
                              </div>

                              {/* Direct link into KB editor */}
                              <div className="shrink-0 self-stretch md:self-auto flex items-center justify-end">
                                <Link href={`/kb/?id=${encodeURIComponent(item.code)}&edit=true`}>
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                  >
                                    <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
                                    Review This Entry
                                  </Button>
                                </Link>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: UNCITED COMMENT GAPS */}
              {activeTab === "gaps" && (
                <div id="panel-gaps" role="tabpanel" aria-labelledby="tab-gaps" className="space-y-4">
                  {/* Explanatory callout */}
                  <div className="bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl p-4 text-xs sm:text-sm text-[#1E3A8A] flex items-start gap-3">
                    <Info className="w-5 h-5 text-[#2563EB] shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-semibold">Reviewer Comment Gap Detection:</strong>
                      <p className="mt-0.5 text-[#1E40AF]">
                        Reviewers frequently request changes without citing an existing rule. Inkguard uses lexical BM25 similarity clustering to group uncodified comments into draft KB proposals. Brand managers can Approve, Edit then Approve, or Reject (substantive reason required).
                      </p>
                    </div>
                  </div>

                  {gapProposals.length === 0 ? (
                    <EmptyState
                      title="No Detected Policy Gaps"
                      description="All reviewer feedback currently maps to existing codified rules or has been resolved."
                    />
                  ) : (
                    <div className="space-y-4">
                      {gapProposals.map((gap) => (
                        <div
                          key={gap.id}
                          className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-sm space-y-4 hover:border-[#0F766E]/50 transition-colors"
                        >
                          {/* Top: Header & Badges */}
                          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#0F766E]/10 text-[#0F766E] border border-[#0F766E]/20">
                                {gap.code}
                              </span>
                              <h2 className="text-lg font-bold text-[#1F2A44]">
                                {gap.title}
                              </h2>
                              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]">
                                <Clock className="w-3 h-3" /> Status: Draft
                              </span>
                              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#EFF6FF] text-[#1E40AF] border border-[#BFDBFE]">
                                <MessageSquare className="w-3 h-3" /> {gap.cluster_size} Reviewer Comments
                              </span>
                            </div>

                            {/* Keywords */}
                            <div className="flex flex-wrap items-center gap-1">
                              {gap.top_keywords.map((kw, i) => (
                                <span
                                  key={i}
                                  className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#F7F7F4] text-[#5B6475] border border-[#CBD2DC]"
                                >
                                  #{kw}
                                </span>
                              ))}
                            </div>
                          </div>

                          {/* Middle: Reviewer Quotes and Proposed Rule Text */}
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
                            {/* Evidence: Reviewer Comments */}
                            <div className="bg-[#F7F7F4] rounded-lg p-4 border border-[#CBD2DC]/70 space-y-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475] flex items-center gap-1.5">
                                <MessageSquare className="w-3.5 h-3.5 text-[#0F766E]" />
                                Sample Reviewer Comments in Cluster:
                              </span>
                              <ul className="space-y-2 text-xs text-[#1F2A44]">
                                {gap.sample_comments.map((comment, i) => (
                                  <li
                                    key={i}
                                    className="p-2.5 rounded bg-white border border-[#CBD2DC]/60 italic text-[#1F2A44]"
                                  >
                                    &ldquo;{comment}&rdquo;
                                  </li>
                                ))}
                              </ul>
                            </div>

                            {/* Proposed Draft Rule Copy */}
                            <div className="bg-[#ECFDF5]/30 rounded-lg p-4 border border-[#A7F3D0] space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider text-[#067647] flex items-center gap-1.5">
                                  <Sparkles className="w-3.5 h-3.5 text-[#067647]" />
                                  Synthesized Draft Rule Policy:
                                </span>
                                <span className="text-xs font-mono text-[#067647]">
                                  v1.0 (Draft)
                                </span>
                              </div>
                              <p className="text-xs sm:text-sm text-[#1F2A44] leading-relaxed bg-white p-3 rounded border border-[#A7F3D0]/60">
                                {gap.body}
                              </p>
                              <div className="text-[11px] text-[#5B6475] flex items-center gap-3 pt-1">
                                <span>Classification: <strong>{gap.classification}</strong></span>
                                <span>Type: <strong>{gap.type}</strong></span>
                              </div>
                            </div>
                          </div>

                          {/* Bottom Action Bar */}
                          <div className="flex flex-wrap items-center justify-end gap-3 pt-3 border-t border-[#CBD2DC]/60">
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => openRejectDialog(gap)}
                            >
                              <X className="w-3.5 h-3.5 mr-1.5" />
                              Reject Proposal...
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => openEditAndApprove(gap)}
                            >
                              <Edit3 className="w-3.5 h-3.5 mr-1.5" />
                              Edit then Approve
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              disabled={isApproveSubmitting}
                              onClick={() => handleApproveGap(gap)}
                            >
                              <Check className="w-3.5 h-3.5 mr-1.5" />
                              Approve Draft Rule
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* DRILLDOWN MODAL FOR AMBIGUOUS RULES */}
          <Dialog
            isOpen={isDrilldownOpen}
            onClose={() => setIsDrilldownOpen(false)}
            title={`Rule Drill-Down: ${drilldownRule?.rule_code || ""}`}
            maxWidth="lg"
          >
            {drilldownRule && (
              <div className="space-y-5">
                <div className="bg-[#F7F7F4] rounded-lg p-4 border border-[#CBD2DC] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-[#0F766E]">
                      {drilldownRule.rule_code}
                    </span>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#1F2A44]/10 text-[#1F2A44]">
                      Ambiguity Score: {drilldownRule.ambiguity_score !== null ? `${drilldownRule.ambiguity_score}/100` : "Not Enough Data"}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-[#1F2A44]">
                    {drilldownRule.rule_title}
                  </h3>
                  <p className="text-xs text-[#5B6475]">
                    {drilldownRule.recommendation}
                  </p>
                </div>

                {/* Plain-Words Factor Breakdown */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="p-3 bg-white rounded-lg border border-[#CBD2DC]">
                    <span className="text-[11px] font-semibold text-[#5B6475] uppercase">
                      Creator Dismissals
                    </span>
                    <div className="text-xl font-bold text-[#BE123C] tabular-nums mt-0.5">
                      {drilldownRule.creator_dismissals}
                    </div>
                    <span className="text-[10px] text-[#5B6475]">
                      {Math.round(drilldownRule.dismissal_rate * 100)}% dismissal rate
                    </span>
                  </div>

                  <div className="p-3 bg-white rounded-lg border border-[#CBD2DC]">
                    <span className="text-[11px] font-semibold text-[#5B6475] uppercase">
                      Reviewer Overrides
                    </span>
                    <div className="text-xl font-bold text-[#B45309] tabular-nums mt-0.5">
                      {drilldownRule.reviewer_overrides}
                    </div>
                    <span className="text-[10px] text-[#5B6475]">
                      {Math.round(drilldownRule.override_rate * 100)}% override rate
                    </span>
                  </div>

                  <div className="p-3 bg-white rounded-lg border border-[#CBD2DC]">
                    <span className="text-[11px] font-semibold text-[#5B6475] uppercase">
                      Reviewers Disagreeing
                    </span>
                    <div className="text-xl font-bold text-[#B45309] tabular-nums mt-0.5">
                      {drilldownRule.reviewers_disagreeing_count || (drilldownRule.disagreement_rate > 0 ? "Multiple" : "0")}
                    </div>
                    <span className="text-[10px] text-[#5B6475]">
                      Discordance: {Math.round(drilldownRule.disagreement_rate * 100)}%
                    </span>
                  </div>

                  <div className="p-3 bg-white rounded-lg border border-[#CBD2DC]">
                    <span className="text-[11px] font-semibold text-[#5B6475] uppercase">
                      Clarifications
                    </span>
                    <div className="text-xl font-bold text-[#1E40AF] tabular-nums mt-0.5">
                      {drilldownRule.clarification_comments}
                    </div>
                    <span className="text-[10px] text-[#5B6475]">
                      Questions on rule
                    </span>
                  </div>
                </div>

                {/* Actual Dismissal Reasons Section */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44] flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5 text-[#BE123C]" />
                    Actual Dismissal Reasons Given:
                  </h4>
                  {drilldownRule.drilldown_dismissals && drilldownRule.drilldown_dismissals.length > 0 ? (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {drilldownRule.drilldown_dismissals.map((dis, idx) => (
                        <div
                          key={idx}
                          className="bg-[#FFF1F2]/40 border border-[#FECDD3] rounded-lg p-3 text-xs text-[#1F2A44]"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-[#BE123C] uppercase text-[10px] tracking-wider">
                              {dis.actor_role} dismissal · {dis.reason_code || "triage"}
                            </span>
                            {dis.created_at && (
                              <span className="text-[10px] text-[#5B6475]">
                                {new Date(dis.created_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          <p className="italic text-[#1F2A44]">&ldquo;{dis.reason_text}&rdquo;</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-[#F7F7F4] rounded-lg p-3 text-xs text-[#5B6475] italic">
                      No explicit dismissal comment recorded; dismissals occurred in creator triage.
                    </div>
                  )}
                </div>

                {/* Actual Clarification Comments Section */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44] flex items-center gap-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-[#1E40AF]" />
                    Threaded Clarification Questions &amp; Comments:
                  </h4>
                  {drilldownRule.drilldown_comments && drilldownRule.drilldown_comments.length > 0 ? (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {drilldownRule.drilldown_comments.map((comm) => (
                        <div
                          key={comm.id}
                          className="bg-[#EFF6FF]/40 border border-[#BFDBFE] rounded-lg p-3 text-xs text-[#1F2A44]"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-[#1E40AF] text-[10px] uppercase tracking-wider">
                              From {comm.author_role || "creator"}
                            </span>
                            {comm.created_at && (
                              <span className="text-[10px] text-[#5B6475]">
                                {new Date(comm.created_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          <p className="italic text-[#1F2A44]">&ldquo;{comm.body}&rdquo;</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-[#F7F7F4] rounded-lg p-3 text-xs text-[#5B6475] italic">
                      No clarification questions logged on this rule.
                    </div>
                  )}
                </div>

                {/* Action footer */}
                <div className="flex items-center justify-between pt-4 border-t border-[#CBD2DC]">
                  <Link href={`/kb/?id=${encodeURIComponent(drilldownRule.rule_code)}&edit=true`}>
                    <Button variant="secondary" size="md">
                      <Edit3 className="w-4 h-4 mr-1.5" />
                      Edit Rule in Knowledge Base
                    </Button>
                  </Link>
                  <Button variant="primary" size="md" onClick={() => setIsDrilldownOpen(false)}>
                    Close Drill-Down
                  </Button>
                </div>
              </div>
            )}
          </Dialog>

          {/* EDIT THEN APPROVE GAP MODAL */}
          <Dialog
            isOpen={!!editingGap}
            onClose={() => setEditingGap(null)}
            title="Edit and Approve Gap Proposal"
            maxWidth="lg"
          >
            {editingGap && (
              <div className="space-y-4">
                <p className="text-xs text-[#5B6475]">
                  Refine the proposed draft rule before promoting it to an active Knowledge Base entry.
                </p>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">
                      Rule Code
                    </label>
                    <Input
                      value={editCode}
                      onChange={(e) => setEditCode(e.target.value)}
                      placeholder="e.g. RULE-GAP-FSC-CERTIFIED"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">
                      Rule Title
                    </label>
                    <Input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="Rule title"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">
                      Policy Statement / Body
                    </label>
                    <textarea
                      rows={5}
                      value={editBody}
                      onChange={(e) => setEditBody(e.target.value)}
                      className="w-full text-xs sm:text-sm p-3 bg-white border border-[#CBD2DC] rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                      placeholder="Policy copy..."
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">
                      Classification Tier
                    </label>
                    <select
                      value={editClassification}
                      onChange={(e) => setEditClassification(e.target.value)}
                      className="w-full text-xs sm:text-sm p-2.5 bg-white border border-[#CBD2DC] rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                    >
                      <option value="public">Public</option>
                      <option value="internal">Internal</option>
                      <option value="confidential">Confidential</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#CBD2DC]">
                  <Button variant="secondary" onClick={() => setEditingGap(null)}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    disabled={isApproveSubmitting || !editTitle || !editBody}
                    onClick={handleSaveEditAndApprove}
                  >
                    <Check className="w-4 h-4 mr-1.5" />
                    Save &amp; Approve to Knowledge Base
                  </Button>
                </div>
              </div>
            )}
          </Dialog>

          {/* REJECT GAP MODAL (MANDATORY REASON) */}
          <Dialog
            isOpen={!!rejectingGap}
            onClose={() => setRejectingGap(null)}
            title={`Reject Proposal: ${rejectingGap?.code || ""}`}
            maxWidth="md"
          >
            {rejectingGap && (
              <div className="space-y-4">
                <p className="text-xs sm:text-sm text-[#5B6475]">
                  Rejection requires an explicit substantive reason. This will be recorded in the append-only Audit Log.
                </p>

                <div className="space-y-1">
                  <label htmlFor="reject-reason-input" className="block text-xs font-bold text-[#1F2A44]">
                    Rejection Reason (Mandatory, min 3 characters) *
                  </label>
                  <textarea
                    id="reject-reason-input"
                    rows={4}
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="e.g. Existing international packaging guidelines already cover this requirement..."
                    className="w-full text-xs sm:text-sm p-3 bg-white border border-[#CBD2DC] rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#BE123C]"
                  />
                  <div className="flex justify-between text-[11px] text-[#5B6475]">
                    <span>Minimum 3 characters</span>
                    <span>{rejectReason.trim().length} characters</span>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#CBD2DC]">
                  <Button variant="secondary" onClick={() => setRejectingGap(null)}>
                    Cancel
                  </Button>
                  <Button
                    variant="danger"
                    disabled={isRejectSubmitting || rejectReason.trim().length < 3}
                    onClick={handleConfirmReject}
                  >
                    <X className="w-4 h-4 mr-1.5" />
                    Confirm Rejection
                  </Button>
                </div>
              </div>
            )}
          </Dialog>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
