import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, type = "text", id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1.5"
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          ref={ref}
          className={cn(
            "w-full px-4 py-2.5 text-sm md:text-base bg-white dark:bg-slate-900 border rounded-xl transition-all duration-150 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 disabled:bg-slate-50 disabled:cursor-not-allowed dark:disabled:bg-slate-800 shadow-2xs",
            error
              ? "border-rose-300 text-rose-900 focus:ring-rose-500/20 focus:border-rose-500"
              : "border-slate-300/90 dark:border-slate-700 text-slate-900 dark:text-slate-100 hover:border-slate-400",
            className
          )}
          {...props}
        />
        {error && <p className="text-sm font-medium text-rose-600 dark:text-rose-400 mt-1.5">{error}</p>}
        {helperText && !error && (
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1.5">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
