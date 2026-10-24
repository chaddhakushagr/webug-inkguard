"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/shared/api/client";
import { DemoUser } from "@/shared/api/types";

export default function LoginPage() {
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("LumoDemo2026!");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getDemoUsers()
      .then((users) => setDemoUsers(users))
      .catch((err) => {
        // Fallback default demo users if backend is still waking up
        setDemoUsers([
          {
            id: "u-creator-social",
            name: "Elena Chen",
            email: "creator.social@lumo.internal",
            role: "creator",
            max_tier: "internal",
            team: "Team Social",
            description: "Social Media Copywriter (Drafts & submits short-form campaigns)",
          },
          {
            id: "u-creator-agency",
            name: "Marcus Vance",
            email: "creator.agency@contractor.external",
            role: "creator",
            max_tier: "public",
            team: "External Agency",
            description: "External Contractor (Restricted strictly to public knowledge base items)",
          },
          {
            id: "u-reviewer",
            name: "Sarah Jenkins",
            email: "reviewer.sarah@lumo.internal",
            role: "reviewer",
            max_tier: "internal",
            team: "Brand Review",
            description: "Senior Brand Reviewer (Reviews queue, requests changes, issues approvals)",
          },
          {
            id: "u-manager",
            name: "Kavita Rao",
            email: "manager.kavita@lumo.internal",
            role: "brand_manager",
            max_tier: "confidential",
            team: "Brand Strategy",
            description: "Brand Director (Manages guidelines, inspects insights, resolves escalations)",
          },
          {
            id: "u-admin",
            name: "System Admin",
            email: "admin@lumo.internal",
            role: "admin",
            max_tier: "confidential",
            team: "Operations",
            description: "Administrator (Manages system settings, AI killswitches, egress policy)",
          },
        ]);
      });
  }, []);

  const handleLogin = async (targetEmail: string, targetPass: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.login(targetEmail, targetPass);
      sessionStorage.setItem("inkguard_token", res.access_token);
      sessionStorage.setItem("inkguard_user", JSON.stringify(res.user));
      window.location.href = "/dashboard/";
    } catch (err: any) {
      setError(err.message || "Login failed. Please verify credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Please enter your email address.");
      return;
    }
    handleLogin(email, password);
  };

  return (
    <main className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-xl bg-indigo-600 mx-auto flex items-center justify-center font-bold text-white text-xl shadow-xl shadow-indigo-500/20">
          IG
        </div>
        <h1 className="mt-4 text-3xl font-extrabold text-white tracking-tight">
          Inkguard Governance
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Pre-publication brand compliance, claim verification &amp; source citations.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-slate-900/90 border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 backdrop-blur-sm">
          {/* Quick Demo Login Grid (SPEC F-02) */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                Instant Demo Logins (Round 2 Judging)
              </h2>
              <span className="text-[11px] text-slate-500">1-click authentication</span>
            </div>

            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {demoUsers.map((user) => (
                <button
                  key={user.id}
                  type="button"
                  onClick={() => handleLogin(user.email, "LumoDemo2026!")}
                  disabled={isLoading}
                  className="flex flex-col text-left p-3 rounded-xl border border-slate-800 bg-slate-800/40 hover:bg-indigo-950/40 hover:border-indigo-500/50 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 group"
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-sm font-semibold text-slate-200 group-hover:text-white">
                      {user.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono capitalize border border-slate-700">
                      {user.role.replace("_", " ")}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 mt-1 line-clamp-1">{user.description}</span>
                  <span className="text-[10px] text-indigo-400/80 mt-1 font-mono">
                    Tier: {user.max_tier}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-3 text-slate-500 font-medium">Or log in manually</span>
            </div>
          </div>

          {error && (
            <div
              role="alert"
              className="mb-4 p-3 bg-red-950/60 border border-red-800/80 rounded-lg text-sm text-red-200 flex items-center space-x-2"
            >
              <span className="text-red-400">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="creator.social@lumo.internal"
                className="mt-1 block w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
            >
              {isLoading ? "Signing in..." : "Sign In with Credentials"}
            </button>
          </form>

          {/* Privacy & Synthetic Data Notice */}
          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-400">
              Zero confidential or customer data is transmitted. All demonstrations run against the
              synthetic &quot;Lumo&quot; brand playbook with offline fallback.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
