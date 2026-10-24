import React from "react";
import { Sparkles, Info } from "lucide-react";
import { Tooltip } from "./Tooltip";

interface AIBadgeProps {
  confidence?: number;
  className?: string;
  showTooltip?: boolean;
}

export const AIBadge: React.FC<AIBadgeProps> = ({
  confidence,
  className = "",
  showTooltip = true,
}) => {
  const badge = (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border border-dashed border-[#0F766E] bg-[#F0FDFA] text-[#0F766E] select-none ${className}`}
    >
      <Sparkles className="w-3 h-3 text-[#0F766E]" aria-hidden="true" />
      <span>AI Assisted</span>
      {confidence !== undefined && (
        <span className="font-mono text-[10px] text-[#0F766E]/80">
          ({Math.round(confidence * 100)}%)
        </span>
      )}
    </span>
  );

  if (!showTooltip) return badge;

  return (
    <Tooltip content="Generated via LLM with strict citation guardrails. Suggestion only — human approval required.">
      {badge}
    </Tooltip>
  );
};
