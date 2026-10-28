"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AppShell,
  Badge,
  Button,
  Card,
  Dialog,
  DiffView,
  EmptyState,
  ErrorState,
  Input,
  Select,
  Skeleton,
  toast,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import { KBEntry, KBVersion, User } from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  BookOpen,
  Filter,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  History,
  Edit3,
  Archive,
  ChevronRight,
  Eye,
  Check,
  AlertTriangle,
} from "lucide-react";

export default function KnowledgeBasePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <KnowledgeBaseContent />
    </Suspense>
  );
}

function KnowledgeBaseContent() {
  const searchParams = useSearchParams();
  const initialId = searchParams.get("id");
  const initialType = searchParams.get("type") || "all";
  const initialTab = searchParams.get("tab") === "edit" || searchParams.get("edit") === "true" ? "edit" : "detail";

  const [user, setUser] = useState<User | null>(null);
  const [entries, setEntries] = useState<KBEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<KBEntry | null>(null);
  const [versions, setVersions] = useState<KBVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>(initialType);
  const [tierFilter, setTierFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("active");
  const [expiringOnly, setExpiringOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Edit / Version Modal States
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"detail" | "versions" | "edit">("detail");
  const [diffFromV, setDiffFromV] = useState<number>(1);
  const [diffToV, setDiffToV] = useState<number>(1);
  const [isSaving, setIsSaving] = useState(false);

  // Edit form fields
  const [editTitle, setEditTitle] = useState("");
  const [editBody, setEditBody] = useState("");
  const [editClassification, setEditClassification] = useState<string>("internal");
  const [editChangeNote, setEditChangeNote] = useState("");

  useEffect(() => {
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
  }, []);

  const loadEntries = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getKBEntries(typeFilter, statusFilter, tierFilter, expiringOnly);
      setEntries(data || []);

      if (initialId && !selectedEntry) {
        const match = data.find((e) => e.id === initialId || e.code === initialId.toUpperCase());
        if (match) {
          openDetail(match, initialTab);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load knowledge base entries");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadEntries();
  }, [typeFilter, tierFilter, statusFilter, expiringOnly]);

  const openDetail = async (entry: KBEntry, tab: "detail" | "versions" | "edit" = "detail") => {
    setSelectedEntry(entry);
    setEditTitle(entry.title);
    setEditBody(entry.body || "");
    setEditClassification(entry.classification);
    setEditChangeNote("");
    setActiveTab(tab);
    setIsDetailOpen(true);

    // Fetch version history
    try {
      const vers = await api.getKBEntryVersions(entry.id);
      setVersions(vers || []);
      if (vers && vers.length >= 2) {
        setDiffFromV(vers[1].version);
        setDiffToV(vers[0].version);
      } else if (vers && vers.length === 1) {
        setDiffFromV(vers[0].version);
        setDiffToV(vers[0].version);
      }
    } catch {
      setVersions([]);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEntry) return;
    setIsSaving(true);
    try {
      const updated = await api.updateKBEntry(selectedEntry.id, {
        title: editTitle,
        body: editBody,
        classification: editClassification,
        change_note: editChangeNote || "Updated via brand governance portal",
      });
      setSelectedEntry(updated);
      setActiveTab("detail");
      await loadEntries();
      const vers = await api.getKBEntryVersions(updated.id);
      setVersions(vers || []);
      toast(`Entry ${updated.code} updated to Version ${updated.current_version}.`, "success");
    } catch (err: any) {
      toast(err.message || "Failed to update entry", "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRetire = async () => {
    if (!selectedEntry || !confirm(`Are you sure you want to retire ${selectedEntry.code}?`)) return;
    try {
      const retired = await api.retireKBEntry(selectedEntry.id);
      setSelectedEntry(retired);
      await loadEntries();
      toast(`Entry ${selectedEntry.code} retired from active governance.`, "info");
    } catch (err: any) {
      toast(err.message || "Failed to retire entry", "error");
    }
  };

  const filteredEntries = entries.filter((e) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      e.code.toLowerCase().includes(q) ||
      e.title.toLowerCase().includes(q) ||
      (e.body && e.body.toLowerCase().includes(q))
    );
  });

  const isManagerOrAdmin = user?.role === "brand_manager" || user?.role === "admin";

  const getValidityBadge = (entry: KBEntry) => {
    if (entry.type !== "fact" || !entry.data?.valid_until) return null;
    const until = new Date(entry.data.valid_until);
    const now = new Date();
    const daysLeft = Math.ceil((until.getTime() - now.getTime()) / (1000 * 3600 * 24));

    if (daysLeft < 0) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]">
          Expired
        </span>
      );
    }
    if (daysLeft <= 90) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]">
          Expiring Soon ({daysLeft}d)
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]">
        Active ({daysLeft}d)
      </span>
    );
  };

  const getTierBadge = (tier: string) => {
    const map: Record<string, string> = {
      public: "bg-[#ECFDF3] text-[#067647] border-[#ABEFC6]",
      internal: "bg-[#F7F7F4] text-[#1F2A44] border-[#CBD2DC]",
      confidential: "bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]",
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${map[tier] || ""}`}>
        {tier}
      </span>
    );
  };

  return (
    <AuthGuard>
      <AppShell pageTitle="Knowledge Base &amp; Brand Guidelines">
        <div className="space-y-6">
          {/* Header & Clearance Indicator */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-[#0F766E]" />
                <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                  Lumo Knowledge Base
                </h1>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
                Single source of truth for tone, terms, verified clinical facts, and governance rules.
                Your clearance: <strong className="font-mono text-[#0F766E] uppercase">{user?.max_tier || "internal"}</strong>.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#5B6475] hidden sm:inline">
                {filteredEntries.length} items accessible
              </span>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-4 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
            {/* Search */}
            <div className="relative flex-1 w-full lg:max-w-sm">
              <Search className="w-4 h-4 text-[#5B6475] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by code, title, or keyword..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-[#F7F7F4] text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              />
            </div>

            {/* Filter Selects */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Type Filter */}
              <select
                aria-label="Filter by type"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Types</option>
                <option value="term">Terms ({entries.filter((e) => e.type === "term").length})</option>
                <option value="fact">Facts ({entries.filter((e) => e.type === "fact").length})</option>
                <option value="rule">Rules ({entries.filter((e) => e.type === "rule").length})</option>
                <option value="tone">Tone ({entries.filter((e) => e.type === "tone").length})</option>
                <option value="asset">Assets ({entries.filter((e) => e.type === "asset").length})</option>
              </select>

              {/* Tier Filter */}
              <select
                aria-label="Filter by classification tier"
                value={tierFilter}
                onChange={(e) => setTierFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Tiers</option>
                <option value="public">Public</option>
                <option value="internal">Internal</option>
                {user?.max_tier === "confidential" && <option value="confidential">Confidential</option>}
              </select>

              {/* Status Filter */}
              <select
                aria-label="Filter by status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="active">Active Only</option>
                <option value="all">Active &amp; Retired</option>
              </select>

              {/* Expiring Toggle */}
              <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#CBD2DC] bg-white text-xs font-semibold text-[#1F2A44] cursor-pointer hover:bg-[#F7F7F4]">
                <input
                  type="checkbox"
                  checked={expiringOnly}
                  onChange={(e) => setExpiringOnly(e.target.checked)}
                  className="rounded border-[#CBD2DC] text-[#0F766E] focus:ring-[#0F766E]"
                />
                <span>Expiring Facts</span>
              </label>
            </div>
          </div>

          {/* Entries Table */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden">
            {isLoading ? (
              <div className="p-8 space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : error ? (
              <ErrorState message={error} onRetry={loadEntries} />
            ) : filteredEntries.length === 0 ? (
              <EmptyState
                title="No Knowledge Base entries match the filter"
                description="Try loosening your filters or clearing the search query."
              />
            ) : (
              <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Knowledge base entries table">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                      <th className="py-3 px-4">Code</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Title &amp; Statement</th>
                      <th className="py-3 px-4">Tier</th>
                      <th className="py-3 px-4">Validity / Status</th>
                      <th className="py-3 px-4">Version</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E5EA]">
                    {filteredEntries.map((e) => (
                      <tr
                        key={e.id}
                        onClick={() => openDetail(e)}
                        className="hover:bg-[#F7F7F4]/70 cursor-pointer transition-colors"
                      >
                        <td className="py-3 px-4 font-mono font-bold text-[#0F766E]">{e.code}</td>
                        <td className="py-3 px-4">
                          <span className="capitalize font-mono px-2 py-0.5 rounded bg-[#E2E5EA] text-[#1F2A44] font-medium">
                            {e.type}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-bold text-[#1F2A44]">{e.title}</div>
                          {e.body && (
                            <div className="text-[11px] text-[#5B6475] line-clamp-1 mt-0.5">{e.body}</div>
                          )}
                        </td>
                        <td className="py-3 px-4">{getTierBadge(e.classification)}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5">
                            {getValidityBadge(e)}
                            {e.status === "retired" && (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[#E2E5EA] text-[#5B6475]">
                                Retired
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono">v{e.current_version}</td>
                        <td className="py-3 px-4 text-right">
                          <span className="text-[#0F766E] font-semibold hover:underline inline-flex items-center gap-1">
                            Inspect <ChevronRight className="w-3.5 h-3.5" />
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Entry Detail & Version History Dialog */}
        <Dialog
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
          title={selectedEntry ? `${selectedEntry.code}: ${selectedEntry.title}` : "KB Entry Details"}
          description={
            selectedEntry
              ? `Classification: ${selectedEntry.classification.toUpperCase()} · Current Version: v${selectedEntry.current_version}`
              : ""
          }
          maxWidth="lg"
        >
          {selectedEntry && (
            <div className="space-y-6">
              {/* Tabs */}
              <div className="flex items-center gap-2 border-b border-[#E2E5EA] pb-2">
                <button
                  type="button"
                  onClick={() => setActiveTab("detail")}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${
                    activeTab === "detail"
                      ? "bg-[#1F2A44] text-white"
                      : "text-[#5B6475] hover:text-[#1F2A44]"
                  }`}
                >
                  Fields &amp; Guidance
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("versions")}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                    activeTab === "versions"
                      ? "bg-[#1F2A44] text-white"
                      : "text-[#5B6475] hover:text-[#1F2A44]"
                  }`}
                >
                  <History className="w-3.5 h-3.5" />
                  Version Diff ({versions.length})
                </button>
                {isManagerOrAdmin && (
                  <button
                    type="button"
                    onClick={() => setActiveTab("edit")}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                      activeTab === "edit"
                        ? "bg-[#1F2A44] text-white"
                        : "text-[#5B6475] hover:text-[#1F2A44]"
                    }`}
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    Edit (New Version)
                  </button>
                )}
              </div>

              {/* Tab 1: Detailed Field View by Type */}
              {activeTab === "detail" && (
                <div className="space-y-4">
                  {/* Badges Row */}
                  <div className="flex flex-wrap items-center gap-2">
                    {getTierBadge(selectedEntry.classification)}
                    {getValidityBadge(selectedEntry)}
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-[#E2E5EA] text-[#1F2A44]">
                      Version {selectedEntry.current_version}
                    </span>
                  </div>

                  {selectedEntry.body && (
                    <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                      <span className="text-[10px] font-bold uppercase text-[#5B6475] block mb-1">
                        Body / Definition
                      </span>
                      <p className="text-xs text-[#1F2A44] leading-relaxed whitespace-pre-wrap">
                        {selectedEntry.body}
                      </p>
                    </div>
                  )}

                  {/* Type-Specific Fields */}
                  {selectedEntry.type === "term" && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Banned Flag</span>
                        <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-bold ${
                          selectedEntry.data?.banned ? "bg-[#FEF3F2] text-[#B42318]" : "bg-[#ECFDF3] text-[#067647]"
                        }`}>
                          {selectedEntry.data?.banned ? "Banned Term" : "Standardized Term"}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Preferred Replacement</span>
                        <span className="text-xs font-bold text-[#0F766E] mt-1 block">
                          {selectedEntry.data?.preferred || "None designated"}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white sm:col-span-2">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Approved Exceptions</span>
                        <p className="text-xs text-[#1F2A44] mt-1">
                          {Array.isArray(selectedEntry.data?.exceptions) && selectedEntry.data.exceptions.length > 0
                            ? selectedEntry.data.exceptions.join(", ")
                            : "None (zero exceptions permitted)"}
                        </p>
                      </div>
                    </div>
                  )}

                  {selectedEntry.type === "fact" && (
                    <div className="space-y-3">
                      <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Verified Statement</span>
                        <p className="text-xs font-medium text-[#1F2A44] mt-1">{selectedEntry.data?.statement}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Source Citation</span>
                          <span className="text-xs text-[#1F2A44] mt-1 block">{selectedEntry.data?.source || "Clinical Dossier"}</span>
                        </div>
                        <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Valid Until</span>
                          <span className="text-xs font-mono font-bold text-[#1F2A44] mt-1 block">
                            {selectedEntry.data?.valid_until || "Ongoing"}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {selectedEntry.type === "tone" && (
                    <div className="space-y-3">
                      <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Editorial Guidance</span>
                        <p className="text-xs text-[#1F2A44] mt-1">{selectedEntry.data?.guidance}</p>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="p-3 rounded-lg border border-[#ABEFC6] bg-[#ECFDF3]/40">
                          <span className="text-[10px] font-bold uppercase text-[#067647] flex items-center gap-1 mb-2">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Approved Examples
                          </span>
                          <ul className="space-y-1.5 text-xs text-[#1F2A44]">
                            {selectedEntry.data?.good_examples?.map((ex: string, i: number) => (
                              <li key={i} className="flex items-start gap-1.5">
                                <span className="text-[#067647]">&bull;</span>
                                <span>&ldquo;{ex}&rdquo;</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div className="p-3 rounded-lg border border-[#FECDCA] bg-[#FEF3F2]/40">
                          <span className="text-[10px] font-bold uppercase text-[#B42318] flex items-center gap-1 mb-2">
                            <XCircle className="w-3.5 h-3.5" /> Off-Tone Examples (Disallowed)
                          </span>
                          <ul className="space-y-1.5 text-xs text-[#1F2A44]">
                            {selectedEntry.data?.bad_examples?.map((ex: string, i: number) => (
                              <li key={i} className="flex items-start gap-1.5">
                                <span className="text-[#B42318]">&bull;</span>
                                <span>&ldquo;{ex}&rdquo;</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {selectedEntry.type === "rule" && (
                    <div className="space-y-3">
                      <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Regex Pattern / Logic</span>
                        <code className="text-xs font-mono text-[#B42318] mt-1 block">
                          {selectedEntry.data?.pattern || "Semantic Logic Check"}
                        </code>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Target Channels</span>
                          <span className="text-xs font-mono uppercase text-[#1F2A44] mt-1 block">
                            {Array.isArray(selectedEntry.data?.applies_to_channels)
                              ? selectedEntry.data.applies_to_channels.join(", ")
                              : "All Channels"}
                          </span>
                        </div>
                        <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Severity</span>
                          <span className="text-xs font-bold uppercase text-[#B42318] mt-1 block">
                            {selectedEntry.data?.severity || "High"}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {selectedEntry.type === "asset" && (
                    <div className="space-y-3">
                      <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Usage Rules</span>
                        <p className="text-xs text-[#1F2A44] mt-1">{selectedEntry.data?.usage_rules}</p>
                      </div>
                      {selectedEntry.data?.palette && (
                        <div className="p-3 rounded-lg border border-[#CBD2DC] bg-white">
                          <span className="text-[10px] font-bold uppercase text-[#5B6475] block mb-2">Palette Swatches</span>
                          <div className="flex flex-wrap items-center gap-3">
                            {Object.entries(selectedEntry.data.palette).map(([name, hex]) => (
                              <div key={name} className="flex items-center gap-2">
                                <div
                                  className="w-6 h-6 rounded-md border border-[#CBD2DC]"
                                  style={{ backgroundColor: String(hex) }}
                                />
                                <div className="text-[11px]">
                                  <span className="font-bold text-[#1F2A44] capitalize">{name}: </span>
                                  <span className="font-mono text-[#5B6475]">{String(hex)}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Version History with Inline DiffView */}
              {activeTab === "versions" && (
                <div className="space-y-4">
                  {versions.length === 0 ? (
                    <p className="text-xs text-[#5B6475]">No older versions recorded.</p>
                  ) : (
                    <>
                      <div className="flex items-center gap-4 p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-[#1F2A44]">Compare:</span>
                          <select
                            aria-label="Compare from version"
                            value={diffFromV}
                            onChange={(e) => setDiffFromV(Number(e.target.value))}
                            className="px-2 py-1 text-xs rounded border border-[#CBD2DC] bg-white"
                          >
                            {versions.map((v) => (
                              <option key={v.id} value={v.version}>
                                v{v.version} ({new Date(v.created_at).toLocaleDateString()})
                              </option>
                            ))}
                          </select>
                        </div>
                        <span className="text-xs text-[#5B6475]">&rarr;</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-[#1F2A44]">With:</span>
                          <select
                            aria-label="Compare with version"
                            value={diffToV}
                            onChange={(e) => setDiffToV(Number(e.target.value))}
                            className="px-2 py-1 text-xs rounded border border-[#CBD2DC] bg-white"
                          >
                            {versions.map((v) => (
                              <option key={v.id} value={v.version}>
                                v{v.version} ({new Date(v.created_at).toLocaleDateString()})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Render Diff */}
                      {(() => {
                        const fromVer = versions.find((v) => v.version === diffFromV);
                        const toVer = versions.find((v) => v.version === diffToV);
                        const fromText = fromVer
                          ? `${fromVer.snapshot.title}\n\n${fromVer.snapshot.body || ""}`
                          : "";
                        const toText = toVer
                          ? `${toVer.snapshot.title}\n\n${toVer.snapshot.body || ""}`
                          : "";
                        return (
                          <div className="border border-[#CBD2DC] rounded-lg overflow-hidden">
                            <div className="bg-[#F7F7F4] px-3 py-2 border-b border-[#CBD2DC] text-[11px] font-bold text-[#5B6475]">
                              Text Diff (v{diffFromV} vs v{diffToV})
                            </div>
                            <div className="p-3">
                              <DiffView original={fromText} modified={toText} />
                            </div>
                          </div>
                        );
                      })()}

                      {/* Versions List Table */}
                      <div className="border border-[#CBD2DC] rounded-lg overflow-hidden">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="bg-[#F7F7F4] border-b border-[#CBD2DC] text-[#5B6475] font-semibold">
                              <th className="py-2 px-3">Version</th>
                              <th className="py-2 px-3">Change Note</th>
                              <th className="py-2 px-3">Changed At</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#CBD2DC]">
                            {versions.map((v) => (
                              <tr key={v.id}>
                                <td className="py-2 px-3 font-mono font-bold text-[#0F766E]">v{v.version}</td>
                                <td className="py-2 px-3 text-[#1F2A44]">{v.change_note || "No note recorded"}</td>
                                <td className="py-2 px-3 text-[#5B6475]">
                                  {new Date(v.created_at).toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Tab 3: Edit Form (Brand Manager / Admin Only) */}
              {activeTab === "edit" && isManagerOrAdmin && (
                <form onSubmit={handleUpdate} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">Entry Title</label>
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      required
                      className="w-full px-3 py-2 rounded-lg border border-[#CBD2DC] text-xs focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">
                      Body / Definition / Guidance
                    </label>
                    <textarea
                      rows={4}
                      value={editBody}
                      onChange={(e) => setEditBody(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-[#CBD2DC] text-xs focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">
                      Classification Tier
                    </label>
                    <select
                      value={editClassification}
                      onChange={(e) => setEditClassification(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-[#CBD2DC] text-xs focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
                    >
                      <option value="public">Public</option>
                      <option value="internal">Internal</option>
                      <option value="confidential">Confidential</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#1F2A44] mb-1">
                      Change Note (Immutable Audit Log)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Updated clinical study expiration date to 2027"
                      value={editChangeNote}
                      onChange={(e) => setEditChangeNote(e.target.value)}
                      required
                      className="w-full px-3 py-2 rounded-lg border border-[#CBD2DC] text-xs focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-[#E2E5EA]">
                    <Button
                      type="button"
                      variant="danger"
                      size="sm"
                      onClick={handleRetire}
                      leftIcon={<Archive className="w-3.5 h-3.5" />}
                    >
                      Retire Entry
                    </Button>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setActiveTab("detail")}
                      >
                        Cancel
                      </Button>
                      <Button type="submit" variant="primary" size="sm" isLoading={isSaving}>
                        Save New Version
                      </Button>
                    </div>
                  </div>
                </form>
              )}
            </div>
          )}
        </Dialog>
      </AppShell>
    </AuthGuard>
  );
}
