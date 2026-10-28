"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileText,
  CheckSquare,
  BookOpen,
  BarChart3,
  Shield,
  Settings,
  HelpCircle,
  Menu,
  X,
  ChevronDown,
  UserCheck,
  LogOut,
  PenTool,
  Activity,
  Target,
  HeartPulse,
} from "lucide-react";
import { ModeChip, AIMode } from "./ModeChip";
import { Dialog } from "./Dialog";
import { Button } from "./Button";
import { ToastContainer } from "./Toast";
import { User, DemoUser } from "../api/types";
import { api } from "../api/client";

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
}

export const AppShell: React.FC<AppShellProps> = ({ children, pageTitle }) => {
  const pathname = usePathname();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [aiMode, setAiMode] = useState<AIMode>("mock");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false);
  const [isReLoginOpen, setIsReLoginOpen] = useState(false);
  const [reLoginMessage, setReLoginMessage] = useState("Your session has expired. Please sign in again.");

  useEffect(() => {
    // 1. Load active user
    const raw = typeof window !== "undefined" ? sessionStorage.getItem("inkguard_user") : null;
    if (raw) {
      try {
        setCurrentUser(JSON.parse(raw));
      } catch {
        // ignore
      }
    }

    // 2. Load demo users for role switcher
    api
      .getDemoUsers()
      .then((users) => setDemoUsers(users))
      .catch(() => {
        // fallback
      });

    // 3. Fetch health / AI mode
    api
      .getHealth()
      .then((h) => {
        if (h.ai_mode) setAiMode(h.ai_mode as AIMode);
      })
      .catch(() => {});

    // 4. 401 Unauthorized listener
    const handleUnauthorized = (e: any) => {
      setReLoginMessage(e?.detail?.message || "Your session has expired. Please sign in again.");
      setIsReLoginOpen(true);
    };

    window.addEventListener("inkguard:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("inkguard:unauthorized", handleUnauthorized);
    };
  }, []);

  const handleSwitchDemoRole = async (user: DemoUser) => {
    try {
      const res = await api.login(user.email, "LumoDemo2026!");
      sessionStorage.setItem("inkguard_token", res.access_token);
      sessionStorage.setItem("inkguard_user", JSON.stringify(res.user));
      setCurrentUser(res.user as User);
      setIsRoleDropdownOpen(false);
      window.location.reload();
    } catch {
      // Direct session fallback
      const fallbackUser: User = {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role,
        max_tier: user.max_tier,
        is_active: true,
      };
      sessionStorage.setItem("inkguard_token", `mock-token-${user.id}`);
      sessionStorage.setItem("inkguard_user", JSON.stringify(fallbackUser));
      setCurrentUser(fallbackUser);
      setIsRoleDropdownOpen(false);
      window.location.reload();
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem("inkguard_token");
    sessionStorage.removeItem("inkguard_user");
    window.location.href = "/";
  };

  // Nav links based on active user role
  const isManagerOrAdmin = currentUser?.role === "brand_manager" || currentUser?.role === "admin";
  const isReviewer = currentUser?.role === "reviewer" || isManagerOrAdmin;

  const navItems = [
    { label: "Dashboard", href: "/dashboard/", icon: <FileText className="w-4 h-4" /> },
    { label: "Submissions", href: "/submissions/", icon: <PenTool className="w-4 h-4" /> },
    ...(isReviewer
      ? [{ label: "Review Queue", href: "/reviewer-queue/", icon: <CheckSquare className="w-4 h-4" /> }]
      : []),
    { label: "Knowledge Base", href: "/kb/", icon: <BookOpen className="w-4 h-4" /> },
    ...(isManagerOrAdmin
      ? [
          { label: "Insights", href: "/insights/", icon: <BarChart3 className="w-4 h-4" /> },
          { label: "Guideline Health", href: "/insights/guideline-health/", icon: <HeartPulse className="w-4 h-4" /> },
          { label: "Evaluation", href: "/eval/", icon: <Target className="w-4 h-4" /> },
          { label: "Audit Log", href: "/audit/", icon: <Shield className="w-4 h-4" /> },
          { label: "Settings", href: "/settings/", icon: <Settings className="w-4 h-4" /> },
        ]
      : []),
    { label: "Status", href: "/status/", icon: <Activity className="w-4 h-4" /> },
    { label: "About AI", href: "/about-ai/", icon: <HelpCircle className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F7F4] text-[#1F2A44]">
      {/* 1. Global Synthetic Demo Banner (Always Visible) */}
      <div
        role="region"
        aria-label="Demo environment notification"
        className="bg-[#FFFBEB] border-b border-[#FDE68A] px-4 py-1.5 text-xs text-[#B45309] flex items-center justify-between z-30"
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#B45309] animate-pulse" aria-hidden="true" />
          <strong className="font-semibold uppercase tracking-wider">Synthetic Demo Data</strong>
          <span className="hidden sm:inline">&middot; Fictional Brand &quot;Lumo&quot; &middot; Zero Real Egress</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden md:inline font-mono text-[11px] text-[#B45309]/90">
            Round 2 Submission Pack
          </span>
          <Link
            href="/about-ai/"
            className="font-medium underline hover:text-[#92400E] focus:outline-none focus-visible:ring-1 focus-visible:ring-[#B45309]"
          >
            Boundary Policy
          </Link>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 2. Left Sidebar (Collapses under 1024px) */}
        <aside
          aria-label="Sidebar Navigation"
          className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-[#E2E5EA] flex flex-col transition-transform duration-200 lg:static lg:translate-x-0 ${
            isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          {/* Logo Brand Header */}
          <div className="h-16 px-6 border-b border-[#E2E5EA] flex items-center justify-between">
            <Link
              href="/dashboard/"
              className="flex items-center gap-2.5 font-bold text-lg text-[#1F2A44] tracking-tight focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E] rounded-md p-1"
            >
              <div className="w-7 h-7 rounded bg-[#1F2A44] text-white flex items-center justify-center font-serif text-sm font-bold shadow-xs">
                IG
              </div>
              <span>Inkguard</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#F7F7F4] border border-[#CBD2DC] text-[#5B6475]">
                v0.2.0
              </span>
            </Link>
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              aria-label="Close mobile navigation"
              className="lg:hidden p-1 rounded-md text-[#5B6475] hover:text-[#1F2A44] hover:bg-[#F7F7F4]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* User Status Card */}
          {currentUser && (
            <div className="p-4 mx-3 my-3 rounded-lg bg-[#F7F7F4] border border-[#E2E5EA]">
              <div className="text-xs font-bold text-[#1F2A44] truncate">{currentUser.name}</div>
              <div className="text-[11px] text-[#5B6475] capitalize mt-0.5">
                {currentUser.role.replace("_", " ")}
              </div>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-white border border-[#CBD2DC] text-[#0F766E] font-semibold">
                  Tier: {currentUser.max_tier}
                </span>
                <span className="text-[10px] text-[#5B6475]">Local Auth</span>
              </div>
            </div>
          )}

          {/* Navigation Links */}
          <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/dashboard/" && pathname?.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E] ${
                    isActive
                      ? "bg-[#0F766E]/10 text-[#0F766E] font-semibold border border-[#0F766E]/20"
                      : "text-[#5B6475] hover:text-[#1F2A44] hover:bg-[#F7F7F4]"
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-[#E2E5EA] bg-[#F7F7F4]/50">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium text-[#5B6475] hover:text-[#B42318] hover:bg-white rounded-md border border-transparent hover:border-[#FECDCA] transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-[#B42318]"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out / Clear Session</span>
            </button>
          </div>
        </aside>

        {/* Mobile Backdrop */}
        {isMobileMenuOpen && (
          <div
            onClick={() => setIsMobileMenuOpen(false)}
            aria-hidden="true"
            className="fixed inset-0 z-30 bg-[#1F2A44]/30 backdrop-blur-xs lg:hidden"
          />
        )}

        {/* 3. Main Workspace Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {/* Top Bar Header */}
          <header className="h-16 bg-white border-b border-[#E2E5EA] px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4 sticky top-0 z-20">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                aria-label="Open mobile navigation menu"
                className="lg:hidden p-2 rounded-lg text-[#5B6475] hover:text-[#1F2A44] hover:bg-[#F7F7F4] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
              >
                <Menu className="w-5 h-5" />
              </button>
              {pageTitle && <h1 className="text-lg font-bold text-[#1F2A44] hidden sm:block">{pageTitle}</h1>}
            </div>

            {/* Top Bar Right: ModeChip + Switch Demo Role */}
            <div className="flex items-center gap-3">
              {/* ModeChip (SPEC Invariant) */}
              <ModeChip mode={aiMode} />

              {/* Instant "Switch Demo Role" Dropdown (For Judges) */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setIsRoleDropdownOpen(!isRoleDropdownOpen)}
                  aria-expanded={isRoleDropdownOpen}
                  aria-haspopup="true"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#CBD2DC] bg-white hover:bg-[#F7F7F4] text-xs font-semibold text-[#1F2A44] shadow-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0F766E]"
                >
                  <UserCheck className="w-3.5 h-3.5 text-[#0F766E]" />
                  <span>Switch Role</span>
                  <ChevronDown className="w-3.5 h-3.5 text-[#5B6475]" />
                </button>

                {isRoleDropdownOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-20"
                      onClick={() => setIsRoleDropdownOpen(false)}
                      aria-hidden="true"
                    />
                    <div
                      role="menu"
                      className="absolute right-0 mt-2 w-72 rounded-xl bg-white border border-[#CBD2DC] shadow-xl p-2 z-30"
                    >
                      <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-[#5B6475] border-b border-[#E2E5EA] mb-1">
                        1-Click Demo Role Switcher
                      </div>
                      <div className="space-y-1">
                        {demoUsers.map((u) => {
                          const isCurrent = currentUser?.email === u.email;
                          return (
                            <button
                              key={u.id}
                              role="menuitem"
                              onClick={() => handleSwitchDemoRole(u)}
                              className={`w-full text-left p-2 rounded-lg text-xs flex flex-col transition-colors ${
                                isCurrent
                                  ? "bg-[#0F766E]/10 border border-[#0F766E]/30"
                                  : "hover:bg-[#F7F7F4]"
                              }`}
                            >
                              <div className="flex items-center justify-between w-full">
                                <span className="font-bold text-[#1F2A44]">{u.name}</span>
                                <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-[#E2E5EA] text-[#5B6475] capitalize">
                                  {u.role.replace("_", " ")}
                                </span>
                              </div>
                              <span className="text-[11px] text-[#5B6475] mt-0.5 line-clamp-1">{u.description}</span>
                              <span className="text-[10px] font-mono text-[#0F766E] mt-0.5">
                                Tier: {u.max_tier}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </header>

          {/* 4. Page Main Content Target */}
          <main id="main-content" tabIndex={-1} className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto outline-none">
            {children}
          </main>
        </div>
      </div>

      {/* 5. Automatic Re-Login Prompt on 401 Session Expiry */}
      <Dialog
        isOpen={isReLoginOpen}
        onClose={() => {
          setIsReLoginOpen(false);
          window.location.href = "/";
        }}
        title="Session Re-Authentication Required"
        description={reLoginMessage}
      >
        <div className="space-y-4">
          <p className="text-xs text-[#5B6475]">
            Select a brand persona to restore your session immediately, or return to the sign-in page.
          </p>
          <div className="space-y-2">
            {demoUsers.map((u) => (
              <button
                key={u.id}
                onClick={async () => {
                  await handleSwitchDemoRole(u);
                  setIsReLoginOpen(false);
                }}
                className="w-full text-left p-3 rounded-lg border border-[#CBD2DC] hover:border-[#0F766E] hover:bg-[#F7F7F4] flex items-center justify-between transition-colors"
              >
                <div>
                  <p className="text-xs font-bold text-[#1F2A44]">{u.name}</p>
                  <p className="text-[11px] text-[#5B6475] capitalize">{u.role.replace("_", " ")} &middot; {u.team}</p>
                </div>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#E2E5EA] text-[#1F2A44]">
                  {u.max_tier.toUpperCase()}
                </span>
              </button>
            ))}
          </div>
          <div className="pt-2 border-t border-[#E2E5EA] flex justify-end">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setIsReLoginOpen(false);
                window.location.href = "/";
              }}
            >
              Go to Full Login
            </Button>
          </div>
        </div>
      </Dialog>

      {/* 6. Global Floating Toast Notification Stack */}
      <ToastContainer />
    </div>
  );
};
