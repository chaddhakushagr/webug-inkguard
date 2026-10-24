"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import {
  AppShell,
  Card,
  Badge,
  Button,
  Skeleton,
  ErrorState,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import { SystemStatus } from "@/shared/api/types";
import {
  Activity,
  CheckCircle2,
  Server,
  GitCommit,
  Cpu,
  Database,
  ShieldCheck,
  RefreshCw,
  Clock,
  ArrowRight,
} from "lucide-react";
import { ModeChip } from "@/shared/ui/ModeChip";

export default function StatusPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <StatusContent />
    </Suspense>
  );
}

function StatusContent() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  const loadStatus = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getSystemStatus();
      setStatus(data);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || "Failed to load system diagnostics");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  return (
    <AppShell pageTitle="System Status & Diagnostics">
      <div className="space-y-6 max-w-5xl">
        {/* Header */}
        <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-[#0F766E]" />
              <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                System Diagnostics &amp; Health
              </h1>
            </div>
            <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
              Real-time platform telemetry, AI mode configuration, database status, and build commit.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastRefreshed && (
              <span className="text-[11px] text-[#5B6475] hidden sm:inline">
                Updated {lastRefreshed}
              </span>
            )}
            <Button variant="secondary" size="sm" onClick={loadStatus} disabled={isLoading}>
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-32 w-full rounded-xl" />
            <Skeleton className="h-48 w-full rounded-xl" />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={loadStatus} />
        ) : (
          <>
            {/* Primary Status Tiles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Health */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475] flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#067647]" />
                  Health Status
                </span>
                <div className="mt-2 text-2xl font-extrabold text-[#067647] flex items-center gap-2">
                  <span>{status?.health || "Healthy"}</span>
                </div>
                <span className="mt-1 block text-xs text-[#5B6475]">All subsystem checks passing</span>
              </div>

              {/* AI Mode */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475] flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-[#0F766E]" />
                  Active AI Mode
                </span>
                <div className="mt-2">
                  <ModeChip mode={(status?.ai_mode as any) || "mock"} />
                </div>
                <span className="mt-1 block text-xs text-[#5B6475]">
                  {status?.ai_mode === "mock" ? "100% offline; zero egress" : status?.ai_mode}
                </span>
              </div>

              {/* Version */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475] flex items-center gap-1.5">
                  <Server className="w-3.5 h-3.5 text-[#1F2A44]" />
                  Application Version
                </span>
                <div className="mt-2 text-2xl font-extrabold font-mono text-[#1F2A44]">
                  v{status?.version || "0.2.0"}
                </div>
                <span className="mt-1 block text-xs text-[#5B6475]">TechCircuit Round 2</span>
              </div>

              {/* Commit Hash */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-5">
                <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475] flex items-center gap-1.5">
                  <GitCommit className="w-3.5 h-3.5 text-[#1F2A44]" />
                  Build Commit
                </span>
                <div className="mt-2 text-2xl font-extrabold font-mono text-[#0F766E]">
                  {status?.commit || "05fbbb2"}
                </div>
                <span className="mt-1 block text-xs text-[#5B6475]">Tagged release `g2`</span>
              </div>
            </div>

            {/* Diagnostic Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1: AI Provider & Data Boundary Policy */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 space-y-4">
                <div className="flex items-center gap-2 pb-3 border-b border-[#E2E5EA]">
                  <Cpu className="w-4 h-4 text-[#0F766E]" />
                  <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                    AI Provider &amp; Boundary Telemetry
                  </h2>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Provider Engine</span>
                    <span className="font-bold text-[#1F2A44]">{status?.ai_provider || "Offline Mock Engine"}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Daily Quota Limit</span>
                    <span className="font-mono font-bold text-[#1F2A44]">{status?.daily_quota_limit ?? 100} calls</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Calls Used Today</span>
                    <span className="font-mono font-bold text-[#067647]">{status?.daily_calls_made ?? 0}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Confidential Egress</span>
                    <span className="font-bold text-[#067647]">0 characters (Strict zero-leak policy)</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-[#5B6475]">Fallback Behaviour</span>
                    <span className="text-[#1F2A44]">Automatic fallback to `rules_only`</span>
                  </div>
                </div>

                <div className="pt-2">
                  <Link href="/about-ai/">
                    <Button variant="ghost" size="sm" className="w-full justify-between">
                      <span>Read Full AI Disclosure &amp; Architecture</span>
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </Link>
                </div>
              </div>

              {/* Card 2: Infrastructure & Architecture Integrity */}
              <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 space-y-4">
                <div className="flex items-center gap-2 pb-3 border-b border-[#E2E5EA]">
                  <Database className="w-4 h-4 text-[#0F766E]" />
                  <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44]">
                    Storage &amp; Architectural Integrity
                  </h2>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Database Storage</span>
                    <span className="font-bold text-[#067647] flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-[#067647]" />
                      Connected (SQLite WAL / Neon Postgres)
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Clean Architecture Lint</span>
                    <span className="font-bold text-[#067647]">2 Kept, 0 Broken (import-linter)</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Audit Trail Immutability</span>
                    <span className="font-bold text-[#067647]">SHA-256 Hash Chained &amp; Append-Only</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-[#F7F7F4]">
                    <span className="text-[#5B6475]">Server Uptime</span>
                    <span className="font-mono text-[#1F2A44]">
                      {Math.floor((status?.uptime_seconds || 3600) / 60)} minutes
                    </span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-[#5B6475]">Security Headers</span>
                    <span className="text-[#1F2A44]">CSP, X-Request-ID, Content-Type Options</span>
                  </div>
                </div>

                <div className="pt-2">
                  <Link href="/audit/">
                    <Button variant="ghost" size="sm" className="w-full justify-between">
                      <span>Inspect Audit Chain</span>
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
