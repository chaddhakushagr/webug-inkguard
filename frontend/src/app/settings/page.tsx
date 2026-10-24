"use client";

import React, { Suspense, useEffect, useState } from "react";
import { AppShell, Button } from "@/shared/ui";
import { AuthGuard } from "@/features/auth/AuthGuard";
import { api } from "@/shared/api/client";
import { Settings, Shield, Sliders, Check } from "lucide-react";

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <SettingsContent />
    </Suspense>
  );
}

function SettingsContent() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    api.getSystemStatus().then(setStatus).catch(() => {});
  }, []);

  return (
    <AuthGuard allowedRoles={["brand_manager", "admin"]}>
      <AppShell pageTitle="System &amp; Governance Settings">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6">
            <div className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-[#0F766E]" />
              <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                Governance &amp; AI Controls
              </h1>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
              System limits, daily API quotas, egress restrictions, and channel risk thresholds.
            </p>
          </div>

          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#1F2A44]">
              Runtime Operational Parameters
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="font-bold text-[#1F2A44] block">Active AI Operating Mode</span>
                <span className="font-mono text-[#0F766E] uppercase font-bold mt-1 block">
                  {status?.ai_mode || "mock"}
                </span>
              </div>
              <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="font-bold text-[#1F2A44] block">Provider Endpoint</span>
                <span className="text-[#5B6475] mt-1 block">
                  {status?.ai_provider || "Offline Mock Pipeline"}
                </span>
              </div>
              <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="font-bold text-[#1F2A44] block">Daily Quota Guardrail</span>
                <span className="font-mono text-[#1F2A44] mt-1 block">
                  {status?.daily_calls_made || 0} / {status?.daily_quota_limit || 100} calls made today
                </span>
              </div>
              <div className="p-3 bg-[#F7F7F4] rounded-lg border border-[#CBD2DC]">
                <span className="font-bold text-[#1F2A44] block">Database Connection</span>
                <span className="text-[#067647] font-bold mt-1 block">
                  Connected &middot; SQLite Local (PostgreSQL ready)
                </span>
              </div>
            </div>
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
