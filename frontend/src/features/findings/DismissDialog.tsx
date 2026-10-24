"use client";

import React, { useState } from "react";
import { Dialog, Button } from "@/shared/ui";
import { AlertTriangle } from "lucide-react";

interface DismissDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reasonCode: string, reasonText: string) => Promise<void>;
  findingExcerpt: string;
}

const REASON_CODES = [
  { code: "brand_exception", label: "Approved Executive Exception" },
  { code: "creative_license", label: "Intentional Creative / Stylistic Expression" },
  { code: "rule_false_positive", label: "Rule False Positive / Inaccurate Match" },
  { code: "legal_override", label: "Legal / Regulatory Counsel Override" },
  { code: "already_addressed", label: "Addressed in Context / Disclosed Elsewhere" },
];

export const DismissDialog: React.FC<DismissDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  findingExcerpt,
}) => {
  const [reasonCode, setReasonCode] = useState(REASON_CODES[0].code);
  const [reasonText, setReasonText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reasonText.trim()) {
      setValidationError("A detailed justification is strictly required to dismiss brand compliance findings.");
      return;
    }
    setValidationError(null);
    setIsSubmitting(true);
    try {
      await onConfirm(reasonCode, reasonText.trim());
      onClose();
      setReasonText("");
    } catch (err: any) {
      setValidationError(err.message || "Failed to dismiss finding");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Dismiss Brand Governance Finding"
      description={`Overriding finding on copy excerpt: "${findingExcerpt}"`}
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div className="p-3 bg-[#FFFBEB] border border-[#FDE68A] text-[#B45309] rounded-lg flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            <strong>Audit Requirement:</strong> All dismissed findings are recorded in the immutable SHA-256 hash-chained audit log with your actor ID and reason code.
          </span>
        </div>

        {validationError && (
          <div className="p-2.5 bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] rounded-lg">
            {validationError}
          </div>
        )}

        <div>
          <label htmlFor="dismiss-reason-code" className="block font-bold text-[#1F2A44] mb-1">
            Dismissal Reason Code <span className="text-[#B42318]">*</span>
          </label>
          <select
            id="dismiss-reason-code"
            value={reasonCode}
            onChange={(e) => setReasonCode(e.target.value)}
            className="w-full p-2.5 rounded-lg border border-[#CBD2DC] bg-white text-xs text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
            required
          >
            {REASON_CODES.map((r) => (
              <option key={r.code} value={r.code}>
                {r.label} ({r.code})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="dismiss-reason-text" className="block font-bold text-[#1F2A44] mb-1">
            Justification &amp; Clinical/Legal Evidence <span className="text-[#B42318]">*</span>
          </label>
          <textarea
            id="dismiss-reason-text"
            rows={3}
            value={reasonText}
            onChange={(e) => setReasonText(e.target.value)}
            placeholder="Explain why this finding does not apply or cite specific executive clearance..."
            className="w-full p-2.5 rounded-lg border border-[#CBD2DC] bg-white text-xs text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
            required
          />
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-[#E2E5EA]">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="danger"
            size="sm"
            isLoading={isSubmitting}
            disabled={!reasonText.trim()}
          >
            Confirm Dismissal
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
