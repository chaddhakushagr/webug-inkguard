"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
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
import { Submission, User } from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  PenTool,
  Plus,
  Search,
  Filter,
  ArrowRight,
  FileText,
  Clock,
  Sparkles,
  ChevronRight,
} from "lucide-react";

export default function SubmissionsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <SubmissionsContent />
    </Suspense>
  );
}

function SubmissionsContent() {
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get("status") || "all";

  const [user, setUser] = useState<User | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>(initialStatus);
  const [channelFilter, setChannelFilter] = useState<string>("all");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

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

  const loadSubmissions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getSubmissions(statusFilter, channelFilter, riskFilter);
      setSubmissions(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load submissions");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSubmissions();
  }, [statusFilter, channelFilter, riskFilter]);

  const filteredSubmissions = submissions.filter((s) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return s.title.toLowerCase().includes(q) || s.content.toLowerCase().includes(q);
  });

  return (
    <AuthGuard>
      <AppShell pageTitle="Submissions &amp; Marketing Copy">
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <PenTool className="w-5 h-5 text-[#0F766E]" />
                <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                  Marketing Copy Submissions
                </h1>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
                Draft, verify, review, and approve pre-publication copy against Lumo brand guidelines.
              </p>
            </div>
            <Link href="/submissions/new/">
              <Button variant="primary" size="md" leftIcon={<Plus className="w-4 h-4" />}>
                New Submission
              </Button>
            </Link>
          </div>

          {/* Filter Bar */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-4 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
            {/* Search Input */}
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-[#5B6475] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search copy or title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-[#F7F7F4] text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              />
            </div>

            {/* Filter Dropdowns */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Status Filter */}
              <select
                aria-label="Filter by status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Statuses</option>
                <option value="Draft">Draft</option>
                <option value="Checked">Checked</option>
                <option value="Submitted">Submitted</option>
                <option value="In Review">In Review</option>
                <option value="Changes Requested">Changes Requested</option>
                <option value="Approved">Approved</option>
                <option value="Marked Published">Marked Published</option>
              </select>

              {/* Channel Filter */}
              <select
                aria-label="Filter by channel"
                value={channelFilter}
                onChange={(e) => setChannelFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Channels</option>
                <option value="social">Social Media</option>
                <option value="email">Email</option>
                <option value="blog">Blog</option>
                <option value="web">Website</option>
                <option value="press_release">Press Release</option>
              </select>

              {/* Risk Tier Filter */}
              <select
                aria-label="Filter by risk tier"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Risk Tiers</option>
                <option value="low">Low Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="high">High Risk</option>
              </select>
            </div>
          </div>

          {/* Submissions Table */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden">
            {isLoading ? (
              <div className="p-8 space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : error ? (
              <ErrorState message={error} onRetry={loadSubmissions} />
            ) : filteredSubmissions.length === 0 ? (
              <EmptyState
                title="No submissions found"
                description="Create a new submission or change your filter selection."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                      <th className="py-3 px-4">Title &amp; Snippet</th>
                      <th className="py-3 px-4">Channel</th>
                      <th className="py-3 px-4">Risk Tier</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Version</th>
                      <th className="py-3 px-4">Last Updated</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E5EA]">
                    {filteredSubmissions.map((s) => (
                      <tr
                        key={s.id}
                        className="hover:bg-[#F7F7F4]/70 transition-colors cursor-pointer"
                        onClick={() => (window.location.href = `/submission/?id=${s.id}`)}
                      >
                        <td className="py-3 px-4">
                          <span className="font-bold text-[#1F2A44] block hover:text-[#0F766E]">
                            {s.title}
                          </span>
                          <span className="text-[11px] text-[#5B6475] line-clamp-1 mt-0.5">
                            {s.content.includes("OCR unavailable on this host")
                              ? "Image submission · Text extraction requires Tesseract"
                              : s.content}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono capitalize px-2 py-0.5 rounded bg-[#E2E5EA] text-[#1F2A44]">
                            {s.channel}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              s.risk_tier === "high"
                                ? "bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]"
                                : s.risk_tier === "medium"
                                ? "bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]"
                                : "bg-[#F7F7F4] text-[#1F2A44] border border-[#CBD2DC]"
                            }`}
                          >
                            {s.risk_tier}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge status={s.status} />
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-[#1F2A44]">v{s.version_no}</td>
                        <td className="py-3 px-4 text-[#5B6475]">
                          {new Date(s.updated_at || s.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                          <Link href={`/submission/?id=${s.id}`}>
                            <Button variant="secondary" size="xs">
                              Open &rarr;
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
      </AppShell>
    </AuthGuard>
  );
}
