import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "danger" | "info" | "outline";
}

export function Badge({
  className,
  variant = "default",
  children,
  ...props
}: BadgeProps) {
  const variants = {
    default: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    success: "bg-emerald-50 text-emerald-700 border border-emerald-200/90 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800",
    warning: "bg-amber-50 text-amber-700 border border-amber-200/90 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800",
    danger: "bg-rose-50 text-rose-700 border border-rose-200/90 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800",
    info: "bg-indigo-50 text-indigo-700 border border-indigo-200/90 dark:bg-indigo-950/40 dark:text-indigo-400 dark:border-indigo-800",
    outline: "border border-slate-300 text-slate-700 dark:border-slate-700 dark:text-slate-300",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-3 py-0.5 rounded-full text-xs font-bold leading-5 tracking-wide",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
