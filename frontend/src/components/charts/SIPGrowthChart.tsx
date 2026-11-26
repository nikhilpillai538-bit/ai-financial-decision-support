"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { formatCurrency } from "@/lib/formatters";

export interface SIPSchedulePoint {
  month: number;
  investment: string;
  interest: string;
  balance: string;
}

export function SIPGrowthChart({
  schedule,
  height = 280,
  currency = "INR",
}: {
  schedule?: SIPSchedulePoint[];
  height?: number;
  currency?: string;
}) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!schedule || schedule.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-xs text-slate-400 border border-dashed border-[#202D45] rounded-xl bg-[#0D1422]/40 p-4">
        <span className="font-semibold text-slate-300 mb-1">No SIP Schedule Calculated</span>
        <span className="text-[11px] text-slate-400">Calculate a projection above to model compound wealth accumulation</span>
      </div>
    );
  }

  // Sample points if schedule is long (e.g. monthly for 10 years = 120 points)
  const step = Math.max(1, Math.floor(schedule.length / 30));
  const sampledData = schedule.filter((_, idx) => idx % step === 0 || idx === schedule.length - 1);

  const chartData = sampledData.map((pt) => ({
    month: pt.month,
    year: (pt.month / 12).toFixed(1),
    invested: parseFloat(pt.investment) || 0,
    balance: parseFloat(pt.balance) || 0,
    wealthGain: Math.max(0, (parseFloat(pt.balance) || 0) - (parseFloat(pt.investment) || 0)),
  }));

  if (!isMounted) {
    return (
      <div
        style={{ width: "100%", height }}
        className="flex items-center justify-center bg-[#0D1422]/40 rounded-xl animate-pulse text-xs text-slate-400"
      >
        Calculating compounding growth...
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="wealthGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="investedGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1C283F" />
          <XAxis
            dataKey="month"
            tickFormatter={(m) => `Mo ${m}`}
            tick={{ fontSize: 11, fill: "#64748B" }}
            axisLine={{ stroke: "#24334F" }}
          />
          <YAxis
            tickFormatter={(val) => {
              if (val >= 10000000) return `${(val / 10000000).toFixed(1)}Cr`;
              if (val >= 100000) return `${(val / 100000).toFixed(1)}L`;
              if (val >= 1000) return `${(val / 1000).toFixed(0)}k`;
              return String(val);
            }}
            tick={{ fontSize: 11, fill: "#64748B" }}
            axisLine={{ stroke: "#24334F" }}
          />
          <Tooltip
            formatter={(val: any, name: any) => [
              formatCurrency(Number(val), currency),
              name === "balance" ? "Total Future Value" : "Capital Invested",
            ]}
            labelFormatter={(label) => `Month ${label}`}
            contentStyle={{
              backgroundColor: "#0C121E",
              borderColor: "#22314E",
              borderRadius: "0.75rem",
              color: "#F8FAFC",
              fontSize: "0.75rem",
              boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
              padding: "8px 12px",
            }}
          />
          <Legend
            iconType="circle"
            wrapperStyle={{ fontSize: "0.75rem", paddingTop: "8px", color: "#94A3B8" }}
          />
          <Area
            type="monotone"
            dataKey="balance"
            name="Future Value"
            stroke="#10B981"
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#wealthGradient)"
          />
          <Area
            type="monotone"
            dataKey="invested"
            name="Total Invested"
            stroke="#06B6D4"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#investedGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
