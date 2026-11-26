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
        "bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 active:from-cyan-600 active:to-teal-600 text-slate-950 font-extrabold shadow-md shadow-cyan-950/30 focus-visible:ring-cyan-400 border border-cyan-300/30",
      secondary:
        "bg-[#182336] text-slate-200 hover:bg-[#202E47] active:bg-[#151F30] border border-[#273855] focus-visible:ring-slate-400 font-semibold",
      outline:
        "border border-[#273855] text-slate-300 hover:border-cyan-500/60 hover:text-cyan-300 hover:bg-cyan-950/30 focus-visible:ring-cyan-400 font-semibold",
      danger:
        "bg-rose-600 hover:bg-rose-500 active:bg-rose-700 text-white font-bold shadow-md shadow-rose-950/40 focus-visible:ring-rose-400 border border-rose-400/30",
      ghost:
        "text-slate-400 hover:bg-slate-800/60 hover:text-white focus-visible:ring-slate-400 font-semibold",
    };

    const sizes = {
      sm: "px-3.5 py-1.5 text-xs font-semibold rounded-lg gap-1.5",
      md: "px-4.5 py-2.5 text-xs sm:text-sm font-semibold rounded-xl gap-2",
      lg: "px-6 py-3.5 text-sm sm:text-base font-bold rounded-xl gap-2.5",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[#090D16] disabled:opacity-50 disabled:pointer-events-none select-none cursor-pointer active:scale-[0.98]",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
