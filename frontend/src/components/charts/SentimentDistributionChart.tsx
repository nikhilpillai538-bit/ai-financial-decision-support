"use client";

import React from "react";
import { formatPercentage } from "@/lib/formatters";

export function SentimentDistributionChart({
  positive,
  negative,
  neutral,
  total,
  overallLabel = "neutral",
}: {
  positive: number;
  negative: number;
  neutral: number;
  total: number;
  overallLabel?: string;
}) {
  if (total === 0) {
    return (
      <div className="text-center py-6 text-xs text-slate-400">
        No sentiment data available for this window.
      </div>
    );
  }

  const labelColors = {
    bullish: "text-emerald-700 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800",
    bearish: "text-rose-700 bg-rose-50 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800",
    neutral: "text-slate-700 bg-slate-50 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  };

  const badgeColor =
    labelColors[overallLabel.toLowerCase() as keyof typeof labelColors] || labelColors.neutral;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          Market Stance:
        </span>
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wide border ${badgeColor}`}
        >
          {overallLabel}
        </span>
      </div>

      {/* Segmented Bar */}
      <div className="h-3 w-full rounded-full overflow-hidden flex bg-slate-100 dark:bg-slate-800">
        {positive > 0 && (
          <div
            style={{ width: `${positive}%` }}
            className="bg-emerald-500 h-full transition-all"
            title={`Positive: ${positive}%`}
          />
        )}
        {neutral > 0 && (
          <div
            style={{ width: `${neutral}%` }}
            className="bg-slate-400 h-full transition-all"
            title={`Neutral: ${neutral}%`}
          />
        )}
        {negative > 0 && (
          <div
            style={{ width: `${negative}%` }}
            className="bg-rose-500 h-full transition-all"
            title={`Negative: ${negative}%`}
          />
        )}
      </div>

      {/* Legend & Percentages */}
      <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 pt-1">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
          <span>Positive: {formatPercentage(positive)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block" />
          <span>Neutral: {formatPercentage(neutral)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
          <span>Negative: {formatPercentage(negative)}</span>
        </div>
      </div>
    </div>
  );
}
