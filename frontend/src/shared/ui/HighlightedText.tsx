"use client";

import React from "react";
import { Finding } from "../api/types";
import { Ruler, Sparkles } from "lucide-react";

interface HighlightedTextProps {
  content: string;
  findings: Finding[];
  selectedFindingId?: string | null;
  onSelectFinding?: (findingId: string) => void;
  className?: string;
}

interface Segment {
  text: string;
  finding?: Finding;
}

export const HighlightedText: React.FC<HighlightedTextProps> = ({
  content,
  findings,
  selectedFindingId,
  onSelectFinding,
  className = "",
}) => {
  // Sort findings by span_start
  const sortedFindings = [...findings]
    .filter((f) => f.span_start >= 0 && f.span_end <= content.length && f.span_start < f.span_end)
    .sort((a, b) => a.span_start - b.span_start);

  const segments: Segment[] = [];
  let currentIndex = 0;

  for (const finding of sortedFindings) {
    // If overlap or out of bounds, skip
    if (finding.span_start < currentIndex) continue;

    // Normal text before finding
    if (finding.span_start > currentIndex) {
      segments.push({
        text: content.substring(currentIndex, finding.span_start),
      });
    }

    // Finding segment
    segments.push({
      text: content.substring(finding.span_start, finding.span_end),
      finding,
    });

    currentIndex = finding.span_end;
  }

  // Trailing text
  if (currentIndex < content.length) {
    segments.push({
      text: content.substring(currentIndex),
    });
  }

  return (
    <div
      className={`prose prose-slate max-w-none font-serif text-base sm:text-lg leading-relaxed text-[#1F2A44] select-text bg-white p-6 sm:p-8 rounded-lg border border-[#E2E5EA] ${className}`}
    >
      {segments.map((segment, idx) => {
        if (!segment.finding) {
          return <span key={idx}>{segment.text}</span>;
        }

        const finding = segment.finding;
        const isSelected = selectedFindingId === finding.id;
        const isRule = finding.source === "rule";

        const severityStyles = {
          high: "bg-[#FEF3F2] text-[#B42318] decoration-[#B42318]",
          medium: "bg-[#FFFBEB] text-[#B45309] decoration-[#B45309]",
          low: "bg-[#EFF8FF] text-[#175CD3] decoration-[#175CD3]",
        }[finding.severity] || "bg-[#FEF3F2] text-[#B42318]";

        const markStyle = isRule ? "finding-mark-rule" : "finding-mark-ai";

        return (
          <mark
            key={finding.id || idx}
            id={`highlight-${finding.id}`}
            tabIndex={0}
            role="button"
            aria-pressed={isSelected}
            aria-label={`${finding.severity} severity ${finding.source} finding: ${finding.explanation}`}
            onClick={() => onSelectFinding?.(finding.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectFinding?.(finding.id);
              }
            }}
            className={`inline px-1 py-0.5 rounded cursor-pointer transition-all ${severityStyles} ${markStyle} ${
              isSelected ? "ring-2 ring-[#0F766E] ring-offset-1 font-semibold" : "hover:opacity-90"
            }`}
          >
            <span>{segment.text}</span>
            <span className="inline-flex items-center ml-1 opacity-70" aria-hidden="true">
              {isRule ? <Ruler className="w-3 h-3 inline" /> : <Sparkles className="w-3 h-3 inline" />}
            </span>
          </mark>
        );
      })}
    </div>
  );
};
