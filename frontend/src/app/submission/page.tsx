"use client";

import React, { Suspense, useEffect, useState, useRef } from "react";
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
  HighlightedText,
  ModeChip,
  Skeleton,
  StatusStepper,
  Banner,
  toast,
} from "@/shared/ui";
import { api, getApiBase } from "@/shared/api/client";
import {
  Submission,
  SubmissionVersion,
  Comment,
  Finding,
  Review,
  User,
} from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import { FindingCard } from "@/features/findings/FindingCard";
import { DismissDialog } from "@/features/findings/DismissDialog";
import { EscalateDialog } from "@/features/findings/EscalateDialog";
import { KBCitationDialog } from "@/features/findings/KBCitationDialog";
import { ReviewProgressBanner } from "@/features/findings/ReviewProgressBanner";
import { DataBoundaryView } from "@/features/submissions/DataBoundaryView";
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
  Filter,
  RotateCw,
  Search,
  Info,
  ExternalLink,
  Image as LucideImage,
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
  const [review, setReview] = useState<Review | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Review Engine execution state
  const [isReviewRunning, setIsReviewRunning] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Mobile / Narrow screen pane toggle: "content" vs "findings"
  const [mobilePane, setMobilePane] = useState<"content" | "findings">("content");

  // Selection & Bi-directional focus
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  // Findings Filters
  const [filterType, setFilterType] = useState<string>("all");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterSource, setFilterSource] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");

  // Edit Mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  // Left Pane Tabs: versions, comments, approvals, boundary
  const [activeTab, setActiveTab] = useState<"versions" | "comments" | "approvals" | "boundary">("versions");

  // Version Diff state
  const [diffFromV, setDiffFromV] = useState<number>(1);
  const [diffToV, setDiffToV] = useState<number>(1);

  // Comment submission (Submission-level)
  const [newCommentBody, setNewCommentBody] = useState("");
  const [isPostingComment, setIsPostingComment] = useState(false);

  // Workflow Dialog states (Approve / Request Changes Note)
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [noteModalType, setNoteModalType] = useState<"approve" | "request_changes">("approve");
  const [actionNote, setActionNote] = useState("");
  const [isActionPending, setIsActionPending] = useState(false);

  // Triage Dialogs state
  const [dismissFinding, setDismissFinding] = useState<Finding | null>(null);
  const [escalateFinding, setEscalateFinding] = useState<Finding | null>(null);
  const [citationDialog, setCitationDialog] = useState<{
    isOpen: boolean;
    code: string | null;
    version?: number | null;
  }>({ isOpen: false, code: null });

  // Load User from Session
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

  // Clean up polling interval
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Main data loader
  const loadData = async (silent = false) => {
    if (!submissionId) {
      setError("No submission ID provided in query parameters.");
      setIsLoading(false);
      return;
    }
    if (!silent) setIsLoading(true);
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

      // If findings exist and we have a review_id, load the review record
      if (findingsData && findingsData.length > 0 && findingsData[0].review_id) {
        api
          .getReview(findingsData[0].review_id)
          .then((rev) => setReview(rev))
          .catch(() => {});
      }
    } catch (err: any) {
      setError(err.message || "Failed to load submission details");
    } finally {
      if (!silent) setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [submissionId]);

  // Bi-directional selection handler
  const handleSelectFinding = (findingId: string) => {
    setSelectedFindingId(findingId);

    // Scroll to finding card in right pane
    setTimeout(() => {
      const cardEl = document.getElementById(`finding-card-${findingId}`);
      if (cardEl) {
        cardEl.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      // Also scroll to highlighted text span
      const highlightEl = document.getElementById(`highlight-${findingId}`);
      if (highlightEl) {
        highlightEl.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 50);
  };

  // Review Trigger & Live Polling (5 Stages)
  const handleTriggerReview = async () => {
    if (!sub || isReviewRunning) return;
    setIsReviewRunning(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const initialRev = await api.triggerReview(sub.id);
      setReview(initialRev);

      // Start polling review progress
      const revId = initialRev.id;
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

      pollIntervalRef.current = setInterval(async () => {
        try {
          const currentRev = await api.getReview(revId);
          setReview(currentRev);

          if (currentRev.status === "completed" || currentRev.status === "failed") {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            setIsReviewRunning(false);
            await loadData(true);

            if (currentRev.status === "completed") {
              const msg = `Brand review completed (${currentRev.findings_count} findings detected). Submission status updated to Checked.`;
              setActionSuccess(msg);
              toast(msg, "success");
            } else {
              const err = currentRev.error || "Review pipeline failed during execution";
              setActionError(err);
              toast(err, "error");
            }
          }
        } catch (pollErr: any) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setIsReviewRunning(false);
          const err = pollErr.message || "Lost connection to review orchestrator";
          setActionError(err);
          toast(err, "error");
        }
      }, 450);
    } catch (err: any) {
      setIsReviewRunning(false);
      const errMsg = err.message || "Failed to initiate brand review";
      setActionError(errMsg);
      toast(errMsg, "error");
    }
  };

  // Finding Triage Actions
  const handleAcceptFinding = async (findingId: string) => {
    setIsActionPending(true);
    setActionError(null);
    try {
      await api.acceptFinding(findingId);
      const msg = "Suggested fix accepted! New content version created, approvals reset, and status reverted to Draft.";
      setActionSuccess(msg);
      toast(msg, "success");
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Failed to accept fix. Underlying copy may have changed.";
      setActionError(errMsg);
      toast(errMsg, "error");
    } finally {
      setIsActionPending(false);
    }
  };

  const handleConfirmDismiss = async (reasonCode: string, reasonText: string) => {
    if (!dismissFinding) return;
    setIsActionPending(true);
    setActionError(null);
    try {
      await api.dismissFinding(dismissFinding.id, reasonCode, reasonText);
      const msg = "Finding dismissed and recorded in the append-only audit trail.";
      setActionSuccess(msg);
      toast(msg, "info");
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Failed to dismiss finding";
      setActionError(errMsg);
      toast(errMsg, "error");
      throw err;
    } finally {
      setIsActionPending(false);
    }
  };

  const handleConfirmEscalate = async (note: string) => {
    if (!escalateFinding) return;
    setIsActionPending(true);
    setActionError(null);
    try {
      await api.escalateFinding(escalateFinding.id, note);
      const msg = "Finding escalated to brand manager. Revision ticket attached.";
      setActionSuccess(msg);
      toast(msg, "info");
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Failed to escalate finding";
      setActionError(errMsg);
      toast(errMsg, "error");
      throw err;
    } finally {
      setIsActionPending(false);
    }
  };

  const handlePostFindingComment = async (body: string, findingId: string) => {
    if (!sub) return;
    try {
      const created = await api.postComment(sub.id, body, findingId);
      setComments((prev) => [...prev, created]);
      toast("Comment posted.", "success");
    } catch (err: any) {
      const errMsg = err.message || "Failed to post finding comment";
      toast(errMsg, "error");
    }
  };

  // Content Edit Handler
  const handleSaveEdit = async () => {
    if (!sub) return;
    setIsSavingEdit(true);
    setActionError(null);
    try {
      const updated = await api.updateContent(sub.id, editContent);
      setSub(updated);
      setIsEditing(false);
      const msg = "Content updated. Submission reverted to Draft. Run Re-check to verify.";
      setActionSuccess(msg);
      toast(msg, "success");
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Failed to update copy";
      setActionError(errMsg);
      toast(errMsg, "error");
    } finally {
      setIsSavingEdit(false);
    }
  };

  // Workflow Action Handlers
  const handleSubmitForApproval = async () => {
    if (!sub || isActionPending) return;
    setIsActionPending(true);
    setActionError(null);
    try {
      const updated = await api.submit(sub.id);
      setSub(updated);
      const msg = "Submission forwarded to the reviewer queue.";
      setActionSuccess(msg);
      toast(msg, "success");
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Submit failed";
      setActionError(errMsg);
      toast(errMsg, "error");
    } finally {
      setIsActionPending(false);
    }
  };

  const handleClaim = async () => {
    if (!sub || isActionPending) return;
    setIsActionPending(true);
    setActionError(null);
    try {
      const updated = await api.claim(sub.id);
      setSub(updated);
      const msg = "Submission claimed and transitioned to In Review.";
      setActionSuccess(msg);
      toast(msg, "success");
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Claim failed";
      setActionError(errMsg);
      toast(errMsg, "error");
    } finally {
      setIsActionPending(false);
    }
  };

  const executeModalAction = async () => {
    if (!sub || isActionPending) return;
    setIsActionPending(true);
    setActionError(null);
    try {
      if (noteModalType === "approve") {
        const updated = await api.approve(sub.id, actionNote);
        setSub(updated);
        const msg = "Approval recorded for current content version.";
        setActionSuccess(msg);
        toast(msg, "success");
      } else {
        if (!actionNote.trim()) {
          toast("A review note explaining requested changes is required.", "error");
          setIsActionPending(false);
          return;
        }
        const updated = await api.requestChanges(sub.id, actionNote);
        setSub(updated);
        const msg = "Changes requested. Creator notified.";
        setActionSuccess(msg);
        toast(msg, "info");
      }
      setNoteModalOpen(false);
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Action failed";
      setActionError(errMsg);
      toast(errMsg, "error");
    } finally {
      setIsActionPending(false);
    }
  };

  const handleMarkPublished = async () => {
    if (!sub || isActionPending) return;
    if (!confirm("Confirm that this approved marketing copy has been published to live channels?")) return;
    setIsActionPending(true);
    setActionError(null);
    try {
      const updated = await api.markPublished(sub.id, "https://brand.lumo.skincare/campaign-live");
      setSub(updated);
      const msg = "Submission marked published with timestamp and immutable audit row.";
      setActionSuccess(msg);
      toast(msg, "success");
      await loadData(true);
    } catch (err: any) {
      const errMsg = err.message || "Publish action failed";
      setActionError(errMsg);
      toast(errMsg, "error");
    } finally {
      setIsActionPending(false);
    }
  };

  const handlePostSubmissionComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sub || !newCommentBody.trim()) return;
    setIsPostingComment(true);
    try {
      const created = await api.postComment(sub.id, newCommentBody.trim());
      setComments((prev) => [...prev, created]);
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
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <Skeleton className="h-96 lg:col-span-7 rounded-xl" />
            <Skeleton className="h-96 lg:col-span-5 rounded-xl" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error || !sub) {
    return (
      <AppShell pageTitle="Submission Not Found">
        <div className="max-w-2xl mx-auto my-12">
          <ErrorState message={error || "Submission could not be located"} onRetry={() => loadData()} />
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
  const openHighSeverityCount = findings.filter(
    (f) => f.severity === "high" && f.status === "open"
  ).length;

  // Filtered Findings
  const filteredFindings = findings.filter((f) => {
    if (filterType !== "all" && f.issue_type !== filterType) return false;
    if (filterSeverity !== "all" && f.severity !== filterSeverity) return false;
    if (filterSource !== "all" && f.source !== filterSource) return false;
    if (filterStatus !== "all" && f.status !== filterStatus) return false;
    return true;
  });

  const totalOpen = findings.filter((f) => f.status === "open").length;
  const totalRule = findings.filter((f) => f.source === "rule").length;
  const totalAI = findings.filter((f) => f.source === "ai").length;

  const isReviewer = user?.role === "reviewer";

  const isDocxOrPdf =
    sub.source === "upload_docx" ||
    sub.source === "upload_pdf" ||
    versions.some((v) => v.source === "upload_docx" || v.source === "upload_pdf") ||
    sub.title.toLowerCase().endsWith(".docx") ||
    sub.title.toLowerCase().endsWith(".pdf");

  const policyFindings = findings.filter((f) => f.is_policy !== false);
  const isOCRUnavailable = sub.content.includes("OCR unavailable on this host");

  return (
    <AuthGuard>
      <AppShell pageTitle={sub.title}>
        <div className="space-y-6">
          {/* Action Success / Error Notifications */}
          {actionSuccess && (
            <Banner
              type="success"
              title="Success"
              action={
                <button
                  type="button"
                  onClick={() => setActionSuccess(null)}
                  className="text-[#067647] hover:underline text-xs font-semibold"
                >
                  Dismiss
                </button>
              }
            >
              {actionSuccess}
            </Banner>
          )}

          {actionError && (
            <Banner
              type="error"
              title="Action Alert"
              action={
                <button
                  type="button"
                  onClick={() => setActionError(null)}
                  className="text-[#B42318] hover:underline text-xs font-semibold"
                >
                  Dismiss
                </button>
              }
            >
              {actionError}
            </Banner>
          )}

          {/* Submission Header Card */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-4 sm:p-6 shadow-xs">
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
                        ? "bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]"
                        : "bg-[#ECFDF3] text-[#067647] border-[#ABEFC6]"
                    }`}
                  >
                    {sub.risk_tier} Risk
                  </span>
                  <span className="font-mono text-xs text-[#5B6475]">
                    Version v{sub.version_no}
                  </span>
                  {review && <ModeChip mode={review.mode} />}
                </div>
                <h1 className="text-xl sm:text-2xl font-bold text-[#1F2A44] tracking-tight">
                  {sub.title}
                </h1>
                <p className="text-xs text-[#5B6475] mt-1">
                  Created by <strong className="text-[#1F2A44]">{sub.creator_id}</strong> &middot; Last updated{" "}
                  {new Date(sub.updated_at).toLocaleString()}
                </p>
              </div>

              {/* Header Action Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                {/* Run / Re-check Review Button */}
                {(allowed.includes("review") || sub.status === "Draft" || sub.status === "Checked") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleTriggerReview}
                    isLoading={isReviewRunning}
                    disabled={isReviewRunning}
                    leftIcon={<Sparkles className="w-4 h-4" />}
                  >
                    {sub.status === "Draft" && versions.length > 1 ? "Re-check Copy" : "Run Brand Review"}
                  </Button>
                )}

                {/* Submit for Review (Creator) */}
                {allowed.includes("submit") && (
                  <div className="relative inline-block">
                    <Button
                      variant="primary"
                      size="md"
                      onClick={handleSubmitForApproval}
                      isLoading={isActionPending}
                      disabled={isActionPending || openHighSeverityCount > 0}
                      rightIcon={<Send className="w-4 h-4" />}
                      title={
                        openHighSeverityCount > 0
                          ? "Submit disabled: Resolve open high-severity findings first"
                          : undefined
                      }
                    >
                      Submit for Approval
                    </Button>
                  </div>
                )}

                {/* Claim Review (Reviewer) */}
                {allowed.includes("claim") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleClaim}
                    isLoading={isActionPending}
                    disabled={isActionPending}
                    leftIcon={<CheckCircle2 className="w-4 h-4" />}
                  >
                    Claim Review
                  </Button>
                )}

                {/* Request Changes (Reviewer) */}
                {allowed.includes("request_changes") && (
                  <Button
                    variant="danger"
                    size="md"
                    onClick={() => {
                      if (isActionPending) return;
                      setNoteModalType("request_changes");
                      setActionNote("");
                      setNoteModalOpen(true);
                    }}
                    isLoading={isActionPending}
                    disabled={isActionPending}
                    leftIcon={<AlertCircle className="w-4 h-4" />}
                  >
                    Request Changes
                  </Button>
                )}

                {/* Approve (Reviewer) */}
                {allowed.includes("approve") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={() => {
                      if (isActionPending) return;
                      setNoteModalType("approve");
                      setActionNote("Verified against Lumo tone, term, and clinical fact guidelines.");
                      setNoteModalOpen(true);
                    }}
                    isLoading={isActionPending}
                    disabled={isActionPending}
                    leftIcon={<Check className="w-4 h-4" />}
                  >
                    Approve Submission
                  </Button>
                )}

                {/* Mark Published */}
                {allowed.includes("mark_published") && (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleMarkPublished}
                    isLoading={isActionPending}
                    disabled={isActionPending}
                    leftIcon={<CheckCircle2 className="w-4 h-4" />}
                  >
                    Mark as Published
                  </Button>
                )}

                {/* Edit Copy (Creator only when allowed) */}
                {allowed.includes("edit") && !isReviewer && !isEditing && (
                  <Button
                    variant="secondary"
                    size="md"
                    onClick={() => setIsEditing(true)}
                    leftIcon={<Edit3 className="w-4 h-4" />}
                  >
                    Edit Copy
                  </Button>
                )}
              </div>
            </div>

            {/* High-severity blocker notice for creator */}
            {openHighSeverityCount > 0 && sub.status === "Checked" && (
              <div className="mt-4 p-3 bg-[#FEF3F2] border border-[#FECDCA] rounded-lg text-xs text-[#B42318] flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <strong>Workflow Blocked:</strong> Submission cannot be submitted to reviewers while {openHighSeverityCount} open high-severity finding(s) remain. Accept suggested fixes or dismiss with evidence.
                </span>
              </div>
            )}

            {/* Status Stepper Progression */}
            <div className="pt-6">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#5B6475] block mb-3">
                Lifecycle Progression
              </span>
              <StatusStepper currentStatus={sub.status} />
            </div>
          </div>

          {/* Review Progress Banner (5 stages, fallback banner, completed stats) */}
          <ReviewProgressBanner
            review={review}
            isRunning={isReviewRunning}
            onRunReview={handleTriggerReview}
            canRunReview={allowed.includes("review") || sub.status === "Draft" || sub.status === "Checked"}
            buttonLabel={sub.status === "Draft" && versions.length > 1 ? "Re-check Copy" : "Run Brand Review"}
          />

          {/* Narrow Screen Pane Switcher (Tabs on narrow screens) */}
          <div className="lg:hidden flex items-center bg-[#E2E5EA] p-1 rounded-xl">
            <button
              type="button"
              onClick={() => setMobilePane("content")}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                mobilePane === "content" ? "bg-white text-[#1F2A44] shadow-xs" : "text-[#5B6475]"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              Copy &amp; Details
            </button>
            <button
              type="button"
              onClick={() => setMobilePane("findings")}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                mobilePane === "findings" ? "bg-white text-[#1F2A44] shadow-xs" : "text-[#5B6475]"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Findings ({findings.length})
            </button>
          </div>

          {/* Main Two-Pane Workspace Layout (Content Left, Findings Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left 7 Columns: Content View & Tabs */}
            <div
              className={`lg:col-span-7 space-y-6 ${
                mobilePane === "findings" ? "hidden lg:block" : "block"
              }`}
            >
              {/* Content Panel (HighlightedText vs Edit Form) */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                <div className="flex items-center justify-between pb-3 border-b border-[#E2E5EA] mb-4">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                      Marketing Copy (Version v{sub.version_no})
                    </h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-[#5B6475]">
                      {isOCRUnavailable
                        ? "Image submission"
                        : `${isEditing ? editContent.length : sub.content.length} chars`}
                    </span>
                    {allowed.includes("edit") && !isReviewer && !isEditing && !isOCRUnavailable && (
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

                {isOCRUnavailable ? (
                  <div className="space-y-4">
                    {/* Soft OCR Banner (Requirement 4) */}
                    <div className="p-4 rounded-xl bg-[#F0FDFA] border border-[#ABEFC6] text-xs text-[#0F766E] flex items-start gap-3">
                      <Info className="w-5 h-5 text-[#0F766E] flex-shrink-0 mt-0.5" />
                      <div className="space-y-1">
                        <p className="font-bold text-[#1F2A44] text-xs">
                          Text Extraction from Images
                        </p>
                        <p className="text-[#0F766E] leading-relaxed">
                          Text extraction from images requires Tesseract. Install it locally or deploy via Docker (see README).
                        </p>
                        <p className="text-[11px] text-[#5B6475]">
                          Visual brand compliance checks (brand color palette conformance and logo detection) evaluated automatically on the submitted image.
                        </p>
                      </div>
                    </div>

                    {/* Image Preview & Asset View */}
                    <div className="p-4 bg-[#F7F7F4] rounded-xl border border-[#CBD2DC] flex flex-col items-center justify-center text-center">
                      <div className="max-w-md w-full overflow-hidden rounded-lg border border-[#CBD2DC] bg-white shadow-xs p-2">
                        <img
                          src={`${getApiBase()}/submissions/${sub.id}/document`}
                          alt={sub.title}
                          className="w-full max-h-72 object-contain rounded"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                      </div>
                      <a
                        href={`${getApiBase()}/submissions/${sub.id}/document`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-3 text-xs font-semibold text-[#0F766E] hover:underline inline-flex items-center gap-1.5"
                      >
                        <LucideImage className="w-3.5 h-3.5" />
                        View original uploaded image
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                ) : isEditing ? (
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
                  <div>
                    {/* HighlightedText with keyboard focus and bidirectional scrolling */}
                    <HighlightedText
                      content={sub.content}
                      findings={findings.filter((f) => f.status === "open")}
                      selectedFindingId={selectedFindingId}
                      onSelectFinding={handleSelectFinding}
                    />

                    <div className="mt-3 flex items-center justify-between text-[11px] text-[#5B6475] pt-2 border-t border-[#E2E5EA]">
                      <span>
                        Underlines: <strong className="text-[#1F2A44]">Solid</strong> = Deterministic Rule &middot;{" "}
                        <strong className="text-[#0F766E]">Wavy</strong> = AI Model Check
                      </span>
                      <span>Click any highlight to focus its finding card</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Tabs: Versions & Diff, Comments, Approvals, Data Boundary */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 shadow-xs">
                {/* Tabs Switcher */}
                <div className="flex flex-wrap items-center gap-2 border-b border-[#E2E5EA] pb-3 mb-6">
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
                    Approvals &amp; Policy
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
                    {versions.length <= 1 ? (
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
                              className="px-2 py-1 text-xs rounded border border-[#CBD2DC] bg-white text-[#1F2A44]"
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
                              className="px-2 py-1 text-xs rounded border border-[#CBD2DC] bg-white text-[#1F2A44]"
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

                        {/* Versions List Table */}
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

                {/* Tab 2: Comments (Submission-level) */}
                {activeTab === "comments" && (
                  <div className="space-y-4">
                    {comments.filter((c) => !c.finding_id).length === 0 ? (
                      <p className="text-xs text-[#5B6475]">No submission-level notes posted yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {comments
                          .filter((c) => !c.finding_id)
                          .map((c) => (
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

                    {/* New Submission Comment Form */}
                    <form onSubmit={handlePostSubmissionComment} className="pt-3 border-t border-[#E2E5EA]">
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
                          disabled={!newCommentBody.trim()}
                          leftIcon={<Send className="w-3.5 h-3.5" />}
                        >
                          Post Comment
                        </Button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Tab 3: Approvals Policy & Timeline */}
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
                  <DataBoundaryView reviewId={review?.id || (findings[0]?.review_id ?? null)} />
                )}
              </div>
            </div>

            {/* Right 5 Columns: Findings Panel (Triage, Filters, Finding Cards) */}
            <div
              className={`lg:col-span-5 space-y-4 ${
                mobilePane === "content" ? "hidden lg:block" : "block"
              }`}
            >
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-5 shadow-xs space-y-4">
                {/* Findings Header & Summary Badges */}
                <div className="flex items-center justify-between pb-3 border-b border-[#E2E5EA]">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#0F766E]" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                      Brand Governance Findings
                    </h2>
                  </div>
                  <span className="text-xs font-bold font-mono px-2 py-0.5 rounded-full bg-[#F7F7F4] text-[#1F2A44] border border-[#CBD2DC]">
                    {findings.length} total
                  </span>
                </div>

                {/* Summary Pill Counts */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                  <div className="p-2 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
                    <span className="text-[10px] uppercase font-bold text-[#5B6475] block">Open</span>
                    <span className="font-bold text-[#1F2A44] tabular-nums">{totalOpen}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-[#FEF3F2] border border-[#FECDCA]">
                    <span className="text-[10px] uppercase font-bold text-[#B42318] block">High Risk</span>
                    <span className="font-bold text-[#B42318] tabular-nums">{openHighSeverityCount}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
                    <span className="text-[10px] uppercase font-bold text-[#5B6475] block">Rule Checks</span>
                    <span className="font-bold text-[#1F2A44] tabular-nums">{totalRule}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-[#F0FDFA] border border-[#ABEFC6]">
                    <span className="text-[10px] uppercase font-bold text-[#0F766E] block">AI Assisted</span>
                    <span className="font-bold text-[#0F766E] tabular-nums">{totalAI}</span>
                  </div>
                </div>

                {/* Filter Controls */}
                <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] space-y-2 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-[#1F2A44] text-[11px]">
                    <Filter className="w-3.5 h-3.5 text-[#0F766E]" />
                    <span>Filter Findings</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label htmlFor="filter-type" className="block text-[10px] font-bold text-[#5B6475] mb-0.5">
                        Issue Type
                      </label>
                      <select
                        id="filter-type"
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="w-full p-1.5 text-xs rounded border border-[#CBD2DC] bg-white text-[#1F2A44]"
                      >
                        <option value="all">All Types</option>
                        <option value="claim">Claim Substantiation</option>
                        <option value="terminology">Terminology &amp; Banned</option>
                        <option value="missing_disclaimer">Disclaimers</option>
                        <option value="confidential_leak">Confidential Leaks</option>
                        <option value="accessibility">Accessibility &amp; Grade</option>
                        <option value="readability">Readability</option>
                        <option value="tone">Tone Guidelines</option>
                        <option value="general_note">General Notes</option>
                      </select>
                    </div>

                    <div>
                      <label htmlFor="filter-severity" className="block text-[10px] font-bold text-[#5B6475] mb-0.5">
                        Severity
                      </label>
                      <select
                        id="filter-severity"
                        value={filterSeverity}
                        onChange={(e) => setFilterSeverity(e.target.value)}
                        className="w-full p-1.5 text-xs rounded border border-[#CBD2DC] bg-white text-[#1F2A44]"
                      >
                        <option value="all">All Severities</option>
                        <option value="high">High Severity</option>
                        <option value="medium">Medium Severity</option>
                        <option value="low">Low Severity</option>
                      </select>
                    </div>

                    <div>
                      <label htmlFor="filter-source" className="block text-[10px] font-bold text-[#5B6475] mb-0.5">
                        Source
                      </label>
                      <select
                        id="filter-source"
                        value={filterSource}
                        onChange={(e) => setFilterSource(e.target.value)}
                        className="w-full p-1.5 text-xs rounded border border-[#CBD2DC] bg-white text-[#1F2A44]"
                      >
                        <option value="all">All Sources</option>
                        <option value="rule">Rule Only</option>
                        <option value="ai">AI Assisted Only</option>
                      </select>
                    </div>

                    <div>
                      <label htmlFor="filter-status" className="block text-[10px] font-bold text-[#5B6475] mb-0.5">
                        Status
                      </label>
                      <select
                        id="filter-status"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="w-full p-1.5 text-xs rounded border border-[#CBD2DC] bg-white text-[#1F2A44]"
                      >
                        <option value="all">All Statuses</option>
                        <option value="open">Open</option>
                        <option value="accepted">Accepted</option>
                        <option value="dismissed">Dismissed</option>
                        <option value="escalated">Escalated</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Finding Cards List */}
                <div className="space-y-3">
                  {isDocxOrPdf && policyFindings.length === 0 && findings.length > 0 && (
                    <div className="p-3 bg-[#ECFDF3] border border-[#ABEFC6] rounded-lg text-xs text-[#067647] flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-[#067647] flex-shrink-0" />
                      <span>
                        <strong>No policy issues found in this document.</strong> The {findings.length} item(s) below are non-blocking advisory observations.
                      </span>
                    </div>
                  )}

                  {findings.length === 0 ? (
                    isDocxOrPdf ? (
                      /* Document Clean State (Requirement 5) */
                      <div className="p-6 bg-[#ECFDF3] border border-[#ABEFC6] rounded-xl text-center space-y-2">
                        <div className="w-10 h-10 mx-auto rounded-full bg-[#067647] text-white flex items-center justify-center font-bold">
                          ✓
                        </div>
                        <h3 className="text-sm font-bold text-[#067647]">
                          No policy issues found in this document
                        </h3>
                        <p className="text-xs text-[#067647] leading-relaxed">
                          No policy violations, tone deviations, or unverified claims detected in this document. All structure, accessibility, and brand standards comply.
                        </p>
                      </div>
                    ) : review?.status === "completed" ? (
                      /* Clean Bill of Health State */
                      <div className="p-6 bg-[#ECFDF3] border border-[#ABEFC6] rounded-xl text-center space-y-2">
                        <div className="w-10 h-10 mx-auto rounded-full bg-[#067647] text-white flex items-center justify-center font-bold">
                          ✓
                        </div>
                        <h3 className="text-sm font-bold text-[#067647]">
                          Clean Bill of Brand Health
                        </h3>
                        <p className="text-xs text-[#067647] leading-relaxed">
                          No policy violations, tone deviations, or unverified claims detected. Marketing copy complies with all brand standards.
                        </p>
                      </div>
                    ) : (
                      /* Not yet reviewed state */
                      <div className="p-6 bg-[#F7F7F4] border border-[#CBD2DC] rounded-xl text-center space-y-2 text-xs text-[#5B6475]">
                        <p>No findings recorded yet. Run a brand review above to scan this content.</p>
                      </div>
                    )
                  ) : filteredFindings.length === 0 ? (
                    <div className="p-6 text-center text-xs text-[#5B6475] bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                      No findings match the selected filter criteria.
                    </div>
                  ) : (
                    filteredFindings.map((finding) => (
                      <FindingCard
                        key={finding.id}
                        finding={finding}
                        isSelected={selectedFindingId === finding.id}
                        onSelect={handleSelectFinding}
                        onOpenCitation={(code, ver) =>
                          setCitationDialog({ isOpen: true, code, version: ver })
                        }
                        onAccept={handleAcceptFinding}
                        onOpenDismiss={(f) => setDismissFinding(f)}
                        onOpenEscalate={(f) => setEscalateFinding(f)}
                        comments={comments.filter((c) => c.finding_id === finding.id)}
                        onPostComment={handlePostFindingComment}
                        isActionPending={isActionPending}
                      />
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dismiss Dialog (Mandatory Reason Code + Text) */}
        {dismissFinding && (
          <DismissDialog
            isOpen={!!dismissFinding}
            onClose={() => setDismissFinding(null)}
            onConfirm={handleConfirmDismiss}
            findingExcerpt={dismissFinding.excerpt}
          />
        )}

        {/* Escalate Dialog (Manager note) */}
        {escalateFinding && (
          <EscalateDialog
            isOpen={!!escalateFinding}
            onClose={() => setEscalateFinding(null)}
            onConfirm={handleConfirmEscalate}
            findingExcerpt={escalateFinding.excerpt}
          />
        )}

        {/* Knowledge Base Citation Inspector Dialog */}
        <KBCitationDialog
          isOpen={citationDialog.isOpen}
          onClose={() => setCitationDialog({ isOpen: false, code: null })}
          entryCode={citationDialog.code}
          entryVersion={citationDialog.version}
        />

        {/* Reviewer Note Modal (Approve / Request Changes) */}
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

            <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-2 border-t border-[#E2E5EA]">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="w-full sm:w-auto justify-center"
                onClick={() => setNoteModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant={noteModalType === "approve" ? "primary" : "danger"}
                size="sm"
                className="w-full sm:w-auto justify-center"
                onClick={executeModalAction}
                isLoading={isActionPending}
                disabled={isActionPending}
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
