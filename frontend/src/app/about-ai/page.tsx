"use client";

import React, { Suspense } from "react";
import { AppShell, Banner } from "@/shared/ui";
import { AuthGuard } from "@/features/auth/AuthGuard";
import { HelpCircle, Shield, Sparkles, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function AboutAIPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <AboutAIContent />
    </Suspense>
  );
}

function AboutAIContent() {
  return (
    <AuthGuard>
      <AppShell pageTitle="About AI &amp; Governance Transparency">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#0F766E]" />
              <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                AI Transparency &amp; Operating Principles
              </h1>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
              Full disclosure regarding external AI models, privacy boundaries, and human-in-the-loop safeguards.
            </p>
          </div>

          {/* Section 1: Invariants */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 space-y-4">
            <h2 className="text-base font-bold text-[#1F2A44] border-b border-[#E2E5EA] pb-2">
              Core Governance Invariants
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="text-xs font-bold text-[#1F2A44] flex items-center gap-1.5 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-[#067647]" /> Suggest, Never Act
                </span>
                <p className="text-xs text-[#5B6475]">
                  No AI routine can approve, publish, or overwrite copy. All editorial actions are exclusively performed by authenticated human creators and reviewers.
                </p>
              </div>

              <div className="p-4 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="text-xs font-bold text-[#1F2A44] flex items-center gap-1.5 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-[#067647]" /> Zero Confidential Egress
                </span>
                <p className="text-xs text-[#5B6475]">
                  Entries marked confidential (e.g. unannounced product launches) are strictly excluded from retrieval context and adapter payloads before external calls.
                </p>
              </div>

              <div className="p-4 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="text-xs font-bold text-[#1F2A44] flex items-center gap-1.5 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-[#067647]" /> Verified Citation Constraint
                </span>
                <p className="text-xs text-[#5B6475]">
                  Every policy finding must cite a retrieved entry code. Code guardrails drop hallucinations, expired facts, or ungrounded claims.
                </p>
              </div>

              <div className="p-4 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="text-xs font-bold text-[#1F2A44] flex items-center gap-1.5 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-[#067647]" /> Minimal-Edit Fixes
                </span>
                <p className="text-xs text-[#5B6475]">
                  Suggested replacements adhere to a 60% character change cap and strictly forbid introducing ungrounded superlatives or numbers.
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: Synthetic Data Notice */}
          <div className="p-5 bg-[#FFFBEB] rounded-xl border border-[#FDE68A] flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-[#B45309] flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#B45309]">
                Synthetic Benchmark Data Baseline
              </h3>
              <p className="text-xs text-[#92400E] mt-1 leading-relaxed">
                All brand guidelines, clinical facts, users, and campaign copy in Inkguard are strictly synthetic benchmarks created for the fictional skincare brand &quot;Lumo&quot;. No real proprietary company secrets, personal identities, or customer records are stored or transmitted.
              </p>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
