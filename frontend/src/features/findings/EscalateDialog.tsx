"use client";

import React, { useState } from "react";
import { Dialog, Button } from "@/shared/ui";
import { ArrowUpRight, HelpCircle } from "lucide-react";

interface EscalateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (note: string) => Promise<void>;
  findingExcerpt: string;
}

export const EscalateDialog: React.FC<EscalateDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  findingExcerpt,
}) => {
  const [note, setNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onConfirm(note.trim() || "Escalated for brand manager review");
      onClose();
      setNote("");
    } catch (err: any) {
      setError(err.message || "Failed to escalate finding");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Escalate Finding to Brand Manager"
      description={`Request managerial guidance on: "${findingExcerpt}"`}
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div className="p-3 bg-[#EFF8FF] border border-[#B2DDFF] text-[#175CD3] rounded-lg flex items-start gap-2">
          <HelpCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            Escalating will notify the assigned brand manager and create a priority review ticket for editorial guidance.
          </span>
        </div>

        {error && (
          <div className="p-2.5 bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] rounded-lg">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="escalate-note" className="block font-bold text-[#1F2A44] mb-1">
            Question or Context for Manager
          </label>
          <textarea
            id="escalate-note"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Explain the ambiguity or question requiring leadership sign-off..."
            className="w-full p-2.5 rounded-lg border border-[#CBD2DC] bg-white text-xs text-[#1F2A44] focus:outline-none focus:ring-2 focus:ring-[#0F766E]"
          />
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-[#E2E5EA]">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={isSubmitting}
            leftIcon={<ArrowUpRight className="w-3.5 h-3.5" />}
          >
            Escalate Finding
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
