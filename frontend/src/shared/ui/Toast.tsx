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
      className={`flex items-start gap-3 p-4 rounded-lg border shadow-lg ${config.bg} ${config.border} max-w-sm w-full transition-all animate-in fade-in slide-in-from-bottom-2`}
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

export function toast(message: string, type: "success" | "error" | "info" = "info", title?: string) {
  if (typeof window !== "undefined") {
    window.dispatchEvent(
      new CustomEvent("inkguard:toast", {
        detail: {
          id: Math.random().toString(36).substring(2, 9),
          message,
          type,
          title,
        },
      })
    );
  }
}

export const ToastContainer: React.FC = () => {
  const [toasts, setToasts] = React.useState<ToastMessage[]>([]);

  React.useEffect(() => {
    const handleToast = (e: any) => {
      if (e?.detail) {
        setToasts((prev) => [...prev, e.detail]);
      }
    };
    window.addEventListener("inkguard:toast", handleToast);
    return () => window.removeEventListener("inkguard:toast", handleToast);
  }, []);

  const handleDismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none"
    >
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <Toast toast={t} onDismiss={handleDismiss} />
        </div>
      ))}
    </div>
  );
};

