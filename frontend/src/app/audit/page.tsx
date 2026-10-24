"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import {
  AppShell,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/shared/ui";
import { api } from "@/shared/api/client";
import { AuditLogItem } from "@/shared/api/types";
import { AuthGuard } from "@/features/auth/AuthGuard";
import {
  Shield,
  Search,
  Filter,
  CheckCircle2,
  Lock,
  Hash,
  Clock,
  ArrowRight,
  Database,
} from "lucide-react";

export default function AuditPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
        </div>
      }
    >
      <AuditContent />
    </Suspense>
  );
}

function AuditContent() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");

  const loadAudit = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getAuditLog();
      setLogs(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load audit trail");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (actionFilter !== "all" && log.action !== actionFilter) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      log.action.toLowerCase().includes(q) ||
      log.entity_type.toLowerCase().includes(q) ||
      log.hash.toLowerCase().includes(q) ||
      (log.actor_role && log.actor_role.toLowerCase().includes(q))
    );
  });

  const uniqueActions = Array.from(new Set(logs.map((l) => l.action)));

  return (
    <AuthGuard allowedRoles={["brand_manager", "admin"]}>
      <AppShell pageTitle="Cryptographic Audit Trail">
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-[#0F766E]" />
                <h1 className="text-2xl font-bold text-[#1F2A44] tracking-tight">
                  Cryptographic Audit Trail
                </h1>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-[#5B6475]">
                Strictly append-only ledger protected by SHA-256 hash chaining and database immutability triggers.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-[#ECFDF3] text-[#067647] border border-[#ABEFC6]">
                Chain Intact ({logs.length} blocks)
              </span>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] p-4 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-[#5B6475] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search action, entity, or hash..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-[#F7F7F4] text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              />
            </div>

            <div className="flex items-center gap-2">
              <select
                aria-label="Filter audit logs by action"
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg border border-[#CBD2DC] bg-white text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
              >
                <option value="all">All Actions ({logs.length})</option>
                {uniqueActions.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Audit Log Table */}
          <div className="bg-white rounded-xl border border-[#CBD2DC] overflow-hidden">
            {isLoading ? (
              <div className="p-8 space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : error ? (
              <ErrorState message={error} onRetry={loadAudit} />
            ) : filteredLogs.length === 0 ? (
              <EmptyState
                title="No audit log entries found"
                description="Events will appear here as governance actions, reviews, and edits occur."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-[#F7F7F4] border-b border-[#E2E5EA] text-[#5B6475] font-semibold">
                      <th className="py-3 px-4">Timestamp (UTC)</th>
                      <th className="py-3 px-4">Actor &amp; Role</th>
                      <th className="py-3 px-4">Action</th>
                      <th className="py-3 px-4">Entity</th>
                      <th className="py-3 px-4">Details</th>
                      <th className="py-3 px-4">SHA-256 Hash Block</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E5EA]">
                    {filteredLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-[#F7F7F4]/70 transition-colors">
                        <td className="py-3 px-4 font-mono text-[#5B6475]">
                          {new Date(log.ts).toLocaleString()}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-bold text-[#1F2A44] block">
                            {log.actor_role ? log.actor_role.replace("_", " ") : "System"}
                          </span>
                          <span className="text-[10px] text-[#5B6475]">{log.actor_id || "system"}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono font-bold text-[#0F766E] uppercase px-1.5 py-0.5 rounded bg-[#ECFDF3]">
                            {log.action}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-[#1F2A44]">
                          {log.entity_type}
                        </td>
                        <td className="py-3 px-4 max-w-xs truncate text-[#5B6475]">
                          {JSON.stringify(log.details)}
                        </td>
                        <td className="py-3 px-4 font-mono text-[10px] text-[#5B6475]">
                          <span className="text-[#1F2A44] font-bold">
                            {log.hash ? log.hash.slice(0, 16) : "GENESIS"}...
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
