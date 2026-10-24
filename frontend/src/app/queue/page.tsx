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
import { Submission, User } from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  CheckSquare,
  Clock,
  Filter,
  Search,
  UserCheck,
  ArrowRight,
  ShieldAlert,
  Inbox,
  CheckCircle2,
} from "lucide-react";

export default function ReviewerQueuePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <ReviewerQueueContent />
    </Suspense>
  );
}

function ReviewerQueueContent() {
  const [user, setUser] = useState<User | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Queue View Tab: 'unassigned' vs 'mine'
  const [queueTab, setQueueTab] = useState<"unassigned" | "mine">("unassigned");

  // Filters & Sorting
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [channelFilter, setChannelFilter] = useState<string>("all");
  const [sortAge, setSortAge] = useState<"oldest" | "newest">("oldest");
  const [claimingId, setClaimingId] = useState<string | null>(null);

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

  const loadQueue = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getSubmissions();
      setSubmissions(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load reviewer queue");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleClaimItem = async (e: React.MouseEvent, subId: string) => {
    e.stopPropagation();
    setClaimingId(subId);
    try {
      await api.claim(subId);
      await loadQueue();
      setQueueTab("mine");
    } catch (err: any) {
      alert(err.message || "Failed to claim submission");
    } finally {
      setClaimingId(null);
    }
  };

  // Filter items by tab
  const unassignedItems = submissions.filter((s) => s.status === "Submitted");
  const myClaimedItems = submissions.filter(
    (s) => s.status === "In Review" && (s.assignee_id === user?.id || !s.assignee_id)
  );

  const currentList = queueTab === "unassigned" ? unassignedItems : myClaimedItems;

  const filteredItems = currentList
    .filter((s) => {
      if (riskFilter !== "all" && s.risk_tier !== riskFilter) return false;
      if (channelFilter !== "all" && s.channel !== channelFilter) return false;
      return true;
    })
    .sort((a, b) => {
      const timeA = new Date(a.updated_at || a.created_at).getTime();
      const timeB = new Date(b.updated_at || b.created_at).getTime();
      return sortAge === "oldest" ? timeA - timeB : timeB - timeA;
    });

  const getAgeLabel = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - d.getTime()) / (1000 * 3600));
    if (diffHours < 1) return "Just now";
    if (diffHours === 1) return "1 hour ago";
    if (diffHours < 24) return `${diffHours} hours ago`;
    const days = Math.floor(diffHours / 24);
    return `${days} day${days > 1 ? "s" : ""} ago`;
  };

  return (
    <AuthGuard allowedRoles={["reviewer", "brand_manager", "admin"]}>
      <AppShell pageTitle="Reviewer Queue">
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-5 h-5 text-[#0F766E]" />
                <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                  Editorial Reviewer Queue
                </h1>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
                Claim pending submissions, inspect governance checks, and issue editorial sign-offs.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]">
                {unassignedItems.length} awaiting review
              </span>
            </div>
          </div>

          {/* Queue Tabs & Filters Bar */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-4 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
            {/* Queue Tabs */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setQueueTab("unassigned")}
                className={`px-3.5 py-2 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                  queueTab === "unassigned"
                    ? "bg-[#1F2A44] text-white"
                    : "text-[#5B6475] hover:text-[#1F2A44] hover:bg-[#F7F7F4]"
                }`}
              >
                <Inbox className="w-3.5 h-3.5" />
                Unassigned Queue ({unassignedItems.length})
              </button>

              <button
                type="button"
                onClick={() => setQueueTab("mine")}
                className={`px-3.5 py-2 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                  queueTab === "mine"
                    ? "bg-[#1F2A44] text-white"
                    : "text-[#5B6475] hover:text-[#1F2A44] hover:bg-[#F7F7F4]"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                My Claimed Items ({myClaimedItems.length})
              </button>
            </div>

            {/* Filter & Sort Controls */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Risk Filter */}
              <select
                aria-label="Filter queue by risk tier"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Risk Tiers</option>
                <option value="low">Low Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="high">High Risk</option>
              </select>

              {/* Channel Filter */}
              <select
                aria-label="Filter queue by channel"
                value={channelFilter}
                onChange={(e) => setChannelFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Channels</option>
                <option value="social">Social</option>
                <option value="email">Email</option>
                <option value="blog">Blog</option>
                <option value="web">Web</option>
                <option value="press_release">Press Release</option>
              </select>

              {/* Age Sort */}
              <select
                aria-label="Sort queue by submission age"
                value={sortAge}
                onChange={(e) => setSortAge(e.target.value as any)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="oldest">Oldest First (SLA Priority)</option>
                <option value="newest">Newest First</option>
              </select>
            </div>
          </div>

          {/* Queue List Table */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden">
            {isLoading ? (
              <div className="p-8 space-y-3">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : error ? (
              <ErrorState message={error} onRetry={loadQueue} />
            ) : filteredItems.length === 0 ? (
              <EmptyState
                title={
                  queueTab === "unassigned"
                    ? "Unassigned queue is empty"
                    : "You have no claimed submissions"
                }
                description={
                  queueTab === "unassigned"
                    ? "All submitted copy has been claimed or resolved."
                    : "Switch to the Unassigned Queue tab to claim a pending submission."
                }
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                      <th className="py-3 px-4">Title &amp; Snippet</th>
                      <th className="py-3 px-4">Channel</th>
                      <th className="py-3 px-4">Risk Tier</th>
                      <th className="py-3 px-4">Creator &amp; Team</th>
                      <th className="py-3 px-4">Submitted Age</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E5EA]">
                    {filteredItems.map((s) => (
                      <tr
                        key={s.id}
                        className="hover:bg-[#F7F7F4]/70 transition-colors cursor-pointer"
                        onClick={() => (window.location.href = `/submission/?id=${s.id}`)}
                      >
                        <td className="py-3.5 px-4 max-w-xs">
                          <span className="font-bold text-[#1F2A44] block hover:text-[#0F766E]">
                            {s.title}
                          </span>
                          <span className="text-[11px] text-[#5B6475] line-clamp-1 mt-0.5">
                            {s.content}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="font-mono capitalize px-2 py-0.5 rounded bg-[#E2E5EA] text-[#1F2A44]">
                            {s.channel}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
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
                        <td className="py-3.5 px-4">
                          <span className="text-[#1F2A44] font-medium block">{s.creator_id}</span>
                          <span className="text-[11px] text-[#5B6475]">{s.team_id || "Brand Marketing"}</span>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-[#5B6475]">
                          <span className="inline-flex items-center gap-1">
                            <Clock className="w-3 h-3 text-[#5B6475]" />
                            {getAgeLabel(s.updated_at || s.created_at)}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <Badge status={s.status} />
                        </td>
                        <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                          {queueTab === "unassigned" ? (
                            <Button
                              variant="primary"
                              size="xs"
                              onClick={(e) => handleClaimItem(e, s.id)}
                              isLoading={claimingId === s.id}
                              leftIcon={<UserCheck className="w-3 h-3" />}
                            >
                              Claim
                            </Button>
                          ) : (
                            <Link href={`/submission/?id=${s.id}`}>
                              <Button variant="secondary" size="xs">
                                Review &rarr;
                              </Button>
                            </Link>
                          )}
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
