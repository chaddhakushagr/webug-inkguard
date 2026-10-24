"use client";

import React, { useEffect } from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, X } from "lucide-react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
  message: string;
  title?: string;
}

interface ToastProps {
  toast: ToastMessage;
  onDismiss: (id: string) => void;
  durationMs?: number;
}

export const Toast: React.FC<ToastProps> = ({ toast, onDismiss, durationMs = 4000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, durationMs);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss, durationMs]);

  const config = {
    success: {
      bg: "bg-[#ECFDF3]",
      border: "border-[#A6F4C5]",
      text: "text-[#067647]",
      icon: <CheckCircle2 className="w-5 h-5 text-[#067647] flex-shrink-0" />,
    },
    error: {
      bg: "bg-[#FEF3F2]",
      border: "border-[#FECDCA]",
      text: "text-[#B42318]",
      icon: <AlertCircle className="w-5 h-5 text-[#B42318] flex-shrink-0" />,
    },
    info: {
      bg: "bg-[#EFF8FF]",
      border: "border-[#B2DDFF]",
      text: "text-[#175CD3]",
      icon: <AlertTriangle className="w-5 h-5 text-[#175CD3] flex-shrink-0" />,
    },
  }[toast.type];

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-start gap-3 p-4 rounded-lg border shadow-lg ${config.bg} ${config.border} max-w-sm w-full transition-all`}
    >
      {config.icon}
      <div className="flex-1">
        {toast.title && <h4 className={`text-sm font-bold ${config.text}`}>{toast.title}</h4>}
        <p className="text-xs text-[#1F2A44] mt-0.5">{toast.message}</p>
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        className="text-[#5B6475] hover:text-[#1F2A44] p-0.5 rounded focus:outline-none focus-visible:ring-1 focus-visible:ring-[#0F766E]"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
