import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean;
}

export function Card({
  className,
  children,
  glow = false,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "bg-[#111827] dark:bg-[#111827] border border-[#202D45] rounded-2xl shadow-lg transition-all duration-200 overflow-hidden relative group",
        glow && "hover:border-cyan-500/40 hover:shadow-cyan-950/20",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-5 py-4 sm:px-6 sm:py-5 border-b border-[#1C273C] bg-[#141C2E]/50 flex flex-col justify-between gap-1",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2",
        className
      )}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        "text-xs sm:text-sm text-slate-400 font-normal leading-relaxed",
        className
      )}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-5 sm:p-6", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-5 py-3.5 sm:px-6 sm:py-4 border-t border-[#1C273C] flex items-center bg-[#0F1624]/60",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
