import React from "react";
import { Tooltip } from "./Tooltip";
import { ShieldCheck, HardDrive, Cpu, AlertTriangle } from "lucide-react";

export type AIMode = "live" | "cached" | "mock" | "rules_only";

interface ModeChipProps {
  mode: AIMode;
  className?: string;
}

export const ModeChip: React.FC<ModeChipProps> = ({ mode = "mock", className = "" }) => {
  const config = {
    live: {
      label: "Live AI",
      bg: "bg-[#ECFDF3]",
      border: "border-[#A6F4C5]",
      text: "text-[#067647]",
      dot: "bg-[#067647] animate-pulse",
      icon: <Cpu className="w-3.5 h-3.5" />,
      tooltip: "Active Google AI Studio endpoint with strict daily cap and boundary filtering.",
    },
    cached: {
      label: "Cached AI",
      bg: "bg-[#EFF8FF]",
      border: "border-[#B2DDFF]",
      text: "text-[#175CD3]",
      dot: "bg-[#175CD3]",
      icon: <HardDrive className="w-3.5 h-3.5" />,
      tooltip: "Replaying verified pre-computed LLM responses for demo stability and quota protection.",
    },
    mock: {
      label: "Mock Engine",
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      text: "text-[#B45309]",
      dot: "bg-[#B45309]",
      icon: <ShieldCheck className="w-3.5 h-3.5" />,
      tooltip: "Zero network/LLM egress. Completely offline deterministic fixtures for local execution.",
    },
    rules_only: {
      label: "Rules Only",
      bg: "bg-[#F7F7F4]",
      border: "border-[#CBD2DC]",
      text: "text-[#1F2A44]",
      dot: "bg-[#5B6475]",
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
      tooltip: "External AI disabled by policy. Deterministic regex, terminology, and accessibility checks only.",
    },
  }[mode] || {
    label: "Mock Engine",
    bg: "bg-[#FFFBEB]",
    border: "border-[#FDE68A]",
    text: "text-[#B45309]",
    dot: "bg-[#B45309]",
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
    tooltip: "Zero network/LLM egress.",
  };

  return (
    <Tooltip content={config.tooltip}>
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${config.bg} ${config.border} ${config.text} cursor-help select-none ${className}`}
      >
        <span className={`w-2 h-2 rounded-full ${config.dot}`} aria-hidden="true" />
        {config.icon}
        <span>{config.label}</span>
      </div>
    </Tooltip>
  );
};
