import React from "react";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  XCircle,
  HelpCircle,
  AlertOctagon,
  FileEdit,
  Clock,
  RotateCcw,
  CheckCheck,
  Globe,
  Ruler,
  Sparkles,
} from "lucide-react";

export type BadgeType =
  | { kind: "severity"; value: "high" | "medium" | "low" }
  | {
      kind: "status";
      value:
        | "Draft"
        | "Checked"
        | "Submitted"
        | "In Review"
        | "Changes Requested"
        | "Approved"
        | "Marked Published";
    }
  | { kind: "verdict"; value: "Supported" | "Contradicted" | "Unverified" | "Expired" }
  | { kind: "source"; value: "rule" | "ai" }
  | { kind: "tier"; value: "public" | "internal" | "confidential" };

interface BadgeProps {
  badge: BadgeType;
  className?: string;
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({ badge, className = "", size = "md" }) => {
  const sizeStyles = size === "sm" ? "text-[11px] px-2 py-0.5 gap-1" : "text-xs px-2.5 py-1 gap-1.5";

  // 1. Severity Badges (WCAG Verified Colors)
  if (badge.kind === "severity") {
    const config = {
      high: {
        bg: "bg-[#FEF3F2]",
        border: "border-[#FECDCA]",
        text: "text-[#B42318]",
        icon: <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "High Severity",
      },
      medium: {
        bg: "bg-[#FFFBEB]",
        border: "border-[#FDE68A]",
        text: "text-[#B45309]",
        icon: <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Medium Severity",
      },
      low: {
        bg: "bg-[#EFF8FF]",
        border: "border-[#B2DDFF]",
        text: "text-[#175CD3]",
        icon: <Info className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Low Severity",
      },
    }[badge.value];

    return (
      <span
        className={`inline-flex items-center font-medium rounded-full border ${config.bg} ${config.border} ${config.text} ${sizeStyles} ${className}`}
      >
        {config.icon}
        <span>{config.label}</span>
      </span>
    );
  }

  // 2. Status Badges
  if (badge.kind === "status") {
    const config = {
      Draft: {
        bg: "bg-[#F7F7F4]",
        border: "border-[#CBD2DC]",
        text: "text-[#5B6475]",
        icon: <FileEdit className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Draft",
      },
      Checked: {
        bg: "bg-[#EFF8FF]",
        border: "border-[#B2DDFF]",
        text: "text-[#175CD3]",
        icon: <CheckCircle className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Checked",
      },
      Submitted: {
        bg: "bg-[#FFFBEB]",
        border: "border-[#FDE68A]",
        text: "text-[#B45309]",
        icon: <Clock className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Submitted",
      },
      "In Review": {
        bg: "bg-[#F0FDF4]",
        border: "border-[#BBF7D0]",
        text: "text-[#15803D]",
        icon: <Clock className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "In Review",
      },
      "Changes Requested": {
        bg: "bg-[#FEF3F2]",
        border: "border-[#FECDCA]",
        text: "text-[#B42318]",
        icon: <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Changes Requested",
      },
      Approved: {
        bg: "bg-[#ECFDF3]",
        border: "border-[#A6F4C5]",
        text: "text-[#067647]",
        icon: <CheckCheck className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Approved",
      },
      "Marked Published": {
        bg: "bg-[#F5F3FF]",
        border: "border-[#DDD6FE]",
        text: "text-[#6D28D9]",
        icon: <Globe className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Published",
      },
    }[badge.value];

    return (
      <span
        className={`inline-flex items-center font-medium rounded-full border ${config.bg} ${config.border} ${config.text} ${sizeStyles} ${className}`}
      >
        {config.icon}
        <span>{config.label}</span>
      </span>
    );
  }

  // 3. Claim Verdict Badges
  if (badge.kind === "verdict") {
    const config = {
      Supported: {
        bg: "bg-[#ECFDF3]",
        border: "border-[#A6F4C5]",
        text: "text-[#067647]",
        icon: <CheckCircle className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Supported",
      },
      Contradicted: {
        bg: "bg-[#FEF3F2]",
        border: "border-[#FECDCA]",
        text: "text-[#B42318]",
        icon: <XCircle className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Contradicted",
      },
      Unverified: {
        bg: "bg-[#FFFBEB]",
        border: "border-[#FDE68A]",
        text: "text-[#B45309]",
        icon: <HelpCircle className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Unverified",
      },
      Expired: {
        bg: "bg-[#FEF3F2]",
        border: "border-[#FECDCA]",
        text: "text-[#B42318]",
        icon: <AlertOctagon className="w-3.5 h-3.5" aria-hidden="true" />,
        label: "Expired Fact",
      },
    }[badge.value];

    return (
      <span
        className={`inline-flex items-center font-medium rounded-full border ${config.bg} ${config.border} ${config.text} ${sizeStyles} ${className}`}
      >
        {config.icon}
        <span>{config.label}</span>
      </span>
    );
  }

  // 4. Source Badges: Rule vs AI (SPEC distinction)
  if (badge.kind === "source") {
    if (badge.value === "rule") {
      return (
        <span
          className={`inline-flex items-center font-semibold rounded-md border border-[#CBD2DC] bg-white text-[#1F2A44] shadow-sm ${sizeStyles} ${className}`}
        >
          <Ruler className="w-3 h-3 text-[#1F2A44]" aria-hidden="true" />
          <span>Rule Check</span>
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center font-semibold rounded-md border border-dashed border-[#0F766E] bg-[#F0FDFA] text-[#0F766E] ${sizeStyles} ${className}`}
      >
        <Sparkles className="w-3 h-3 text-[#0F766E]" aria-hidden="true" />
        <span>AI Finding</span>
      </span>
    );
  }

  // 5. Tier Badges
  const tierConfig = {
    public: "bg-[#ECFDF3] border-[#A6F4C5] text-[#067647]",
    internal: "bg-[#EFF8FF] border-[#B2DDFF] text-[#175CD3]",
    confidential: "bg-[#FEF3F2] border-[#FECDCA] text-[#B42318]",
  }[badge.value];

  return (
    <span
      className={`inline-flex items-center font-mono uppercase text-[10px] tracking-wider rounded border px-2 py-0.5 font-semibold ${tierConfig} ${className}`}
    >
      <span>{badge.value}</span>
    </span>
  );
};
