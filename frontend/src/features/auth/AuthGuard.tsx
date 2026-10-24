"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { User, DemoUser } from "@/shared/api/types";
import { api } from "@/shared/api/client";
import { Button, Banner } from "@/shared/ui";
import { Lock, UserCheck, ShieldAlert, ArrowRight } from "lucide-react";

interface AuthGuardProps {
  children: React.ReactNode;
  allowedRoles?: Array<"creator" | "reviewer" | "brand_manager" | "admin">;
}

const DEMOS: Record<string, User> = {
  creator: {
    id: "u-creator-social",
    name: "Elena Chen",
    email: "creator.social@lumo.internal",
    role: "creator",
    max_tier: "internal",
    team_id: "Team Social",
    is_active: true,
  },
  agency: {
    id: "u-creator-agency",
    name: "Marcus Vance",
    email: "creator.agency@contractor.external",
    role: "creator",
    max_tier: "public",
    team_id: "External Agency",
    is_active: true,
  },
  reviewer: {
    id: "u-reviewer",
    name: "Sarah Jenkins",
    email: "reviewer.sarah@lumo.internal",
    role: "reviewer",
    max_tier: "internal",
    team_id: "Brand Review",
    is_active: true,
  },
  manager: {
    id: "u-manager",
    name: "Kavita Rao",
    email: "manager.kavita@lumo.internal",
    role: "brand_manager",
    max_tier: "confidential",
    team_id: "Brand Strategy",
    is_active: true,
  },
  admin: {
    id: "u-admin",
    name: "System Admin",
    email: "admin@lumo.internal",
    role: "admin",
    max_tier: "confidential",
    team_id: "Operations",
    is_active: true,
  },
};

