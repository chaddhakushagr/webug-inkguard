"use client";

import React from "react";
import { ModeChip, AIMode } from "@/shared/ui/ModeChip";
import { Banner, Button } from "@/shared/ui";
import { Review } from "@/shared/api/types";
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  RotateCw,
  FileSearch,
  Scale,
  Brain,
  ShieldCheck,
  Cpu,
} from "lucide-react";

interface ReviewProgressBannerProps {
  review: Review | null;
  isRunning: boolean;
  onRunReview: () => void;
  canRunReview: boolean;
  buttonLabel?: string;
  error?: string | null;
}

const STAGES = [
  { id: "extracting", name: "Extracting Copy", icon: FileSearch },
  { id: "rule_checks", name: "Rule Checks", icon: Scale },
  { id: "retrieving", name: "Retrieving KB", icon: FileSearch },
  { id: "analysing", name: "Analysing Claims", icon: Brain },
  { id: "finalising", name: "Guardrails & Finalising", icon: ShieldCheck },
];

export const ReviewProgressBanner: React.FC<ReviewProgressBannerProps> = ({
  review,
  isRunning,
  onRunReview,
  canRunReview,
  buttonLabel = "Run Brand Review",
  error,
}) => {
  const currentStageIndex = isRunning && review?.status
    ? STAGES.findIndex((s) => s.id === review.status)
    : -1;

  return (
    <div className="space-y-3" aria-live="polite">
      {/* Running Review Progress Box */}
      {isRunning && (
        <div className="p-4 bg-white rounded-xl border border-[#CBD2DC] shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E5EA] mb-3">
            <div className="flex items-center gap-2">
              <RotateCw className="w-4 h-4 text-[#0F766E] animate-spin" />
              <span className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                Evaluating Marketing Copy Across 5 Pipeline Stages
              </span>
            </div>
            <span className="font-mono text-xs font-bold text-[#0F766E] uppercase">
              {review?.status?.replace("_", " ") || "Processing"}
            </span>
          </div>

          {/* Stepper with 5 stages */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {STAGES.map((stage, idx) => {
              const Icon = stage.icon;
              const isPast = currentStageIndex > idx || (!isRunning && review?.status === "completed");
              const isCurrent = currentStageIndex === idx;

              return (
                <div
                  key={stage.id}
                  className={`p-2.5 rounded-lg border text-center transition-all ${
                    isCurrent
                      ? "bg-[#F0FDFA] border-[#0F766E] text-[#0F766E] ring-2 ring-[#0F766E]/20"
                      : isPast
                      ? "bg-[#ECFDF3] border-[#ABEFC6] text-[#067647]"
                      : "bg-[#F7F7F4] border-[#CBD2DC] text-[#5B6475] opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-center mb-1">
                    {isPast ? (
                      <CheckCircle2 className="w-4 h-4 text-[#067647]" />
                    ) : isCurrent ? (
                      <Icon className="w-4 h-4 text-[#0F766E] animate-pulse" />
                    ) : (
                      <Icon className="w-4 h-4 text-[#5B6475]" />
                    )}
                  </div>
                  <span className="block text-[11px] font-bold leading-tight">
                    {stage.name}
                  </span>
                  <span className="block text-[9px] uppercase font-mono mt-0.5 opacity-80">
                    Step {idx + 1}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Fallback Banner (when quota cap or no-AI admin switch activated) */}
      {review?.fallback_reason && (
        <Banner
          type="warning"
          title="Automatic AI Fallback Activated"
          action={
            <span className="font-mono text-[10px] uppercase font-bold text-[#B45309]">
              Mode: {review.mode}
            </span>
          }
        >
          {review.fallback_reason}
        </Banner>
      )}

      {/* Error State */}
      {error && (
        <Banner
          type="error"
          title="Review Execution Error"
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={onRunReview}
              leftIcon={<RotateCw className="w-3.5 h-3.5" />}
            >
              Retry Review
            </Button>
          }
        >
          {error}
        </Banner>
      )}

      {/* Completed Review Bar (when not running) */}
      {!isRunning && review && review.status === "completed" && (
        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-[#1F2A44] flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-[#067647]" />
              Review Completed
            </span>
            <ModeChip mode={(review.mode as AIMode) || "mock"} />
            {review.stats?.latency_ms && (
              <span className="text-[#5B6475] font-mono text-[11px] flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {review.stats.latency_ms}ms
              </span>
            )}
            {review.stats?.rules_evaluated && (
              <span className="text-[#5B6475] font-mono text-[11px]">
                &middot; {review.stats.rules_evaluated} rules evaluated
              </span>
            )}
            {review.stats?.kb_retrieved_count && (
              <span className="text-[#5B6475] font-mono text-[11px]">
                &middot; {review.stats.kb_retrieved_count} facts retrieved
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="font-bold text-[#1F2A44]">
              {review.findings_count} findings
            </span>
            {canRunReview && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onRunReview}
                leftIcon={<RotateCw className="w-3.5 h-3.5" />}
              >
                Re-check Copy
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
