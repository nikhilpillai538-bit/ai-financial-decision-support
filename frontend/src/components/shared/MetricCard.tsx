import React from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/Card";

export interface MetricCardProps {
  title: string;
  value: React.ReactNode;
  subtitle?: string;
  icon?: React.ReactNode;
  variant?: "default" | "success" | "danger" | "warning" | "brand" | "cyan";
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon,
  variant = "default",
  trend,
  className,
}: MetricCardProps) {
  const iconBg: Record<string, string> = {
    default: "bg-[#182336] text-slate-300 border border-[#273855]",
    success: "bg-emerald-950/60 text-emerald-400 border border-emerald-800/70",
    danger: "bg-rose-950/60 text-rose-400 border border-rose-800/70",
    warning: "bg-amber-950/60 text-amber-400 border border-amber-800/70",
    brand: "bg-cyan-950/60 text-cyan-400 border border-cyan-800/70",
    cyan: "bg-cyan-950/60 text-cyan-400 border border-cyan-800/70",
  };

  const topBorderGlow: Record<string, string> = {
    default: "before:bg-slate-700",
    success: "before:bg-emerald-500",
    danger: "before:bg-rose-500",
    warning: "before:bg-amber-500",
    brand: "before:bg-gradient-to-r before:from-cyan-400 before:to-teal-400",
    cyan: "before:bg-gradient-to-r before:from-cyan-400 before:to-teal-400",
  };

  return (
    <Card
      className={cn(
        "relative transition-all duration-200 hover:shadow-xl hover:-translate-y-0.5 overflow-hidden",
        "before:content-[''] before:absolute before:top-0 before:left-0 before:right-0 before:h-[2px]",
        topBorderGlow[variant],
        className
      )}
    >
      <CardContent className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1.5 flex-1 min-w-0">
            <p className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">
              {title}
            </p>
            <div className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white truncate">
              {value}
            </div>
          </div>
          {icon && (
            <div className={cn("p-2.5 sm:p-3 rounded-xl flex items-center justify-center shrink-0 shadow-sm", iconBg[variant])}>
              {icon}
            </div>
          )}
        </div>

        {(subtitle || trend) && (
          <div className="mt-3.5 pt-3 border-t border-[#1C273C] flex items-center text-xs text-slate-400 gap-2 flex-wrap">
            {trend && (
              <span
                className={cn(
                  "font-bold px-2 py-0.5 rounded-md text-[10px] inline-flex items-center",
                  trend.isPositive
                    ? "text-emerald-300 bg-emerald-950/60 border border-emerald-800/60"
                    : "text-rose-300 bg-rose-950/60 border border-rose-800/60"
                )}
              >
                {trend.value}
              </span>
            )}
            {trend?.label && <span className="font-medium text-slate-400">{trend.label}</span>}
            {trend && subtitle && <span className="text-slate-600">•</span>}
            {subtitle && <span className="font-normal text-slate-400 truncate">{subtitle}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
