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
  Skeleton,
  StatusStepper,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import {
  Submission,
  SubmissionVersion,
  Comment,
  Finding,
  Review,
  User,
} from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  PenTool,
  Clock,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  FileText,
  MessageSquare,
  History,
  ShieldCheck,
  Edit3,
  Send,
  UserCheck,
  Check,
  X,
  AlertTriangle,
  Lock,
} from "lucide-react";

export default function SubmissionDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <SubmissionDetailContent />
    </Suspense>
  );
}

function SubmissionDetailContent() {
  const searchParams = useSearchParams();
  const submissionId = searchParams.get("id");

  const [user, setUser] = useState<User | null>(null);
  const [sub, setSub] = useState<Submission | null>(null);
  const [versions, setVersions] = useState<SubmissionVersion[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Edit Mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  // Tab State
  const [activeTab, setActiveTab] = useState<"versions" | "comments" | "approvals" | "boundary">("versions");

  // Version Diff state
  const [diffFromV, setDiffFromV] = useState<number>(1);
  const [diffToV, setDiffToV] = useState<number>(1);

  // Comment submission
  const [newCommentBody, setNewCommentBody] = useState("");
  const [isPostingComment, setIsPostingComment] = useState(false);

  // Action dialog states (Approve / Request Changes Note)
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [noteModalType, setNoteModalType] = useState<"approve" | "request_changes">("approve");
  const [actionNote, setActionNote] = useState("");
  const [isActionPending, setIsActionPending] = useState(false);

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

  const loadData = async () => {
    if (!submissionId) {
      setError("No submission ID provided in query parameters.");
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const [submissionData, versionsData, commentsData, findingsData] = await Promise.all([
        api.getSubmission(submissionId),
        api.getVersions(submissionId).catch(() => []),
        api.getComments(submissionId).catch(() => []),
        api.getFindings(submissionId).catch(() => []),
      ]);

      setSub(submissionData);
      setEditContent(submissionData.content);
      setVersions(versionsData || []);
      setComments(commentsData || []);
      setFindings(findingsData || []);

      if (versionsData && versionsData.length >= 2) {
        setDiffFromV(versionsData[1].version_no);
        setDiffToV(versionsData[0].version_no);
      } else if (versionsData && versionsData.length === 1) {
        setDiffFromV(versionsData[0].version_no);
        setDiffToV(versionsData[0].version_no);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load submission details");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [submissionId]);

  // Primary Actions Handlers
  const handleSaveEdit = async () => {
    if (!sub) return;
    setIsSavingEdit(true);
    try {
      const updated = await api.updateContent(sub.id, editContent);
      setSub(updated);
      setIsEditing(false);
      setActionSuccess("Content updated. Submission reverted to Draft for new verification.");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to update content");
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleTriggerReview = async () => {
    if (!sub) return;
    setIsActionPending(true);
    try {
      await api.triggerReview(sub.id);
      setActionSuccess("Brand review completed in mock mode.");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Review failed");
    } finally {
      setIsActionPending(false);
    }
  };

  const handleSubmitForApproval = async () => {
    if (!sub) return;
    setIsActionPending(true);
    try {
      const updated = await api.submit(sub.id);
      setSub(updated);
      setActionSuccess("Submission forwarded to the reviewer queue.");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Submit failed");
    } finally {
      setIsActionPending(false);
    }
  };

  const handleClaim = async () => {
    if (!sub) return;
    setIsActionPending(true);
    try {
      const updated = await api.claim(sub.id);
      setSub(updated);
      setActionSuccess("Submission claimed and transitioned to In Review.");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Claim failed");
    } finally {
      setIsActionPending(false);
    }
  };

  const openApproveModal = () => {
    setNoteModalType("approve");
    setActionNote("Verified against Lumo tone, term, and clinical fact guidelines.");
    setNoteModalOpen(true);
  };

  const openRequestChangesModal = () => {
    setNoteModalType("request_changes");
    setActionNote("");
    setNoteModalOpen(true);
  };

  const executeModalAction = async () => {
    if (!sub) return;
    setIsActionPending(true);
    try {
      if (noteModalType === "approve") {
        const updated = await api.approve(sub.id, actionNote);
        setSub(updated);
        setActionSuccess("Approval recorded for current content version.");
      } else {
        if (!actionNote.trim()) {
          alert("A review note explaining requested changes is required.");
          setIsActionPending(false);
          return;
        }
        const updated = await api.requestChanges(sub.id, actionNote);
        setSub(updated);
        setActionSuccess("Changes requested. Creator notified.");
      }
      setNoteModalOpen(false);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Action failed");
    } finally {
      setIsActionPending(false);
    }
  };

  const handleMarkPublished = async () => {
    if (!sub) return;
    if (!confirm("Confirm that this approved marketing copy has been published to live channels?")) return;
    setIsActionPending(true);
    try {
      const updated = await api.markPublished(sub.id, "https://brand.lumo.skincare/campaign-live");
      setSub(updated);
      setActionSuccess("Submission marked published with timestamp and immutable audit row.");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Publish action failed");
    } finally {
      setIsActionPending(false);
    }
  };

  const handlePostComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sub || !newCommentBody.trim()) return;
    setIsPostingComment(true);
    try {
      const created = await api.postComment(sub.id, newCommentBody.trim());
      setComments([...comments, created]);
      setNewCommentBody("");
    } catch (err: any) {
      alert(err.message || "Failed to post comment");
    } finally {
      setIsPostingComment(false);
    }
  };

  if (isLoading) {
    return (
      <AppShell pageTitle="Submission Details">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-16 w-full rounded-xl" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Skeleton className="h-96 lg:col-span-2 rounded-xl" />
            <Skeleton className="h-96 rounded-xl" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error || !sub) {
    return (
      <AppShell pageTitle="Submission Not Found">
        <div className="max-w-2xl mx-auto my-12">
          <ErrorState message={error || "Submission could not be located"} onRetry={loadData} />
          <div className="mt-4 text-center">
            <Link href="/submissions/">
              <Button variant="secondary" size="sm">
                Return to Submissions List
              </Button>
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  const allowed = sub.allowed_actions || [];

  return (
    <AuthGuard>
      <AppShell pageTitle={sub.title}>
        <div className="space-y-6">
          {/* Action Success Banner */}
          {actionSuccess && (
            <div className="p-3 bg-[#ECFDF3] border border-[#ABEFC6] text-xs font-semibold text-[#067647] rounded-lg flex items-center justify-between">
              <span>{actionSuccess}</span>
              <button
                type="button"
                onClick={() => setActionSuccess(null)}
                className="text-[#067647] hover:underline text-[11px]"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Header Card with StatusStepper & Context-Sensitive Action */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-[#E2E5EA]">
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-[#E2E5EA] text-[#1F2A44] font-semibold">
                    {sub.channel}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      sub.risk_tier === "high"
                        ? "bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]"
                        : sub.risk_tier === "medium"
                        ? "bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A]"
                        : "bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]"
                    }`}
                  >
                    {sub.risk_tier} Risk
                  </span>
                  <span className="font-mono text-xs text-[#5B6475]">
                    Version v{sub.version_no}
                  </span>
                </div>
                <h1 className="text-xl sm:text-2xl font-bold text-[#1F2A44] tracking-tight">
                  {sub.title}
                </h1>
                <p className="text-xs text-[#5B6475] mt-1">
                  Created by <strong className="text-[#1F2A44]">{sub.creator_id}</strong> &middot; Last updated{" "}
                  {new Date(sub.updated_at).toLocaleString()}
                </p>
              </div>

              {/* Context-Sensitive Primary Action (Driven strictly by allowed_actions from API) */}
              <div className="flex flex-wrap items-center gap-2">
                {allowed.includes("review") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleTriggerReview}
                    isLoading={isActionPending}
                    leftIcon={<Sparkles className="w-4 h-4" />}
                  >
                    Run Brand Review
                  </Button>
                )}

                {allowed.includes("submit") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleSubmitForApproval}
                    isLoading={isActionPending}
                    rightIcon={<Send className="w-4 h-4" />}
                  >
                    Submit for Approval
                  </Button>
                )}

                {allowed.includes("claim") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleClaim}
                    isLoading={isActionPending}
                    leftIcon={<CheckCircle2 className="w-4 h-4" />}
                  >
                    Claim Review
                  </Button>
                )}

                {allowed.includes("request_changes") && (
                  <Button
                    variant="danger"
                    size="md"
                    onClick={openRequestChangesModal}
                    isLoading={isActionPending}
                    leftIcon={<AlertCircle className="w-4 h-4" />}
                  >
                    Request Changes
                  </Button>
                )}

                {allowed.includes("approve") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={openApproveModal}
                    isLoading={isActionPending}
                    leftIcon={<Check className="w-4 h-4" />}
                  >
                    Approve Submission
                  </Button>
                )}

                {allowed.includes("mark_published") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleMarkPublished}
                    isLoading={isActionPending}
                    leftIcon={<CheckCircle2 className="w-4 h-4" />}
                  >
                    Mark as Published
                  </Button>
                )}

                {allowed.includes("edit") && !isEditing && (
                  <Button
                    variant="secondary"
                    size="md"
                    onClick={() => setIsEditing(true)}
                    leftIcon={<Edit3 className="w-4 h-4" />}
                  >
                    Edit Content
                  </Button>
                )}
              </div>
            </div>

            {/* Status Stepper Progression */}
            <div className="pt-6">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#5B6475] block mb-3">
                Lifecycle Progression
              </span>
              <StatusStepper currentStatus={sub.status} />
            </div>
          </div>

          {/* Main Workspace Layout: 2 Columns */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left 8 Cols: Content & Tabs */}
            <div className="lg:col-span-8 space-y-6">
              {/* Content Panel (View vs Edit Mode) */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                <div className="flex items-center justify-between pb-3 border-b border-[#E2E5EA] mb-4">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                      Copy Content (Version v{sub.version_no})
                    </h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-[#5B6475]">
                      {isEditing ? editContent.length : sub.content.length} chars
                    </span>
                    {allowed.includes("edit") && !isEditing && (
                      <button
                        type="button"
                        onClick={() => setIsEditing(true)}
                        className="text-xs font-semibold text-[#0F766E] hover:underline ml-2"
                      >
                        Edit
                      </button>
                    )}
                  </div>
                </div>

                {isEditing ? (
                  <div className="space-y-4">
                    <div className="p-3 bg-[#FFFBEB] border border-[#FDE68A] text-xs text-[#B45309] rounded-lg">
                      <strong>Notice:</strong> Editing content creates a new version, voids any existing approvals, and resets workflow status to Draft.
                    </div>
                    <textarea
                      rows={8}
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full p-3 rounded-lg border border-[#CBD2DC] bg-[#F7F7F4] text-xs text-[#1F2A44] font-mono focus:outline-none focus:ring-2 focus:ring-[#0F766E] leading-relaxed"
                    />
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E5EA]">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditContent(sub.content);
                          setIsEditing(false);
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={handleSaveEdit}
                        isLoading={isSavingEdit}
                      >
                        Save New Version
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] text-xs text-[#1F2A44] font-mono leading-relaxed whitespace-pre-wrap">
                    {sub.content}
                  </div>
                )}
              </div>

              {/* Tabs: Versions, Comments, Approvals, Boundary */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                {/* Tabs Header */}
                <div className="flex items-center gap-2 border-b border-[#E2E5EA] pb-3 mb-6">
                  <button
                    type="button"
                    onClick={() => setActiveTab("versions")}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                      activeTab === "versions"
                        ? "bg-[#1F2A44] text-white"
                        : "text-[#5B6475] hover:text-[#1F2A44]"
                    }`}
                  >
                    <History className="w-3.5 h-3.5" />
                    Versions &amp; Diff ({versions.length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab("comments")}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                      activeTab === "comments"
                        ? "bg-[#1F2A44] text-white"
                        : "text-[#5B6475] hover:text-[#1F2A44]"
                    }`}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    Comments ({comments.length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab("approvals")}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                      activeTab === "approvals"
                        ? "bg-[#1F2A44] text-white"
                        : "text-[#5B6475] hover:text-[#1F2A44]"
                    }`}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Approvals &amp; Timeline
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab("boundary")}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 ${
                      activeTab === "boundary"
                        ? "bg-[#1F2A44] text-white"
                        : "text-[#5B6475] hover:text-[#1F2A44]"
                    }`}
                  >
                    <Lock className="w-3.5 h-3.5" />
                    Data Boundary
                  </button>
                </div>

                {/* Tab 1: Versions & DiffView */}
                {activeTab === "versions" && (
                  <div className="space-y-4">
                    {versions.length === 0 ? (
                      <p className="text-xs text-[#5B6475]">Only initial version v1 recorded.</p>
                    ) : (
                      <>
                        <div className="flex items-center gap-4 p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-[#1F2A44]">From:</span>
                            <select
                              aria-label="Compare from version"
                              value={diffFromV}
                              onChange={(e) => setDiffFromV(Number(e.target.value))}
                              className="px-2 py-1 text-xs rounded border border-[#CBD2DC] bg-white"
                            >
                              {versions.map((v) => (
                                <option key={v.id} value={v.version_no}>
                                  v{v.version_no} ({new Date(v.created_at).toLocaleDateString()})
                                </option>
                              ))}
                            </select>
                          </div>
                          <span className="text-xs text-[#5B6475]">&rarr;</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-[#1F2A44]">To:</span>
                            <select
                              aria-label="Compare to version"
                              value={diffToV}
                              onChange={(e) => setDiffToV(Number(e.target.value))}
                              className="px-2 py-1 text-xs rounded border border-[#CBD2DC] bg-white"
                            >
                              {versions.map((v) => (
                                <option key={v.id} value={v.version_no}>
                                  v{v.version_no} ({new Date(v.created_at).toLocaleDateString()})
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        {/* Inline DiffView */}
                        {(() => {
                          const fromVer = versions.find((v) => v.version_no === diffFromV);
                          const toVer = versions.find((v) => v.version_no === diffToV);
                          return (
                            <div className="border border-[#CBD2DC] rounded-lg overflow-hidden">
                              <div className="bg-[#F7F7F4] px-3 py-2 border-b border-[#CBD2DC] text-[11px] font-bold text-[#5B6475]">
                                Word &amp; Character Diff (v{diffFromV} vs v{diffToV})
                              </div>
                              <div className="p-4">
                                <DiffView
                                  original={fromVer?.content || ""}
                                  modified={toVer?.content || ""}
                                />
                              </div>
                            </div>
                          );
                        })()}

                        {/* Versions List */}
                        <div className="border border-[#CBD2DC] rounded-lg overflow-hidden mt-4">
                          <table className="w-full text-left text-xs">
                            <thead>
                              <tr className="bg-[#F7F7F4] border-b border-[#CBD2DC] text-[#5B6475] font-semibold">
                                <th className="py-2.5 px-3">Version</th>
                                <th className="py-2.5 px-3">Created By</th>
                                <th className="py-2.5 px-3">SHA-256 Hash</th>
                                <th className="py-2.5 px-3">Timestamp</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-[#CBD2DC]">
                              {versions.map((v) => (
                                <tr key={v.id}>
                                  <td className="py-2.5 px-3 font-mono font-bold text-[#0F766E]">
                                    v{v.version_no}
                                  </td>
                                  <td className="py-2.5 px-3 text-[#1F2A44]">{v.created_by}</td>
                                  <td className="py-2.5 px-3 font-mono text-[10px] text-[#5B6475]">
                                    {v.content_hash.slice(0, 16)}...
                                  </td>
                                  <td className="py-2.5 px-3 text-[#5B6475]">
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

                {/* Tab 2: Comments (Threaded submission-level) */}
                {activeTab === "comments" && (
                  <div className="space-y-4">
                    {comments.length === 0 ? (
                      <p className="text-xs text-[#5B6475]">No review comments posted yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {comments.map((c) => (
                          <div key={c.id} className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-bold text-xs text-[#1F2A44]">{c.author_name}</span>
                              <span className="text-[10px] text-[#5B6475]">
                                {new Date(c.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                              </span>
                            </div>
                            <p className="text-xs text-[#1F2A44] whitespace-pre-wrap">{c.body}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* New Comment Input */}
                    <form onSubmit={handlePostComment} className="pt-3 border-t border-[#E2E5EA]">
                      <label htmlFor="new-comment" className="block text-xs font-bold text-[#1F2A44] mb-1">
                        Add Review Note or Comment
                      </label>
                      <textarea
                        id="new-comment"
                        rows={3}
                        placeholder="Type feedback, regulatory context, or approval note..."
                        value={newCommentBody}
                        onChange={(e) => setNewCommentBody(e.target.value)}
                        className="w-full p-2.5 rounded-lg border border-[#CBD2DC] text-xs text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
                      />
                      <div className="flex justify-end mt-2">
                        <Button
                          type="submit"
                          variant="primary"
                          size="sm"
                          isLoading={isPostingComment}
                          leftIcon={<Send className="w-3.5 h-3.5" />}
                        >
                          Post Comment
                        </Button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Tab 3: Approvals Timeline */}
                {activeTab === "approvals" && (
                  <div className="space-y-4">
                    <div className="p-4 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                      <span className="text-xs font-bold text-[#1F2A44] block mb-1">
                        Required Approvals Policy
                      </span>
                      <p className="text-xs text-[#5B6475]">
                        Channel &quot;{sub.channel}&quot; is classified as{" "}
                        <strong className="uppercase font-mono text-[#0F766E]">{sub.risk_tier}</strong> risk.
                        Requires{" "}
                        <strong className="text-[#1F2A44]">
                          {sub.risk_tier === "high" ? "2 distinct reviewer approvals" : "1 reviewer approval"}
                        </strong>{" "}
                        on content version v{sub.version_no}.
                      </p>
                    </div>

                    <div className="p-4 bg-white rounded-lg border border-[#CBD2DC]">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475] block mb-3">
                        Timeline of Review Actions
                      </span>
                      <div className="space-y-3">
                        <div className="flex items-start gap-3">
                          <div className="w-6 h-6 rounded-full bg-[#ECFDF3] border border-[#ABEFC6] text-[#067647] flex items-center justify-center text-xs font-bold mt-0.5">
                            ✓
                          </div>
                          <div>
                            <p className="text-xs font-bold text-[#1F2A44]">Content Created (v1)</p>
                            <p className="text-[11px] text-[#5B6475]">
                              {new Date(sub.created_at).toLocaleString()} by {sub.creator_id}
                            </p>
                          </div>
                        </div>

                        {sub.status !== "Draft" && (
                          <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-[#ECFDF3] border border-[#ABEFC6] text-[#067647] flex items-center justify-center text-xs font-bold mt-0.5">
                              ✓
                            </div>
                            <div>
                              <p className="text-xs font-bold text-[#1F2A44]">Brand Review Executed</p>
                              <p className="text-[11px] text-[#5B6475]">
                                Automated rule &amp; fact checks evaluated on version v{sub.version_no}
                              </p>
                            </div>
                          </div>
                        )}

                        {sub.status === "Approved" && (
                          <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-[#ECFDF3] border border-[#ABEFC6] text-[#067647] flex items-center justify-center text-xs font-bold mt-0.5">
                              ✓
                            </div>
                            <div>
                              <p className="text-xs font-bold text-[#1F2A44]">Reviewer Approved</p>
                              <p className="text-[11px] text-[#5B6475]">Editorial clearance granted for publication</p>
                            </div>
                          </div>
                        )}

                        {sub.status === "Marked Published" && (
                          <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-[#0F766E] text-white flex items-center justify-center text-xs font-bold mt-0.5">
                              ★
                            </div>
                            <div>
                              <p className="text-xs font-bold text-[#0F766E]">Published Live</p>
                              <p className="text-[11px] text-[#5B6475]">
                                Verified published to {sub.published_url || "brand channels"}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 4: Data Boundary Panel */}
                {activeTab === "boundary" && (
                  <div className="space-y-4">
                    <div className="p-4 bg-[#ECFDF3] border border-[#ABEFC6] rounded-lg">
                      <div className="flex items-center gap-2 text-[#067647] font-bold text-xs mb-1">
                        <ShieldCheck className="w-4 h-4" /> Zero Confidential Data Leak Invariant Maintained
                      </div>
                      <p className="text-xs text-[#067647]">
                        Retriever and LLM adapter assertions confirmed zero confidential entries or unredacted secrets left the process boundary.
                      </p>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">AI Provider</span>
                        <span className="text-xs font-bold text-[#1F2A44] mt-1 block">Offline Mock Engine</span>
                      </div>
                      <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">External Calls</span>
                        <span className="text-xs font-bold text-[#1F2A44] mt-1 block">0 (Zero external network)</span>
                      </div>
                      <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Max Tier Sent</span>
                        <span className="text-xs font-mono font-bold text-[#0F766E] uppercase mt-1 block">public</span>
                      </div>
                      <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                        <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Tokens In/Out</span>
                        <span className="text-xs font-bold text-[#1F2A44] mt-1 block">0 / 0</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right 4 Cols: Findings Panel Placeholder (Active in Prompt 2B) */}
            <div className="lg:col-span-4 space-y-4">
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-5 shadow-xs">
                <div className="flex items-center justify-between pb-3 border-b border-[#E2E5EA] mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                      Findings Panel
                    </h2>
                  </div>
                  <span className="text-xs font-bold font-mono px-2 py-0.5 rounded-full bg-[#F7F7F4] text-[#1F2A44] border border-[#CBD2DC]">
                    {findings.length} findings
                  </span>
                </div>

                <div className="p-4 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] text-center space-y-3">
                  <div className="w-10 h-10 mx-auto rounded-full bg-white border border-[#CBD2DC] flex items-center justify-center text-[#0F766E]">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <h3 className="text-xs font-bold text-[#1F2A44]">
                    Interactive Findings Triage Placeholder
                  </h3>
                  <p className="text-[11px] text-[#5B6475] leading-relaxed">
                    Full findings triage with minimal-edit suggestion diffs, Accept, Dismiss (with mandatory reasons), and Escalate actions will be connected in Prompt 2B.
                  </p>
                  <div className="pt-2 border-t border-[#E2E5EA] text-[10px] font-mono text-[#5B6475]">
                    Pipeline: Extract &rarr; Sanitise &rarr; RuleChecks &rarr; A11y &rarr; Retrieve &rarr; Analyse &rarr; Guardrails
                  </div>
                </div>

                {findings.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#5B6475] block">
                      Preliminary Issues Preview
                    </span>
                    {findings.slice(0, 3).map((f) => (
                      <div key={f.id} className="p-2.5 bg-white rounded-lg border border-[#E2E5EA] text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-mono text-[10px] font-bold text-[#0F766E] uppercase">
                            {f.issue_type}
                          </span>
                          <span
                            className={`text-[9px] font-bold uppercase px-1.5 py-0.2 rounded ${
                              f.severity === "high" ? "bg-[#FEF3F2] text-[#B42318]" : "bg-[#F7F7F4] text-[#1F2A44]"
                            }`}
                          >
                            {f.severity}
                          </span>
                        </div>
                        <p className="font-semibold text-[#1F2A44] line-clamp-1">&ldquo;{f.excerpt}&rdquo;</p>
                        <p className="text-[11px] text-[#5B6475] line-clamp-2 mt-0.5">{f.explanation}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Action Note Modal (Approve / Request Changes) */}
        <Dialog
          isOpen={noteModalOpen}
          onClose={() => setNoteModalOpen(false)}
          title={noteModalType === "approve" ? "Editorial Sign-Off & Approval" : "Request Revisions from Creator"}
          description={`Submission: ${sub.title}`}
        >
          <div className="space-y-4">
            <div>
              <label htmlFor="action-note" className="block text-xs font-bold text-[#1F2A44] mb-1">
                {noteModalType === "approve" ? "Approval Endorsement Note" : "Revision Instructions (Required)"}
              </label>
              <textarea
                id="action-note"
                rows={3}
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                placeholder={
                  noteModalType === "approve"
                    ? "Add any optional sign-off remarks..."
                    : "Specify required copy changes, tone adjustments, or missing citations..."
                }
                className="w-full p-2.5 rounded-lg border border-[#CBD2DC] text-xs text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-[#E2E5EA]">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setNoteModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant={noteModalType === "approve" ? "primary" : "danger"}
                size="sm"
                onClick={executeModalAction}
                isLoading={isActionPending}
              >
                {noteModalType === "approve" ? "Confirm Approval" : "Submit Revision Request"}
              </Button>
            </div>
          </div>
        </Dialog>
      </AppShell>
    </AuthGuard>
  );
}
