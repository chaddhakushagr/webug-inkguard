"use client";

import React, { useState } from "react";
import { Finding, Comment } from "@/shared/api/types";
import { AIBadge, Button, DiffView } from "@/shared/ui";
import {
  Ruler,
  Sparkles,
  BookOpen,
  Check,
  X,
  ArrowUpRight,
  MessageSquare,
  Send,
  AlertTriangle,
  Info,
  Scale,
} from "lucide-react";

interface FindingCardProps {
  finding: Finding;
  isSelected: boolean;
  onSelect: (findingId: string) => void;
  onOpenCitation: (entryCode: string, entryVersion?: number | null) => void;
  onAccept: (findingId: string) => void;
  onOpenDismiss: (finding: Finding) => void;
  onOpenEscalate: (finding: Finding) => void;
  comments: Comment[];
  onPostComment: (body: string, findingId: string) => Promise<void>;
  isActionPending?: boolean;
}

export const FindingCard: React.FC<FindingCardProps> = ({
  finding,
  isSelected,
  onSelect,
  onOpenCitation,
  onAccept,
  onOpenDismiss,
  onOpenEscalate,
  comments,
  onPostComment,
  isActionPending = false,
}) => {
  const [showComments, setShowComments] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [isPostingComment, setIsPostingComment] = useState(false);

  const isRule = finding.source === "rule";
  const isOpen = finding.status === "open";
  const allowed = finding.allowed_actions || (isOpen ? ["accept", "dismiss", "escalate"] : []);

  const severityConfig = {
    high: {
      bg: "bg-[#FEF3F2]",
      text: "text-[#B42318]",
      border: "border-[#FECDCA]",
      badge: "bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]",
    },
    medium: {
      bg: "bg-[#FFFBEB]",
      text: "text-[#B45309]",
      border: "border-[#FDE68A]",
      badge: "bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]",
    },
    low: {
      bg: "bg-[#EFF8FF]",
      text: "text-[#175CD3]",
      border: "border-[#B2DDFF]",
      badge: "bg-[#EFF8FF] text-[#175CD3] border-[#B2DDFF]",
    },
  }[finding.severity] || {
    bg: "bg-[#FEF3F2]",
    text: "text-[#B42318]",
    border: "border-[#FECDCA]",
    badge: "bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]",
  };

  const verdictConfig = finding.claim_verdict
    ? {
        Supported: "bg-[#ECFDF3] text-[#067647] border-[#ABEFC6]",
        Contradicted: "bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]",
        Unverified: "bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]",
        Expired: "bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]",
      }[finding.claim_verdict] || "bg-[#F7F7F4] text-[#1F2A44] border-[#CBD2DC]"
    : null;

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setIsPostingComment(true);
    try {
      await onPostComment(commentText.trim(), finding.id);
      setCommentText("");
    } catch {
      // handled above
    } finally {
      setIsPostingComment(false);
    }
  };

  const cardBorderClass = isRule ? "finding-card-rule" : "finding-card-ai";
  const statusBorderColor =
    finding.severity === "high"
      ? "border-l-[#B42318]"
      : finding.severity === "medium"
      ? "border-l-[#B45309]"
      : "border-l-[#175CD3]";

  return (
    <div
      id={`finding-card-${finding.id}`}
      tabIndex={0}
      role="region"
      aria-label={`${finding.severity} severity finding: ${finding.explanation}`}
      onClick={() => onSelect(finding.id)}
      onFocus={() => onSelect(finding.id)}
      className={`p-4 rounded-xl border bg-white shadow-xs transition-all cursor-pointer ${cardBorderClass} ${statusBorderColor} ${
        isSelected
          ? "ring-2 ring-[#0F766E] border-[#0F766E] shadow-sm"
          : "border-[#CBD2DC] hover:border-[#CBD2DC]/80"
      }`}
    >
      {/* Header: Issue type, Severity, Source */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-[#E2E5EA]">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#F7F7F4] text-[#1F2A44] border border-[#CBD2DC]">
            {finding.issue_type.replace("_", " ")}
          </span>
          <span
            className={`font-mono text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${severityConfig.badge}`}
          >
            {finding.severity}
          </span>
          {!finding.is_policy && (
            <span className="text-[10px] font-semibold text-[#5B6475] bg-[#F7F7F4] px-1.5 py-0.5 rounded">
              Non-policy observation
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {isRule ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-[#F7F7F4] text-[#1F2A44] border border-[#CBD2DC]">
              <Ruler className="w-3 h-3 text-[#5B6475]" />
              Rule Check
            </span>
          ) : (
            <AIBadge confidence={finding.confidence} />
          )}

          {finding.status !== "open" && (
            <span
              className={`font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                finding.status === "accepted"
                  ? "bg-[#ECFDF3] text-[#067647]"
                  : finding.status === "dismissed"
                  ? "bg-[#F7F7F4] text-[#5B6475] line-through"
                  : "bg-[#EFF8FF] text-[#175CD3]"
              }`}
            >
              {finding.status}
            </span>
          )}
        </div>
      </div>

      {/* Excerpt Highlighted Context */}
      <div className="mt-3">
        <span className="text-[10px] uppercase font-bold tracking-wider text-[#5B6475] block">
          Flagged Copy Excerpt
        </span>
        <div className="p-2.5 bg-[#F7F7F4] rounded-lg border border-[#E2E5EA] font-serif text-xs text-[#1F2A44] mt-1 font-medium leading-relaxed">
          &ldquo;{finding.excerpt}&rdquo;
        </div>
      </div>

      {/* Plain Language Explanation */}
      <div className="mt-2.5">
        <p className="text-xs text-[#1F2A44] leading-relaxed font-sans">
          {finding.explanation}
        </p>
      </div>

      {/* Claim Verdict & Needs Human Judgment Markers */}
      {(finding.claim_verdict || finding.needs_human_judgment) && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {finding.claim_verdict && (
            <span
              className={`font-mono text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${verdictConfig}`}
            >
              Claim Verdict: {finding.claim_verdict}
            </span>
          )}
          {finding.needs_human_judgment && (
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#B45309] bg-[#FFFBEB] px-2 py-0.5 rounded border border-[#FDE68A]">
              <AlertTriangle className="w-3 h-3" />
              Needs Human Judgment
            </span>
          )}
        </div>
      )}

      {/* Verifier Pass Entailment Verdict (AI findings only) */}
      {!isRule && (
        <div className="mt-2.5">
          {finding.needs_human_judgment || finding.verifier_verdict === "unsure" ? (
            <div className="p-2 bg-[#FFFBEB] rounded-lg border border-[#FDE68A] text-xs text-[#B45309] flex items-start gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-[#B45309] mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-semibold">Needs human judgment:</span>{" "}
                <span className="font-normal font-sans">
                  {finding.verifier_reason || "Evidence is borderline or inconclusive; human judgment required."}
                </span>
              </div>
            </div>
          ) : finding.verifier_verdict === "not_supported" ? (
            <div className="p-2 bg-[#FEF3F2] rounded-lg border border-[#FECDCA] text-xs text-[#B42318] flex items-start gap-1.5">
              <X className="w-3.5 h-3.5 text-[#B42318] mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-semibold">Not supported:</span>{" "}
                <span className="font-normal font-sans">
                  {finding.verifier_reason || "Citation does not support a policy violation."}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-2 bg-[#ECFDF3] rounded-lg border border-[#ABEFC6] text-xs text-[#067647] flex items-start gap-1.5">
              <Check className="w-3.5 h-3.5 text-[#067647] mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-semibold">
                  Verified against {finding.cited_entry_code || "knowledge base"}:
                </span>{" "}
                <span className="font-normal font-sans">
                  {finding.verifier_reason || "Semantic entailment verified against cited policy."}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Cited Knowledge Base Source */}
      {finding.cited_entry_code && (
        <div className="mt-3 pt-2.5 border-t border-[#E2E5EA] flex items-center justify-between text-xs">
          <span className="text-[11px] text-[#5B6475] flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-[#0F766E]" />
            Cited Guideline:
          </span>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onOpenCitation(finding.cited_entry_code!, finding.cited_entry_version);
            }}
            className="font-mono text-xs font-bold text-[#0F766E] hover:underline flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-[#F0FDFA]"
          >
            <span>{finding.cited_entry_code}</span>
            {finding.cited_entry_version && (
              <span className="text-[10px] font-normal text-[#5B6475]">
                (v{finding.cited_entry_version})
              </span>
            )}
            &rarr;
          </button>
        </div>
      )}

      {/* Suggested Fix (DiffView or No safe suggestion note) */}
      <div className="mt-3 pt-2.5 border-t border-[#E2E5EA]">
        <span className="text-[10px] uppercase font-bold tracking-wider text-[#5B6475] block mb-1.5">
          Suggested Replacement
        </span>
        {finding.suggested_fix ? (
          <DiffView
            original={finding.excerpt}
            modified={finding.suggested_fix}
            className="border-[#CBD2DC]"
          />
        ) : (
          <div className="p-2.5 bg-[#F7F7F4] rounded-lg border border-[#E2E5EA] text-xs text-[#5B6475] italic flex items-center gap-2">
            <Info className="w-4 h-4 text-[#5B6475] flex-shrink-0" />
            <span>No safe automated suggestion; requires manual author edit.</span>
          </div>
        )}
      </div>

      {/* Action Buttons: Accept / Dismiss / Escalate */}
      {isOpen && (
        <div className="mt-4 pt-3 border-t border-[#E2E5EA] flex flex-wrap items-center justify-end gap-2">
          {allowed.includes("escalate") && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onOpenEscalate(finding);
              }}
              disabled={isActionPending}
              leftIcon={<ArrowUpRight className="w-3.5 h-3.5" />}
            >
              Escalate
            </Button>
          )}

          {allowed.includes("dismiss") && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onOpenDismiss(finding);
              }}
              disabled={isActionPending}
              leftIcon={<X className="w-3.5 h-3.5" />}
            >
              Dismiss
            </Button>
          )}

          {allowed.includes("accept") && finding.suggested_fix && (
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onAccept(finding.id);
              }}
              isLoading={isActionPending}
              leftIcon={<Check className="w-3.5 h-3.5" />}
            >
              Accept Fix
            </Button>
          )}
        </div>
      )}

      {/* Finding Comments Accordion */}
      <div className="mt-3 pt-2 border-t border-[#E2E5EA]/60">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setShowComments(!showComments);
          }}
          className="text-[11px] font-semibold text-[#5B6475] hover:text-[#1F2A44] flex items-center gap-1.5 transition-colors"
        >
          <MessageSquare className="w-3.5 h-3.5 text-[#0F766E]" />
          <span>
            {comments.length > 0 ? `Discussion (${comments.length})` : "Add note to finding"}
          </span>
        </button>

        {showComments && (
          <div className="mt-3 space-y-2 pt-2 border-t border-[#E2E5EA]" onClick={(e) => e.stopPropagation()}>
            {comments.length > 0 ? (
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {comments.map((c) => (
                  <div key={c.id} className="p-2 bg-[#F7F7F4] rounded-lg border border-[#E2E5EA] text-xs">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="font-bold text-[11px] text-[#1F2A44]">{c.author_name}</span>
                      <span className="text-[9px] text-[#5B6475]">
                        {new Date(c.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#1F2A44] whitespace-pre-wrap">{c.body}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-[#5B6475] italic">No comments on this finding yet.</p>
            )}

            <form onSubmit={handleCommentSubmit} className="pt-2 flex gap-1.5">
              <input
                type="text"
                placeholder="Write a comment or note..."
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                className="flex-1 px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] focus:outline-none focus:ring-1 focus:ring-[#0F766E]"
              />
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isPostingComment}
                disabled={!commentText.trim()}
              >
                <Send className="w-3 h-3" />
              </Button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
