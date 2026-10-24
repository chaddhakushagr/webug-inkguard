"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  Lock,
  ArrowRight,
  Sparkles,
  FileText,
  AlertTriangle,
  UserCheck,
  Info,
} from "lucide-react";
import { api } from "@/shared/api/client";
import { DemoUser } from "@/shared/api/types";
import { Button, Input, Banner } from "@/shared/ui";

const DEFAULT_DEMO_USERS: DemoUser[] = [
  {
    id: "u-creator-social",
    name: "Elena Chen",
    email: "creator.social@lumo.internal",
    role: "creator",
    max_tier: "internal",
    team: "Team Social",
    description: "Drafts copy, runs brand reviews, resolves findings, submits for approval.",
  },
  {
    id: "u-creator-agency",
    name: "Marcus Vance",
    email: "creator.agency@contractor.external",
    role: "creator",
    max_tier: "public",
    team: "External Agency",
    description: "External writer restricted strictly to public guideline entries.",
  },
  {
    id: "u-reviewer",
    name: "Sarah Jenkins",
    email: "reviewer.sarah@lumo.internal",
    role: "reviewer",
    max_tier: "internal",
    team: "Brand Review",
    description: "Claims queue items, comments on findings, approves or requests changes.",
  },
  {
    id: "u-manager",
    name: "Kavita Rao",
    email: "manager.kavita@lumo.internal",
    role: "brand_manager",
    max_tier: "confidential",
    team: "Brand Strategy",
    description: "Edits knowledge base, resolves escalations, monitors governance insights.",
  },
  {
    id: "u-admin",
    name: "System Admin",
    email: "admin@lumo.internal",
    role: "admin",
    max_tier: "confidential",
    team: "Operations",
    description: "Full system administration, AI egress switch, and daily quota controls.",
  },
];

