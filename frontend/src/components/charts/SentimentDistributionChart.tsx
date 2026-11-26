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
      <div className="flex flex-col items-center justify-center py-6 text-xs text-slate-400 border border-dashed border-[#202D45] rounded-xl bg-[#0D1422]/40 p-4">
        <span className="font-semibold text-slate-300 mb-1">No FinBERT Sentiment Ingested</span>
        <span className="text-[11px] text-slate-400">Fetch live RSS feeds on Market News to score articles</span>
      </div>
    );
  }

  const labelColors = {
    bullish: "text-emerald-300 bg-emerald-950/60 border-emerald-800/80",
    bearish: "text-rose-300 bg-rose-950/60 border-rose-800/80",
    neutral: "text-slate-300 bg-slate-800/60 border-slate-700/80",
  };

  const badgeColor =
    labelColors[overallLabel.toLowerCase() as keyof typeof labelColors] || labelColors.neutral;

  return (
    <div className="space-y-3.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-400 font-medium">
          Market FinBERT Stance:
        </span>
        <span
          className={`text-[11px] px-3 py-0.5 rounded-full font-bold uppercase tracking-wider border ${badgeColor}`}
        >
          {overallLabel}
        </span>
      </div>

      {/* Segmented Bar */}
      <div className="h-3.5 w-full rounded-full overflow-hidden flex bg-[#0A0E18] p-0.5 border border-[#1E2C44]">
        {positive > 0 && (
          <div
            style={{ width: `${positive}%` }}
            className="bg-emerald-500 h-full rounded-l-full transition-all"
            title={`Positive: ${positive}%`}
          />
        )}
        {neutral > 0 && (
          <div
            style={{ width: `${neutral}%` }}
            className="bg-slate-500 h-full transition-all"
            title={`Neutral: ${neutral}%`}
          />
        )}
        {negative > 0 && (
          <div
            style={{ width: `${negative}%` }}
            className="bg-rose-500 h-full rounded-r-full transition-all"
            title={`Negative: ${negative}%`}
          />
        )}
      </div>

      {/* Legend & Percentages */}
      <div className="flex items-center justify-between text-xs text-slate-300 pt-1 flex-wrap gap-2">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block shadow-xs" />
          <span className="font-medium">Positive: {formatPercentage(positive)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block shadow-xs" />
          <span className="font-medium">Neutral: {formatPercentage(neutral)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-400 inline-block shadow-xs" />
          <span className="font-medium">Negative: {formatPercentage(negative)}</span>
        </div>
      </div>
    </div>
  );
}
