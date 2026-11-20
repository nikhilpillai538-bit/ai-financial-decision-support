import React from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/Card";

export interface MetricCardProps {
  title: string;
  value: React.ReactNode;
  subtitle?: string;
  icon?: React.ReactNode;
  variant?: "default" | "success" | "danger" | "warning" | "brand";
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
  const iconBg = {
    default: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    success: "bg-emerald-50 text-emerald-600 border border-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400",
    danger: "bg-rose-50 text-rose-600 border border-rose-100 dark:bg-rose-950/50 dark:text-rose-400",
    warning: "bg-amber-50 text-amber-600 border border-amber-100 dark:bg-amber-950/50 dark:text-amber-400",
    brand: "bg-indigo-50 text-indigo-600 border border-indigo-100 dark:bg-indigo-950/50 dark:text-indigo-400",
  };

  return (
    <Card className={cn("transition-all duration-200 hover:shadow-fintech hover:-translate-y-0.5", className)}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1.5 flex-1 min-w-0">
            <p className="text-xs font-bold text-slate-500 dark:text-slate-400 tracking-wider uppercase">
              {title}
            </p>
            <div className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 truncate">
              {value}
            </div>
          </div>
          {icon && (
            <div className={cn("p-3.5 rounded-2xl flex items-center justify-center shrink-0 shadow-xs", iconBg[variant])}>
              {icon}
            </div>
          )}
        </div>

        {(subtitle || trend) && (
          <div className="mt-4 flex items-center text-sm text-slate-600 dark:text-slate-400 gap-2 flex-wrap">
            {trend && (
              <span
                className={cn(
                  "font-bold px-2 py-0.5 rounded-full text-xs inline-flex items-center",
                  trend.isPositive
                    ? "text-emerald-700 bg-emerald-50 border border-emerald-200 dark:text-emerald-400 dark:bg-emerald-950/50"
                    : "text-rose-700 bg-rose-50 border border-rose-200 dark:text-rose-400 dark:bg-rose-950/50"
                )}
              >
                {trend.value}
              </span>
            )}
            {trend?.label && <span className="font-medium text-slate-500">{trend.label}</span>}
            {trend && subtitle && <span className="text-slate-300">•</span>}
            {subtitle && <span className="font-normal text-slate-500">{subtitle}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
