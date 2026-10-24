"use client";

import React, { Suspense, useEffect, useState } from "react";
import { AppShell, Banner, Card, Badge, ModeChip, type AIMode } from "@/shared/ui";
import { AuthGuard } from "@/features/auth/AuthGuard";
import { api } from "@/shared/api/client";
import { SystemStatus } from "@/shared/api/types";
import {
  HelpCircle,
  Shield,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Cpu,
  Lock,
  Layers,
  ArrowRight,
  Database,
  ExternalLink,
  Sliders,
  Scale,
} from "lucide-react";

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
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    api.getSystemStatus().then(setStatus).catch(() => {});
  }, []);

  const isMock = !status || status.ai_mode === "mock";
  const isLive = status?.ai_mode === "live";

  return (
    <AuthGuard>
      <AppShell pageTitle="About AI in Inkguard">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <Sparkles className="w-6 h-6 text-[#0F766E]" />
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1F2A44] tracking-tight">
                  About AI in Inkguard
                </h1>
              </div>
              <p className="mt-2 text-xs sm:text-sm text-[#5B6475] leading-relaxed">
                Full transparency disclosure on our multi-stage review architecture, data egress boundaries, model limits, and human-in-the-loop governance.
              </p>
            </div>
            <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#5B6475]">Engine State</span>
              <ModeChip mode={((status?.ai_mode as AIMode) || "mock")} />
            </div>
          </div>

          {/* Active Mode Notice Banner */}
          {isMock ? (
            <div className="p-5 bg-[#FFFBEB] rounded-xl border border-[#FDE68A] flex items-start gap-3">
              <Shield className="w-5 h-5 text-[#B45309] flex-shrink-0 mt-0.5" />
              <div>
                <h2 className="text-sm font-bold text-[#B45309]">Running in 100% Offline Mock Mode</h2>
                <p className="text-xs text-[#92400E] mt-1 leading-relaxed">
                  Inkguard is currently running completely offline without external network or LLM API calls. Review evaluations are executed using deterministic fixtures that mirror real model responses with zero telemetry egress.
                </p>
              </div>
            </div>
          ) : (
            <div className="p-5 bg-[#ECFDF3] rounded-xl border border-[#ABEFC6] flex items-start gap-3">
              <Cpu className="w-5 h-5 text-[#067647] flex-shrink-0 mt-0.5" />
              <div>
                <h2 className="text-sm font-bold text-[#067647]">Live Model Connected ({status?.ai_provider || "Google AI Studio"})</h2>
                <p className="text-xs text-[#067647] mt-1 leading-relaxed">
                  Live reviews are sent to Google AI Studio with strict daily call limits ({status?.daily_calls_made || 0} / {status?.daily_quota_limit || 100} calls used today) and complete data-boundary redaction.
                </p>
              </div>
            </div>
          )}

          {/* Section 1: Model Architecture & Operating Modes */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 sm:p-8 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-[#1F2A44] tracking-tight flex items-center gap-2">
                <Cpu className="w-5 h-5 text-[#0F766E]" />
                1. AI Models &amp; Pipeline Architecture
              </h2>
              <p className="text-xs sm:text-sm text-[#5B6475] mt-1">
                Inkguard never passes raw text directly to an LLM. It routes content through a 5-stage pipeline:
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#CBD2DC]">
                <strong className="block text-[#1F2A44] mb-1">Live Mode</strong>
                <span className="font-mono text-[11px] text-[#0F766E] block mb-1">gemini-2.5-flash</span>
                <p className="text-[#5B6475] text-[11px]">
                  Fast inference, structured JSON output mode, prompt-versioned temperature 0.1 for high reproducibility.
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#CBD2DC]">
                <strong className="block text-[#1F2A44] mb-1">Cached Mode</strong>
                <span className="font-mono text-[11px] text-[#175CD3] block mb-1">Deterministic Cache</span>
                <p className="text-[#5B6475] text-[11px]">
                  Replays identical prior review responses from the database, eliminating quota usage for repeated checks.
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#CBD2DC]">
                <strong className="block text-[#1F2A44] mb-1">Mock Mode (Default)</strong>
                <span className="font-mono text-[11px] text-[#B45309] block mb-1">Offline Fixtures</span>
                <p className="text-[#5B6475] text-[11px]">
                  100% offline, zero network egress. Evaluates sample copy against curated benchmark fixtures.
                </p>
              </div>
              <div className="p-3.5 rounded-lg bg-[#F7F7F4] border border-[#CBD2DC]">
                <strong className="block text-[#1F2A44] mb-1">Rules Only</strong>
                <span className="font-mono text-[11px] text-[#5B6475] block mb-1">Deterministic Checks</span>
                <p className="text-[#5B6475] text-[11px]">
                  Automatic fallback when daily cap is reached or external AI switch is disabled by admin policy.
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: What is Sent vs What is NEVER Sent */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 sm:p-8 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-[#1F2A44] tracking-tight flex items-center gap-2">
                <Lock className="w-5 h-5 text-[#0F766E]" />
                2. Data Boundary: What is Sent vs. What is Never Sent
              </h2>
              <p className="text-xs sm:text-sm text-[#5B6475] mt-1">
                Strict egress policies enforce dual-layer classification filtering before any external payload is created:
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* What is Sent */}
              <div className="p-5 rounded-xl bg-[#ECFDF3]/50 border border-[#A6F4C5] space-y-3">
                <div className="flex items-center gap-2 text-[#067647] font-bold text-sm">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>What is Sent to External AI</span>
                </div>
                <ul className="space-y-2 text-xs text-[#1F2A44]">
                  <li className="flex items-start gap-2">
                    <span className="text-[#067647] font-bold">&bull;</span>
                    <span><strong>Sanitized Content:</strong> Draft marketing copy with emails, phone numbers, and keys redacted.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#067647] font-bold">&bull;</span>
                    <span><strong>Public &amp; Internal Guidelines:</strong> Only retrieved brand rules and facts with tier &le; caller&apos;s authorization.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#067647] font-bold">&bull;</span>
                    <span><strong>System Prompt Guardrails:</strong> Strict rules forbidding ungrounded claims and capping edits to 60%.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#067647] font-bold">&bull;</span>
                    <span><strong>Boundary Log:</strong> Every call generates a full cryptographic telemetry record viewable in the UI.</span>
                  </li>
                </ul>
              </div>

              {/* What is Never Sent */}
              <div className="p-5 rounded-xl bg-[#FEF3F2]/50 border border-[#FECDCA] space-y-3">
                <div className="flex items-center gap-2 text-[#B42318] font-bold text-sm">
                  <XCircle className="w-4 h-4 flex-shrink-0" />
                  <span>What is NEVER Sent to External AI</span>
                </div>
                <ul className="space-y-2 text-xs text-[#1F2A44]">
                  <li className="flex items-start gap-2">
                    <span className="text-[#B42318] font-bold">&bull;</span>
                    <span><strong>Confidential Entries:</strong> Unannounced product codenames and confidential clinical trial facts.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#B42318] font-bold">&bull;</span>
                    <span><strong>Company Secrets &amp; Keys:</strong> Seeded passwords, tokens, and secret strings are dropped at sanitization.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#B42318] font-bold">&bull;</span>
                    <span><strong>User Identities:</strong> Reviewer comments, employee names, emails, and audit chains stay on-prem.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#B42318] font-bold">&bull;</span>
                    <span><strong>Zero Egress in Mock:</strong> Completely disabled during mock, cached, and rules-only modes.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Section 3: Limits & Quota Protections */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 sm:p-8 space-y-4">
            <h2 className="text-lg font-bold text-[#1F2A44] tracking-tight flex items-center gap-2">
              <Sliders className="w-5 h-5 text-[#0F766E]" />
              3. Operational Limits &amp; Quota Safeguards
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-lg bg-[#F7F7F4] border border-[#CBD2DC]">
                <span className="text-xs font-bold text-[#5B6475] uppercase block mb-1">Daily Live Call Cap</span>
                <span className="text-2xl font-extrabold text-[#1F2A44]">{status?.daily_quota_limit || 100} calls</span>
                <p className="text-[11px] text-[#5B6475] mt-1">
                  Protects free tier from exhaustion. Automatically switches to <code className="font-mono">rules_only</code> on breach.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-[#F7F7F4] border border-[#CBD2DC]">
                <span className="text-xs font-bold text-[#5B6475] uppercase block mb-1">Rate Limiting</span>
                <span className="text-2xl font-extrabold text-[#1F2A44]">60 / hour</span>
                <p className="text-[11px] text-[#5B6475] mt-1">
                  Per-user in-memory sliding window prevents automated review spam (HTTP 429 response).
                </p>
              </div>

              <div className="p-4 rounded-lg bg-[#F7F7F4] border border-[#CBD2DC]">
                <span className="text-xs font-bold text-[#5B6475] uppercase block mb-1">Content Size Cap</span>
                <span className="text-2xl font-extrabold text-[#1F2A44]">20,000 chars</span>
                <p className="text-[11px] text-[#5B6475] mt-1">
                  Strict request body limits prevent denial of service and memory leaks (HTTP 413 response).
                </p>
              </div>
            </div>
          </div>

          {/* Section 4: Free-Tier Disclosure & Synthetic Data */}
          <div className="p-6 bg-white rounded-xl border border-[#CBD2DC] space-y-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#B45309]" />
              <h2 className="text-base font-bold text-[#1F2A44]">
                4. Free-Tier Terms Disclosure &amp; Fictional Brand Baseline
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-[#5B6475] leading-relaxed">
              Google AI Studio free-tier terms disclose that logged API requests may be processed by Google reviewers and used to improve Google products. Because enterprise brand governance requires strict confidentiality, Inkguard follows two uncompromising rules:
            </p>
            <div className="space-y-2 pt-1 text-xs text-[#1F2A44]">
              <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#067647] flex-shrink-0" />
                <span><strong>Strictly Fictional Data:</strong> All brand guidelines, facts, rules, and campaigns belong to the synthetic brand <em>&quot;Lumo Skincare&quot;</em>. Zero real proprietary IP or customer data exists in this codebase.</span>
              </div>
              <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#067647] flex-shrink-0" />
                <span><strong>Admin Kill-Switch:</strong> Administrators can toggle the &quot;No external AI&quot; policy switch at any time to instantly restrict the entire platform to purely offline rule-based execution.</span>
              </div>
            </div>
          </div>

          {/* Section 5: Suggest, Never Act Invariant */}
          <div className="p-6 bg-[#0F766E]/5 rounded-xl border border-[#0F766E]/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-[#1F2A44]">Safety Invariant: Suggest, Never Act</h3>
              <p className="text-xs text-[#5B6475] mt-1">
                AI in Inkguard is purely assistive. It cannot approve submissions, publish copy, or overwrite text. Editorial decisions remain entirely in human hands.
              </p>
            </div>
            <a
              href="/docs/AI_USAGE.md"
              target="_blank"
              rel="noreferrer"
              className="text-xs font-semibold text-[#0F766E] hover:underline flex items-center gap-1 flex-shrink-0"
            >
              Read AI_USAGE.md &rarr;
            </a>
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
