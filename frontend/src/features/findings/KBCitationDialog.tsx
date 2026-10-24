"use client";

import React, { useEffect, useState } from "react";
import { Dialog, Badge, Skeleton } from "@/shared/ui";
import { api } from "@/shared/api/client";
import { KBEntry } from "@/shared/api/types";
import { BookOpen, ShieldAlert, Clock, Tag } from "lucide-react";

interface KBCitationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  entryCode: string | null;
  entryVersion?: number | null;
}

export const KBCitationDialog: React.FC<KBCitationDialogProps> = ({
  isOpen,
  onClose,
  entryCode,
  entryVersion,
}) => {
  const [entry, setEntry] = useState<KBEntry | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && entryCode) {
      setIsLoading(true);
      setError(null);
      api
        .getKBEntry(entryCode)
        .then((data) => setEntry(data))
        .catch((err) => setError(err.message || "Knowledge base entry could not be retrieved"))
        .finally(() => setIsLoading(false));
    } else {
      setEntry(null);
    }
  }, [isOpen, entryCode]);

  if (!isOpen) return null;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={entry ? `${entry.code}: ${entry.title}` : `Knowledge Base Reference: ${entryCode}`}
      description={`Brand governance rule citation (Version v${entryVersion ?? entry?.current_version ?? 1})`}
    >
      <div className="space-y-4 text-xs">
        {isLoading ? (
          <div className="space-y-3 py-2">
            <Skeleton className="h-4 w-3/4 rounded" />
            <Skeleton className="h-16 w-full rounded" />
            <Skeleton className="h-10 w-full rounded" />
          </div>
        ) : error ? (
          <div className="p-3 bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] rounded-lg">
            <strong>Error:</strong> {error}
          </div>
        ) : entry ? (
          <>
            {/* Meta tags */}
            <div className="flex flex-wrap items-center gap-2 pb-3 border-b border-[#E2E5EA]">
              <span className="font-mono font-bold px-2 py-0.5 rounded bg-[#1F2A44] text-white uppercase text-[10px]">
                {entry.type}
              </span>
              <span
                className={`font-mono text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                  entry.classification === "confidential"
                    ? "bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]"
                    : entry.classification === "internal"
                    ? "bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]"
                    : "bg-[#ECFDF3] text-[#067647] border-[#ABEFC6]"
                }`}
              >
                {entry.classification} tier
              </span>
              <span className="text-[#5B6475] text-[11px]">
                Status: <strong className="text-[#1F2A44] capitalize">{entry.status}</strong>
              </span>
              <span className="text-[#5B6475] text-[11px] ml-auto">
                Updated {new Date(entry.updated_at).toLocaleDateString()}
              </span>
            </div>

            {/* Body / Description */}
            {entry.body && (
              <div>
                <span className="font-bold text-[#1F2A44] block mb-1">Guideline &amp; Policy:</span>
                <p className="text-[#5B6475] leading-relaxed whitespace-pre-wrap bg-[#F7F7F4] p-3 rounded-lg border border-[#E2E5EA]">
                  {entry.body}
                </p>
              </div>
            )}

            {/* Type Specific Fields */}
            {entry.type === "term" && entry.data && (
              <div className="grid grid-cols-2 gap-2 p-3 bg-white border border-[#CBD2DC] rounded-lg">
                <div>
                  <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Approved Term</span>
                  <span className="font-semibold text-[#067647] mt-0.5 block">{entry.data.approved_term || "None"}</span>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Match Type</span>
                  <span className="font-mono text-[#1F2A44] mt-0.5 block">{entry.data.match_type || "exact"}</span>
                </div>
              </div>
            )}

            {entry.type === "fact" && entry.data && (
              <div className="space-y-2 p-3 bg-white border border-[#CBD2DC] rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase text-[#5B6475]">Efficacy Substantiation</span>
                  {entry.data.valid_until && (
                    <span className="font-mono text-[10px] text-[#5B6475]">
                      Valid until: {entry.data.valid_until}
                    </span>
                  )}
                </div>
                {entry.data.claim_support && (
                  <p className="text-[11px] text-[#1F2A44] font-medium leading-normal">
                    &ldquo;{entry.data.claim_support}&rdquo;
                  </p>
                )}
                {entry.data.study_reference && (
                  <p className="text-[10px] text-[#5B6475]">
                    Study Ref: <strong className="text-[#1F2A44]">{entry.data.study_reference}</strong>
                  </p>
                )}
              </div>
            )}

            {entry.type === "rule" && entry.data && (
              <div className="p-3 bg-white border border-[#CBD2DC] rounded-lg space-y-1">
                <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Target Channels</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {(entry.data.channels || ["all"]).map((ch: string) => (
                    <span key={ch} className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#F7F7F4] border border-[#E2E5EA]">
                      {ch}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : null}

        <div className="flex justify-end pt-3 border-t border-[#E2E5EA]">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-[#1F2A44] text-white hover:bg-[#1F2A44]/90"
          >
            Close Citation
          </button>
        </div>
      </div>
    </Dialog>
  );
};
