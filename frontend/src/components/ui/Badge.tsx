import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "danger" | "info" | "outline" | "cyan";
}

export function Badge({
  className,
  variant = "default",
  children,
  ...props
}: BadgeProps) {
  const variants = {
    default: "bg-[#162134] text-slate-300 border border-[#263753]",
    success: "bg-emerald-950/60 text-emerald-300 border border-emerald-800/80",
    warning: "bg-amber-950/60 text-amber-300 border border-amber-800/80",
    danger: "bg-rose-950/60 text-rose-300 border border-rose-800/80",
    info: "bg-cyan-950/60 text-cyan-300 border border-cyan-800/80",
    cyan: "bg-cyan-950/60 text-cyan-300 border border-cyan-500/30",
    outline: "border border-[#273855] text-slate-300 bg-transparent",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold leading-4 tracking-wide shrink-0",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
