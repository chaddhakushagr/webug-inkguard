"use client";

import React, { useEffect, useState } from "react";
import { Loader2, CheckCircle2 } from "lucide-react";

export function ColdStartBanner() {
  const [isWaking, setIsWaking] = useState(false);
  const [isAwake, setIsAwake] = useState(false);

  useEffect(() => {
    const handleColdStart = (e: Event) => {
      const customEvent = e as CustomEvent<{ waking: boolean; message?: string }>;
      if (customEvent.detail?.waking) {
        setIsWaking(true);
        setIsAwake(false);
      } else {
        setIsWaking(false);
        setIsAwake(true);
        const timer = setTimeout(() => setIsAwake(false), 3500);
        return () => clearTimeout(timer);
      }
    };

    window.addEventListener("inkguard:cold_start", handleColdStart);
    return () => window.removeEventListener("inkguard:cold_start", handleColdStart);
  }, []);

  if (!isWaking && !isAwake) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed top-0 left-0 right-0 z-50 text-center py-2 px-4 text-xs font-semibold flex items-center justify-center gap-2 shadow-md transition-all duration-300 ${
        isWaking
          ? "bg-[#0F766E] text-white border-b border-[#0D655E]"
          : "bg-[#067647] text-white border-b border-[#05603A]"
      }`}
    >
      {isWaking ? (
        <>
          <Loader2 className="w-3.5 h-3.5 animate-spin text-white flex-shrink-0" />
          <span>Waking the server, this can take about a minute</span>
        </>
      ) : (
        <>
          <CheckCircle2 className="w-3.5 h-3.5 text-white flex-shrink-0" />
          <span>Server is awake and ready</span>
        </>
      )}
    </div>
  );
}
