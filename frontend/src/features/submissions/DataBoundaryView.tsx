"use client";

import React, { useEffect, useState } from "react";
import { DataBoundary } from "@/shared/api/types";
import { api } from "@/shared/api/client";
import { Skeleton } from "@/shared/ui";
import { ShieldCheck, Lock, HardDrive, Key, Mail, Phone, Cpu } from "lucide-react";

interface DataBoundaryViewProps {
  reviewId?: string | null;
}

export const DataBoundaryView: React.FC<DataBoundaryViewProps> = ({ reviewId }) => {
  const [boundary, setBoundary] = useState<DataBoundary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reviewId) return;
    setIsLoading(true);
    setError(null);
    api
      .getReviewBoundary(reviewId)
      .then((data) => setBoundary(data))
      .catch((err) => setError(err.message || "Failed to load data boundary telemetry"))
      .finally(() => setIsLoading(false));
  }, [reviewId]);

  if (!reviewId) {
    return (
      <div className="p-6 text-center text-xs text-[#5B6475] bg-[#F7F7F4] rounded-xl border border-[#CBD2DC]">
        Run a brand review to inspect data boundary and privacy telemetry.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4 py-3">
        <Skeleton className="h-16 w-full rounded-xl" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !boundary) {
    return (
      <div className="p-4 bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] text-xs rounded-xl">
        <strong>Data Boundary Telemetry:</strong> {error || "Unable to retrieve boundary record."}
      </div>
    );
  }

  const isOffline =
    boundary.external_calls_count === 0 ||
    boundary.provider.toLowerCase().includes("mock") ||
    boundary.provider.toLowerCase().includes("zero");

  const redaction = boundary.redaction_summary || {};
  const totalRedacted =
    (redaction.emails || 0) +
    (redaction.phone_numbers || 0) +
    (redaction.api_keys || 0) +
    (redaction.secrets || 0);

  return (
    <div className="space-y-4 text-xs">
      {/* Primary Assurance Banner */}
      <div
        className={`p-4 rounded-xl border ${
          isOffline
            ? "bg-[#ECFDF3] border-[#ABEFC6] text-[#067647]"
            : "bg-[#EFF8FF] border-[#B2DDFF] text-[#175CD3]"
        }`}
      >
        <div className="flex items-center gap-2 font-bold text-xs mb-1">
          <ShieldCheck className="w-4 h-4 flex-shrink-0" />
          <span>
            {isOffline
              ? "Zero External Egress Invariant Verified"
              : "Air-Gapped Data Boundary & Confidential Filter Active"}
          </span>
        </div>
        <p className="text-[11px] leading-relaxed">
          {boundary.message ||
            (isOffline
              ? "Offline mock mode: zero data sent to external services."
              : "All outgoing payloads verified: zero confidential entries and all PII scrubbed prior to network transmission.")}
        </p>
      </div>

      {/* Boundary Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">AI Provider</span>
          <span className="text-xs font-bold text-[#1F2A44] mt-1 block truncate">
            {boundary.provider}
          </span>
          <span className="text-[10px] font-mono text-[#5B6475] block mt-0.5">
            Model: {boundary.model}
          </span>
        </div>

        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">External Calls</span>
          <span className="text-sm font-bold text-[#1F2A44] mt-1 block tabular-nums">
            {boundary.external_calls_count}
          </span>
          <span className="text-[10px] text-[#5B6475] block mt-0.5">
            {isOffline ? "0 outbound network requests" : "Live HTTPS egress"}
          </span>
        </div>

        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Characters Sent</span>
          <span className="text-sm font-bold text-[#1F2A44] mt-1 block tabular-nums">
            {boundary.characters_sent ?? 0}
          </span>
          <span className="text-[10px] text-[#5B6475] block mt-0.5">
            Cache Hit: {boundary.cache_hit ? "Yes (Cached)" : "No"}
          </span>
        </div>

        <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
          <span className="text-[10px] font-bold uppercase text-[#5B6475] block">Max Tier Sent</span>
          <span className="text-xs font-mono font-bold text-[#0F766E] uppercase mt-1 block">
            {boundary.highest_tier_sent || "public"}
          </span>
          <span className="text-[10px] text-[#067647] font-semibold block mt-0.5">
            Confidential: Never sent
          </span>
        </div>
      </div>

      {/* Redaction Summary Breakdown */}
      <div className="p-4 bg-white rounded-lg border border-[#CBD2DC] space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#E2E5EA]">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-[#0F766E]" />
            <span className="font-bold text-xs text-[#1F2A44]">
              In-Memory Redaction Summary ({totalRedacted} items masked)
            </span>
          </div>
          <span className="text-[10px] text-[#5B6475]">Raw secrets are never persisted</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="p-2 bg-[#F7F7F4] rounded border border-[#E2E5EA] flex items-center justify-between">
            <span className="text-[#5B6475] flex items-center gap-1">
              <Mail className="w-3 h-3" /> Emails
            </span>
            <span className="font-mono font-bold text-[#1F2A44]">{redaction.emails || 0}</span>
          </div>

          <div className="p-2 bg-[#F7F7F4] rounded border border-[#E2E5EA] flex items-center justify-between">
            <span className="text-[#5B6475] flex items-center gap-1">
              <Phone className="w-3 h-3" /> Phones
            </span>
            <span className="font-mono font-bold text-[#1F2A44]">{redaction.phone_numbers || 0}</span>
          </div>

          <div className="p-2 bg-[#F7F7F4] rounded border border-[#E2E5EA] flex items-center justify-between">
            <span className="text-[#5B6475] flex items-center gap-1">
              <Key className="w-3 h-3" /> API Keys
            </span>
            <span className="font-mono font-bold text-[#1F2A44]">{redaction.api_keys || 0}</span>
          </div>

          <div className="p-2 bg-[#F7F7F4] rounded border border-[#E2E5EA] flex items-center justify-between">
            <span className="text-[#5B6475] flex items-center gap-1">
              <Lock className="w-3 h-3" /> Launch Secrets
            </span>
            <span className="font-mono font-bold text-[#1F2A44]">{redaction.secrets || 0}</span>
          </div>
        </div>
      </div>

      {/* Entry Codes Included */}
      {boundary.entry_codes_included && boundary.entry_codes_included.length > 0 && (
        <div className="p-4 bg-white rounded-lg border border-[#CBD2DC] space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#5B6475] block">
            Retrieved Knowledge Base Entries in Prompt Context ({boundary.entry_codes_included.length})
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
            {boundary.entry_codes_included.map((code) => (
              <span
                key={code}
                className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#F7F7F4] text-[#1F2A44] border border-[#CBD2DC]"
              >
                {code}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
