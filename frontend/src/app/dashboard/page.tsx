"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/shared/ui/Navbar";
import { api } from "@/shared/api/client";
import { User, Submission, InsightsSummary } from "@/shared/api/types";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [insights, setInsights] = useState<InsightsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const raw = typeof window !== "undefined" ? sessionStorage.getItem("inkguard_user") : null;
    if (raw) {
      try {
        setUser(JSON.parse(raw));
      } catch {
        // ignore
      }
    }

    Promise.all([api.getSubmissions(), api.getInsightsSummary()])
      .then(([subs, ins]) => {
        setSubmissions(subs);
        setInsights(ins);
      })
      .catch((err) => {
        setError(err.message || "Failed to load dashboard data");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* User Greeting & Role Banner */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Welcome, {user ? user.name : "Brand Collaborator"}
              </h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-800 capitalize font-medium">
                {user ? user.role.replace("_", " ") : "creator"}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Role: <strong className="text-slate-200 capitalize">{user?.role || "creator"}</strong> &middot; Max Egress Classification Tier:{" "}
              <strong className="text-indigo-400 uppercase font-mono">{user?.max_tier || "internal"}</strong>
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              href="/submissions/new/"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
            >
              + New Submission
            </Link>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Submissions</div>
            <div className="mt-2 text-3xl font-extrabold text-white">{submissions.length}</div>
            <div className="mt-1 text-xs text-indigo-400">In governance lifecycle</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Clean Submissions</div>
            <div className="mt-2 text-3xl font-extrabold text-emerald-400">
              {insights ? `${insights.clean_submissions_pct}%` : "64%"}
            </div>
            <div className="mt-1 text-xs text-slate-500">Zero policy findings</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Dismissals</div>
            <div className="mt-2 text-3xl font-extrabold text-amber-400">
              {insights ? insights.total_dismissals : 19}
            </div>
            <div className="mt-1 text-xs text-slate-500">With verified rationales</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Brand Rules</div>
            <div className="mt-2 text-3xl font-extrabold text-indigo-400">
              {insights ? insights.active_governance_rules : 32}
            </div>
            <div className="mt-1 text-xs text-slate-500">In-process BM25 indexed</div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent mb-3" />
            <p>Loading active governance pipeline...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-950/60 border border-red-800 rounded-xl p-6 text-red-200 mb-6">
            <h3 className="font-semibold mb-1">Failed to connect to backend service</h3>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Recent Submissions List */}
        {!isLoading && !error && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-base font-semibold text-white">Recent Content Submissions</h2>
              <span className="text-xs text-slate-500">Phase 0 Contract Fixtures</span>
            </div>

            {submissions.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <p>No content submissions found.</p>
              </div>
            ) : (
              <ul className="divide-y divide-slate-800">
                {submissions.map((sub) => (
                  <li key={sub.id} className="p-6 hover:bg-slate-800/40 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                            sub.status === "Approved"
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : sub.status === "Checked"
                              ? "bg-indigo-950 text-indigo-300 border border-indigo-800"
                              : sub.status === "Submitted"
                              ? "bg-amber-950 text-amber-300 border border-amber-800"
                              : "bg-slate-800 text-slate-300 border border-slate-700"
                          }`}
                        >
                          {sub.status}
                        </span>
                        <h3 className="text-base font-semibold text-white">
                          <Link href={`/submissions/detail/?id=${sub.id}`} className="hover:text-indigo-400">
                            {sub.title}
                          </Link>
                        </h3>
                      </div>
                      <span className="text-xs text-slate-500 uppercase font-mono tracking-wider">
                        Channel: {sub.channel} &middot; Risk: {sub.risk_tier}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-400 line-clamp-2">{sub.content}</p>
                    <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
                      <span>Version {sub.version_no}</span>
                      <div className="flex items-center space-x-2">
                        {sub.allowed_actions.map((act) => (
                          <span key={act} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 capitalize">
                            {act}
                          </span>
                        ))}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
