import React, { forwardRef, useId } from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leftIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, leftIcon, id, className = "", ...props }, ref) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    const errorId = `${inputId}-error`;
    const hintId = `${inputId}-hint`;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-semibold text-[#1F2A44] mb-1.5">
            {label}
            {props.required && <span className="text-[#B42318] ml-0.5">*</span>}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 text-[#5B6475] pointer-events-none flex items-center">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            aria-invalid={error ? "true" : undefined}
            aria-describedby={error ? errorId : hint ? hintId : undefined}
            className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-[#1F2A44] placeholder-[#5B6475]/60 transition-colors focus:outline-none focus:ring-2 focus:ring-[#0F766E] disabled:bg-[#F7F7F4] disabled:text-[#5B6475] ${
              leftIcon ? "pl-9" : ""
            } ${
              error
                ? "border-[#B42318] focus:border-[#B42318] focus:ring-[#B42318]"
                : "border-[#CBD2DC] hover:border-[#5B6475] focus:border-[#0F766E]"
            } ${className}`}
            {...props}
          />
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

Input.displayName = "Input";
