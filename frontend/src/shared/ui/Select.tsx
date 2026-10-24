import React, { forwardRef, useId } from "react";
import { ChevronDown } from "lucide-react";

export interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  options: Option[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, hint, error, options, id, className = "", ...props }, ref) => {
    const generatedId = useId();
    const selectId = id || generatedId;
    const errorId = `${selectId}-error`;
    const hintId = `${selectId}-hint`;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-semibold text-[#1F2A44] mb-1.5">
            {label}
            {props.required && <span className="text-[#B42318] ml-0.5">*</span>}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            aria-invalid={error ? "true" : undefined}
            aria-describedby={error ? errorId : hint ? hintId : undefined}
            className={`w-full appearance-none rounded-lg border bg-white px-3 py-2 pr-9 text-sm text-[#1F2A44] transition-colors focus:outline-none focus:ring-2 focus:ring-[#0F766E] disabled:bg-[#F7F7F4] disabled:text-[#5B6475] ${
              error
                ? "border-[#B42318] focus:border-[#B42318] focus:ring-[#B42318]"
                : "border-[#CBD2DC] hover:border-[#5B6475] focus:border-[#0F766E]"
            } ${className}`}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-[#5B6475]">
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
        {error ? (
          <p id={errorId} role="alert" className="mt-1 text-xs font-medium text-[#B42318] flex items-center gap-1">
            <span>●</span> {error}
          </p>
        ) : hint ? (
          <p id={hintId} className="mt-1 text-xs text-[#5B6475]">
            {hint}
          </p>
        ) : null}
      </div>
    );
  }
);

Select.displayName = "Select";
