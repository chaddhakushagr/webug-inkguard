import React from "react";
import { AlertTriangle, Info, CheckCircle2, AlertCircle } from "lucide-react";

export interface BannerProps {
  type?: "demo" | "warning" | "info" | "success" | "error";
  title?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const Banner: React.FC<BannerProps> = ({
  type = "info",
  title,
  children,
  action,
  className = "",
}) => {
  const config = {
    demo: {
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      text: "text-[#B45309]",
      icon: <AlertTriangle className="w-4 h-4 text-[#B45309] flex-shrink-0" />,
    },
    warning: {
      bg: "bg-[#FFFBEB]",
      border: "border-[#FDE68A]",
      text: "text-[#B45309]",
      icon: <AlertTriangle className="w-4 h-4 text-[#B45309] flex-shrink-0" />,
    },
    info: {
      bg: "bg-[#EFF8FF]",
      border: "border-[#B2DDFF]",
      text: "text-[#175CD3]",
      icon: <Info className="w-4 h-4 text-[#175CD3] flex-shrink-0" />,
    },
    success: {
      bg: "bg-[#ECFDF3]",
      border: "border-[#A6F4C5]",
      text: "text-[#067647]",
      icon: <CheckCircle2 className="w-4 h-4 text-[#067647] flex-shrink-0" />,
    },
    error: {
      bg: "bg-[#FEF3F2]",
      border: "border-[#FECDCA]",
      text: "text-[#B42318]",
      icon: <AlertCircle className="w-4 h-4 text-[#B42318] flex-shrink-0" />,
    },
  }[type];

  return (
    <div
      role="region"
      aria-label={title || "Notification banner"}
      className={`p-3.5 sm:p-4 rounded-lg border ${config.bg} ${config.border} flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs sm:text-sm ${className}`}
    >
      <div className="flex items-start gap-2.5">
        <div className="mt-0.5">{config.icon}</div>
        <div>
          {title && <span className={`font-bold mr-1.5 ${config.text}`}>{title}:</span>}
          <span className="text-[#1F2A44] leading-normal">{children}</span>
        </div>
      </div>
      {action && <div className="flex-shrink-0 self-end sm:self-auto">{action}</div>}
    </div>
  );
};
