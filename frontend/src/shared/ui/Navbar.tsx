"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { User } from "../api/types";

export function Navbar() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    const raw = typeof window !== "undefined" ? sessionStorage.getItem("inkguard_user") : null;
    if (raw) {
      try {
        setCurrentUser(JSON.parse(raw));
      } catch {
        // ignore
      }
    }
  }, []);

  const handleLogout = () => {
    sessionStorage.removeItem("inkguard_token");
    sessionStorage.removeItem("inkguard_user");
    window.location.href = "/";
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-8">
            <Link href="/dashboard/" className="flex items-center space-x-3 group focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-lg p-1">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30 group-hover:bg-indigo-500 transition-colors">
                IG
              </div>
              <div>
                <span className="font-bold text-lg text-white tracking-tight">Inkguard</span>
                <span className="ml-2 text-xs text-indigo-400 font-medium px-1.5 py-0.5 rounded bg-indigo-950/80 border border-indigo-800/50">
                  v0.2.0
                </span>
              </div>
            </Link>

            {/* Nav Links */}
            <nav className="hidden md:flex space-x-1" aria-label="Main Navigation">
              <Link
                href="/dashboard/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/submissions/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
              >
                Submissions
              </Link>
              <Link
                href="/reviewer-queue/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
              >
                Review Queue
              </Link>
              <Link
                href="/kb/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
              >
                Knowledge Base
              </Link>
              <Link
                href="/insights/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
              >
                Insights
              </Link>
              <Link
                href="/audit/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
              >
                Audit Log
              </Link>
              <Link
                href="/about-ai/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 hover:text-white transition-colors"
              >
                About AI
              </Link>
            </nav>
          </div>

          {/* User profile & Session */}
          <div className="flex items-center space-x-4">
            {currentUser ? (
              <div className="flex items-center space-x-3">
                <div className="text-right hidden sm:block">
                  <div className="text-sm font-medium text-white">{currentUser.name}</div>
                  <div className="text-xs text-slate-400 capitalize">
                    {currentUser.role.replace("_", " ")} &middot;{" "}
                    <span className="text-indigo-400 uppercase text-[10px] tracking-wider">
                      {currentUser.max_tier}
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded border border-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  Switch / Logout
                </button>
              </div>
            ) : (
              <Link
                href="/"
                className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-3.5 py-1.5 rounded-lg shadow transition-colors"
              >
                Demo Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
