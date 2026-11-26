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
            className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5"
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          ref={ref}
          className={cn(
            "w-full px-3.5 py-2.5 text-xs sm:text-sm bg-[#0E1524] border rounded-xl transition-all duration-150 placeholder:text-slate-400 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 disabled:bg-slate-900/50 disabled:text-slate-400 disabled:cursor-not-allowed shadow-inner",
            error
              ? "border-rose-500/80 text-rose-200 focus:ring-rose-500/20 focus:border-rose-500"
              : "border-[#202D45] hover:border-[#2C3E5E]",
            className
          )}
          {...props}
        />
        {error && <p className="text-xs font-semibold text-rose-400 mt-1.5">{error}</p>}
        {helperText && !error && (
          <p className="text-xs text-slate-400 mt-1.5">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
