import React from "react";
import { Check, Clock, AlertTriangle, FileEdit, CheckCheck, Globe, RotateCcw } from "lucide-react";

export type StepState =
  | "Draft"
  | "Checked"
  | "Submitted"
  | "In Review"
  | "Changes Requested"
  | "Approved"
  | "Marked Published";

interface StatusStepperProps {
  currentStatus: StepState;
  className?: string;
}

const STEPS: { status: StepState; label: string; icon: React.ReactNode }[] = [
  { status: "Draft", label: "Draft", icon: <FileEdit className="w-3.5 h-3.5" /> },
  { status: "Checked", label: "Checked", icon: <Check className="w-3.5 h-3.5" /> },
  { status: "Submitted", label: "Submitted", icon: <Clock className="w-3.5 h-3.5" /> },
  { status: "In Review", label: "In Review", icon: <Clock className="w-3.5 h-3.5" /> },
  { status: "Approved", label: "Approved", icon: <CheckCheck className="w-3.5 h-3.5" /> },
  { status: "Marked Published", label: "Published", icon: <Globe className="w-3.5 h-3.5" /> },
];

export const StatusStepper: React.FC<StatusStepperProps> = ({ currentStatus, className = "" }) => {
  const isChangesRequested = currentStatus === "Changes Requested";

  const getStepIndex = (st: StepState) => {
    if (st === "Changes Requested") return 3; // Linked to In Review
    return STEPS.findIndex((s) => s.status === st);
  };

  const currentIndex = getStepIndex(currentStatus);

  return (
    <div className={`w-full bg-white rounded-lg border border-[#E2E5EA] p-4 sm:p-5 ${className}`}>
      <div className="flex items-center justify-between overflow-x-auto pb-2 sm:pb-0 gap-2">
        {STEPS.map((step, idx) => {
          const isCompleted = idx < currentIndex;
          const isCurrent = idx === currentIndex && !isChangesRequested;

          return (
            <React.Fragment key={step.status}>
              <div className="flex flex-col items-center flex-1 min-w-[70px]">
                <div
                  aria-current={isCurrent ? "step" : undefined}
                  className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                    isCompleted
                      ? "bg-[#067647] text-white"
                      : isCurrent
                      ? "bg-[#0F766E] text-white ring-4 ring-[#0F766E]/20"
                      : "bg-[#F7F7F4] text-[#5B6475] border border-[#CBD2DC]"
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : step.icon}
                </div>
                <span
                  className={`mt-1.5 text-xs text-center font-medium whitespace-nowrap ${
                    isCurrent
                      ? "text-[#0F766E] font-bold"
                      : isCompleted
                      ? "text-[#1F2A44]"
                      : "text-[#5B6475]"
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {idx < STEPS.length - 1 && (
                <div
                  aria-hidden="true"
                  className={`flex-1 h-0.5 mx-1 hidden sm:block ${
                    idx < currentIndex ? "bg-[#067647]" : "bg-[#E2E5EA]"
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Changes Requested Branch Callout */}
      {isChangesRequested && (
        <div
          role="status"
          className="mt-3 pt-3 border-t border-[#FECDCA] flex items-center justify-between text-xs bg-[#FEF3F2] p-2.5 rounded-md text-[#B42318]"
        >
          <div className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-[#B42318]" />
            <span className="font-semibold">Workflow Branch: Changes Requested</span>
            <span className="text-[#1F2A44] hidden sm:inline">
              &mdash; Reviewer returned submission to author for edits.
            </span>
          </div>
          <span className="font-mono text-[11px] bg-white px-2 py-0.5 rounded border border-[#FECDCA]">
            Action required by Creator
          </span>
        </div>
      )}
    </div>
  );
};
