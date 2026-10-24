import React from "react";
import { Plus, Minus } from "lucide-react";

export interface DiffLine {
  type: "added" | "removed" | "unchanged";
  text: string;
}

interface DiffViewProps {
  diffText?: string;
  lines?: DiffLine[];
  className?: string;
}

export const DiffView: React.FC<DiffViewProps> = ({ diffText, lines, className = "" }) => {
  let parsedLines: DiffLine[] = lines || [];

  if (!lines && diffText) {
    parsedLines = diffText.split("\n").map((line) => {
      if (line.startsWith("+") && !line.startsWith("+++")) {
        return { type: "added", text: line.substring(1) };
      }
      if (line.startsWith("-") && !line.startsWith("---")) {
        return { type: "removed", text: line.substring(1) };
      }
      return { type: "unchanged", text: line };
    });
  }

  return (
    <div
      className={`font-mono text-xs sm:text-sm rounded-lg border border-[#E2E5EA] overflow-hidden bg-white ${className}`}
      aria-label="Content Revision Diff View"
    >
      <div className="bg-[#F7F7F4] px-4 py-2 border-b border-[#E2E5EA] text-xs font-sans text-[#5B6475] flex items-center justify-between">
        <span className="font-semibold text-[#1F2A44]">Revision Changes</span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-[#067647]">
            <Plus className="w-3.5 h-3.5" /> Added
          </span>
          <span className="flex items-center gap-1 text-[#B42318]">
            <Minus className="w-3.5 h-3.5" /> Removed
          </span>
        </div>
      </div>

      <div className="divide-y divide-[#E2E5EA]/40 overflow-x-auto p-2">
        {parsedLines.map((line, idx) => {
          if (line.type === "added") {
            return (
              <div
                key={idx}
                className="flex items-start gap-2 bg-[#ECFDF3] text-[#067647] px-3 py-1.5 rounded"
              >
                <Plus className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <span className="sr-only">Added: </span>
                <span className="whitespace-pre-wrap">{line.text}</span>
              </div>
            );
          }

          if (line.type === "removed") {
            return (
              <div
                key={idx}
                className="flex items-start gap-2 bg-[#FEF3F2] text-[#B42318] px-3 py-1.5 rounded line-through decoration-[#B42318]/50"
              >
                <Minus className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <span className="sr-only">Removed: </span>
                <span className="whitespace-pre-wrap">{line.text}</span>
              </div>
            );
          }

          return (
            <div key={idx} className="flex items-start gap-2 text-[#5B6475] px-3 py-1">
              <span className="w-4 flex-shrink-0 text-center select-none opacity-40">&middot;</span>
              <span className="whitespace-pre-wrap">{line.text}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
