import React, { forwardRef, useId } from "react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, hint, error, id, className = "", rows = 4, ...props }, ref) => {
    const generatedId = useId();
    const textareaId = id || generatedId;
    const errorId = `${textareaId}-error`;
    const hintId = `${textareaId}-hint`;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={textareaId} className="block text-xs font-semibold text-[#1F2A44] mb-1.5">
            {label}
            {props.required && <span className="text-[#B42318] ml-0.5">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          rows={rows}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          className={`w-full rounded-lg border bg-white p-3 text-sm text-[#1F2A44] placeholder-[#5B6475]/60 transition-colors focus:outline-none focus:ring-2 focus:ring-[#0F766E] disabled:bg-[#F7F7F4] disabled:text-[#5B6475] leading-relaxed ${
            error
              ? "border-[#B42318] focus:border-[#B42318] focus:ring-[#B42318]"
              : "border-[#CBD2DC] hover:border-[#5B6475] focus:border-[#0F766E]"
          } ${className}`}
          {...props}
        />
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

Textarea.displayName = "Textarea";
