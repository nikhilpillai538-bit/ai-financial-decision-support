"use client";

import React from "react";
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
  if (!schedule || schedule.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-400">
        Calculate a SIP projection above to visualize wealth accumulation over time.
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

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="wealthGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="investedGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis
            dataKey="month"
            tickFormatter={(m) => `Mo ${m}`}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={{ stroke: "#cbd5e1" }}
          />
          <YAxis
            tickFormatter={(val) => {
              if (val >= 10000000) return `${(val / 10000000).toFixed(1)}Cr`;
              if (val >= 100000) return `${(val / 100000).toFixed(1)}L`;
              if (val >= 1000) return `${(val / 1000).toFixed(0)}k`;
              return String(val);
            }}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={{ stroke: "#cbd5e1" }}
          />
          <Tooltip
            formatter={(val: any, name: any) => [
              formatCurrency(Number(val), currency),
              name === "balance" ? "Total Future Value" : "Capital Invested",
            ]}
            labelFormatter={(label) => `Month ${label}`}
            contentStyle={{
              backgroundColor: "#1e293b",
              borderColor: "#334155",
              borderRadius: "0.5rem",
              color: "#f8fafc",
              fontSize: "0.75rem",
            }}
          />
          <Legend
            iconType="circle"
            wrapperStyle={{ fontSize: "0.75rem", paddingTop: "8px" }}
          />
          <Area
            type="monotone"
            dataKey="balance"
            name="Future Value"
            stroke="#10b981"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#wealthGradient)"
          />
          <Area
            type="monotone"
            dataKey="invested"
            name="Total Invested"
            stroke="#6366f1"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#investedGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