export default function LoginPage() {
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>(DEFAULT_DEMO_USERS);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("LumoDemo2026!");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showManualForm, setShowManualForm] = useState(false);

  useEffect(() => {
    api
      .getDemoUsers()
      .then((users) => {
        if (users && users.length > 0) setDemoUsers(users);
      })
      .catch(() => {});
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
      setError(err.message || "Authentication failed. Please verify credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Please provide an email address.");
      return;
    }
    handleLogin(email, password);
  };

  return (
    <div className="min-h-screen bg-[#F7F7F4] flex flex-col justify-between">
      {/* Top Demo Banner */}
      <div
        role="region"
        aria-label="Synthetic data notification"
        className="bg-[#FFFBEB] border-b border-[#FDE68A] px-4 py-2 text-xs text-[#B45309] flex items-center justify-between"
      >
        <div className="flex items-center gap-2 max-w-7xl mx-auto w-full">
          <AlertTriangle className="w-4 h-4 text-[#B45309] flex-shrink-0" />
          <span>
            <strong>Demo Environment:</strong> Fictional Brand &quot;Lumo&quot; &middot; All data is synthetic &middot; Offline Mock Mode active
          </span>
        </div>
      </div>

      {/* Main Two-Column Container */}
      <main id="main-content" tabIndex={-1} className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 sm:py-16 flex items-center outline-none">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 w-full items-start">
          {/* Left Column: Product Pitch & Honesty Notice */}
          <div className="lg:col-span-5 flex flex-col justify-center">
            {/* Logo & Brand Header */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-[#1F2A44] text-white flex items-center justify-center font-serif text-xl font-bold shadow-xs">
                IG
              </div>
              <div>
                <span className="font-bold text-2xl text-[#1F2A44] tracking-tight block">Inkguard</span>
                <span className="text-xs text-[#5B6475] font-medium">Pre-Publication Brand Governance</span>
              </div>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-[#1F2A44] tracking-tight leading-tight">
              Proofread brand copy with cited authority.
            </h1>

            <p className="mt-4 text-base text-[#5B6475] leading-relaxed">
              Inkguard verifies marketing and product copy against approved brand guidelines, facts, and legal rules. It explains every finding with a versioned source citation, suggests minimal-edit fixes that protect author intent, and ensures humans retain editorial control.
            </p>

            {/* Core Invariants Checklist */}
            <div className="mt-6 space-y-2.5 bg-white p-5 rounded-xl border border-[#E2E5EA]">
              <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F2A44] mb-2">
                Core Governance Principles
              </h2>
              <div className="flex items-start gap-2.5 text-xs text-[#1F2A44]">
                <CheckCircle2 className="w-4 h-4 text-[#067647] flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Verification, not generation:</strong> Checks claims and tone against approved sources; never writes ungrounded copy.
                </span>
              </div>
              <div className="flex items-start gap-2.5 text-xs text-[#1F2A44]">
                <CheckCircle2 className="w-4 h-4 text-[#067647] flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Deterministic first, AI second:</strong> Regex, terminology, and accessibility run in code; AI assists semantic nuances.
                </span>
              </div>
              <div className="flex items-start gap-2.5 text-xs text-[#1F2A44]">
                <CheckCircle2 className="w-4 h-4 text-[#067647] flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Suggest, never act:</strong> No AI code path can auto-publish or approve. Authors and reviewers make all decisions.
                </span>
              </div>
            </div>

            {/* AI Disclosure & Privacy Note */}
            <div className="mt-6 p-4 rounded-xl bg-[#F0FDFA] border border-[#A6F4C5] text-xs text-[#0F766E] flex items-start gap-3">
              <Sparkles className="w-4 h-4 text-[#0F766E] flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block font-bold">Data Boundary &amp; AI Disclosure</strong>
                <p className="mt-0.5 text-[#1F2A44] leading-relaxed">
                  Confidential entries never leave the boundary. The app operates in 100% offline mock mode by default with zero external dependencies.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Persona Switcher & Login Form */}
          <div className="lg:col-span-7 bg-white rounded-2xl border border-[#CBD2DC] p-6 sm:p-8 shadow-xs">
            <div className="flex items-center justify-between border-b border-[#E2E5EA] pb-4 mb-6">
              <div>
                <h2 className="text-lg font-bold text-[#1F2A44]">Instant Demo Sign In</h2>
                <p className="text-xs text-[#5B6475] mt-0.5">
                  Select a persona below to explore role-specific permissions and workflows
                </p>
              </div>
              <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[#5B6475]">
                <UserCheck className="w-3.5 h-3.5 text-[#0F766E]" />
                1-Click Login
              </span>
            </div>

            {error && (
              <div
                role="alert"
                className="mb-6 p-3.5 bg-[#FEF3F2] border border-[#FECDCA] rounded-lg text-xs font-medium text-[#B42318] flex items-center gap-2"
              >
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* 5 Persona Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
              {demoUsers.map((user) => {
                const initials = user.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("");

                return (
                  <button
                    key={user.id}
                    type="button"
                    onClick={() => handleLogin(user.email, "LumoDemo2026!")}
                    disabled={isLoading}
                    className="p-3.5 rounded-xl border border-[#CBD2DC] bg-[#F7F7F4]/50 hover:bg-white hover:border-[#0F766E] text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E] group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-[#1F2A44] text-white flex items-center justify-center font-bold text-xs group-hover:bg-[#0F766E] transition-colors">
                            {initials}
                          </div>
                          <div>
                            <span className="text-sm font-bold text-[#1F2A44] block group-hover:text-[#0F766E] transition-colors">
                              {user.name}
                            </span>
                            <span className="text-[11px] text-[#5B6475] capitalize">
                              {user.role.replace("_", " ")}
                            </span>
                          </div>
                        </div>
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border border-[#CBD2DC] bg-white text-[#5B6475]">
                          {user.max_tier}
                        </span>
                      </div>
                      <p className="text-xs text-[#5B6475] leading-relaxed line-clamp-2">
                        {user.description}
                      </p>
                    </div>

                    <div className="mt-3 pt-2 border-t border-[#E2E5EA]/70 flex items-center justify-between text-xs font-semibold text-[#0F766E]">
                      <span>Log in as {user.role.replace("_", " ")}</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Toggle Manual Form */}
            <div className="border-t border-[#E2E5EA] pt-5">
              <button
                type="button"
                onClick={() => setShowManualForm(!showManualForm)}
                className="text-xs text-[#5B6475] hover:text-[#1F2A44] font-medium flex items-center gap-1.5 focus:outline-none focus-visible:ring-1 focus-visible:ring-[#0F766E] rounded"
              >
                <span>{showManualForm ? "▲ Hide manual credentials form" : "▼ Enter custom email and password"}</span>
              </button>

              {showManualForm && (
                <form onSubmit={onSubmit} className="mt-4 space-y-4 bg-[#F7F7F4]/60 p-4 rounded-xl border border-[#E2E5EA]">
                  <Input
                    label="Email Address"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="creator.social@lumo.internal"
                    required
                  />

                  <Input
                    label="Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  <Button type="submit" variant="primary" size="md" isLoading={isLoading} className="w-full">
                    Authenticate
                  </Button>
                </form>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#E2E5EA] bg-white py-4 px-4 text-center text-xs text-[#5B6475]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Inkguard Brand Governance &middot; Team WeBug &middot; TechCircuit Hackathon Round 2</span>
          <span>Zero external cookies &middot; Local-first &middot; Accessible WCAG 2.1 AA</span>
        </div>
      </footer>
    </div>
  );
}
