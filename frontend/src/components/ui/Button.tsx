"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const variants = {
      primary:
        "bg-linear-to-r from-indigo-600 to-indigo-700 text-white hover:from-indigo-500 hover:to-indigo-600 active:from-indigo-700 active:to-indigo-800 shadow-sm hover:shadow-indigo-500/25 focus-visible:ring-indigo-500",
      secondary:
        "bg-slate-100 text-slate-800 hover:bg-slate-200 active:bg-slate-300 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 focus-visible:ring-slate-400",
      outline:
        "border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800 focus-visible:ring-slate-400",
      danger:
        "bg-linear-to-r from-rose-600 to-rose-700 text-white hover:from-rose-500 hover:to-rose-600 active:from-rose-700 active:to-rose-800 shadow-sm hover:shadow-rose-500/25 focus-visible:ring-rose-500",
      ghost:
        "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 focus-visible:ring-slate-400",
    };

    const sizes = {
      sm: "px-3.5 py-2 text-xs font-semibold rounded-lg",
      md: "px-5 py-2.5 text-sm font-semibold rounded-xl",
      lg: "px-6 py-3.5 text-base font-bold rounded-xl",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none cursor-pointer active:scale-[0.98]",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