export const AuthGuard: React.FC<AuthGuardProps> = ({ children, allowedRoles }) => {
  const defaultUser = allowedRoles && !allowedRoles.includes("creator") ? DEMOS.manager : DEMOS.creator;

  const [user, setUser] = useState<User | null>(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const demoParam = params.get("demo");
      if (demoParam && DEMOS[demoParam.toLowerCase()]) {
        const u = DEMOS[demoParam.toLowerCase()];
        sessionStorage.setItem("inkguard_token", `demo-token-${u.id}`);
        sessionStorage.setItem("inkguard_user", JSON.stringify(u));
        sessionStorage.removeItem("inkguard_logout");
        return u;
      }
      if (sessionStorage.getItem("inkguard_logout") === "true") {
        return null;
      }
      const storedUser = sessionStorage.getItem("inkguard_user");
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          // If stored user is not allowed on this route, switch to defaultUser
          if (allowedRoles && !allowedRoles.includes(parsed.role)) {
            sessionStorage.setItem("inkguard_token", `demo-token-${defaultUser.id}`);
            sessionStorage.setItem("inkguard_user", JSON.stringify(defaultUser));
            return defaultUser;
          }
          return parsed;
        } catch {}
      }
      // Ensure storage has default user token
      sessionStorage.setItem("inkguard_token", `demo-token-${defaultUser.id}`);
      sessionStorage.setItem("inkguard_user", JSON.stringify(defaultUser));
    }
    return defaultUser;
  });

  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const demoParam = params.get("demo");
      if (demoParam && DEMOS[demoParam.toLowerCase()]) {
        const u = DEMOS[demoParam.toLowerCase()];
        return `demo-token-${u.id}`;
      }
      if (sessionStorage.getItem("inkguard_logout") === "true") {
        return null;
      }
      return sessionStorage.getItem("inkguard_token") || `demo-token-${defaultUser.id}`;
    }
    return `demo-token-${defaultUser.id}`;
  });

  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const demoParam = params.get("demo");

      if (demoParam && DEMOS[demoParam.toLowerCase()]) {
        const u = DEMOS[demoParam.toLowerCase()];
        sessionStorage.setItem("inkguard_token", `demo-token-${u.id}`);
        sessionStorage.setItem("inkguard_user", JSON.stringify(u));
        sessionStorage.removeItem("inkguard_logout");
        setUser(u);
        setToken(`demo-token-${u.id}`);
        return;
      }

      if (sessionStorage.getItem("inkguard_logout") === "true") {
        setUser(null);
        setToken(null);
        return;
      }

      const storedUser = sessionStorage.getItem("inkguard_user");
      const storedToken = sessionStorage.getItem("inkguard_token");
      if (storedUser && storedToken) {
        try {
          const parsed = JSON.parse(storedUser);
          if (allowedRoles && !allowedRoles.includes(parsed.role)) {
            sessionStorage.setItem("inkguard_token", `demo-token-${defaultUser.id}`);
            sessionStorage.setItem("inkguard_user", JSON.stringify(defaultUser));
            setUser(defaultUser);
            setToken(`demo-token-${defaultUser.id}`);
            return;
          }
          setUser(parsed);
          setToken(storedToken);
          return;
        } catch {}
      }
    }

    api.getDemoUsers().then((d) => {
      if (d) setDemoUsers(d);
    }).catch(() => {});
  }, []);

  const handleQuickSwitch = async (demo: DemoUser) => {
    try {
      const res = await api.login(demo.email, "LumoDemo2026!");
      sessionStorage.setItem("inkguard_token", res.access_token);
      sessionStorage.setItem("inkguard_user", JSON.stringify(res.user));
      window.location.reload();
    } catch {
      sessionStorage.setItem("inkguard_token", `mock-${demo.id}`);
      sessionStorage.setItem("inkguard_user", JSON.stringify({
        id: demo.id,
        name: demo.name,
        email: demo.email,
        role: demo.role,
        max_tier: demo.max_tier,
        is_active: true,
      }));
      window.location.reload();
    }
  };

  if (isChecking) {
    return (
      <div className="min-h-[400px] flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0F766E]" />
      </div>
    );
  }

  // 1. Not Authenticated
  if (!user || !token) {
    return (
      <div className="max-w-md mx-auto my-16 p-8 bg-white border border-[#CBD2DC] rounded-xl text-center shadow-xs">
        <div className="w-12 h-12 mx-auto rounded-full bg-[#F7F7F4] border border-[#CBD2DC] flex items-center justify-center text-[#1F2A44] mb-4">
          <Lock className="w-6 h-6 text-[#0F766E]" />
        </div>
        <h2 className="text-xl font-bold text-[#1F2A44]">Authentication Required</h2>
        <p className="text-sm text-[#5B6475] mt-2 mb-6">
          You must be signed in with a brand persona to access this governance area.
        </p>
        <Link href="/">
          <Button variant="primary" fullWidth size="lg">
            Go to Sign In
          </Button>
        </Link>
      </div>
    );
  }

  // 2. Role Not Allowed
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    const recommendedDemo = demoUsers.find((d) => allowedRoles.includes(d.role));

    return (
      <div className="max-w-lg mx-auto my-12 p-8 bg-white border border-[#F8D7DA] rounded-xl shadow-xs">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-[#FEF3F2] border border-[#FECDCA] flex items-center justify-center text-[#B42318]">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1F2A44]">Role Clearance Notice</h2>
            <p className="text-xs text-[#5B6475]">Role-Based Access Control Invariant</p>
          </div>
        </div>

        <p className="text-sm text-[#1F2A44] mb-4">
          This workspace is restricted to{" "}
          <strong className="font-semibold text-[#0F766E]">
            {allowedRoles.map((r) => r.replace("_", " ")).join(", ")}
          </strong>
          . Your current persona is <strong className="capitalize">{user.name} ({user.role.replace("_", " ")})</strong>.
        </p>

        {recommendedDemo && (
          <div className="p-4 bg-[#F7F7F4] border border-[#CBD2DC] rounded-lg mb-6">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5B6475] block mb-1">
              Suggested Test Persona
            </span>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-[#1F2A44]">{recommendedDemo.name}</p>
                <p className="text-xs text-[#5B6475] capitalize">{recommendedDemo.role.replace("_", " ")} &middot; {recommendedDemo.team}</p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleQuickSwitch(recommendedDemo)}
                leftIcon={<UserCheck className="w-3.5 h-3.5 text-[#0F766E]" />}
              >
                Switch Role
              </Button>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3">
          <Link href="/dashboard/">
            <Button variant="ghost" size="sm">
              Return to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
