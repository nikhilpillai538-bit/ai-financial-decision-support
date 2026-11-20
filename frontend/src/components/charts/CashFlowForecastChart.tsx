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
  ReferenceLine,
} from "recharts";
import { DailyProjection } from "@/types";
import { formatCurrency, formatDate } from "@/lib/formatters";

export function CashFlowForecastChart({
  data,
  height = 280,
  currency = "INR",
}: {
  data: DailyProjection[];
  height?: number;
  currency?: string;
}) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-400">
        No forecast timeline data available.
      </div>
    );
  }

  const chartData = data.map((d) => ({
    date: d.date,
    displayDate: formatDate(d.date),
    balance: parseFloat(d.closing_balance || d.projected_balance || "0") || 0,
    inflow: parseFloat(d.projected_income || d.inflow || "0") || 0,
    outflow: parseFloat(d.projected_expenses || d.outflow || "0") || 0,
  }));

  const minBalance = Math.min(...chartData.map((d) => d.balance));

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis
            dataKey="date"
            tickFormatter={(val) => {
              const d = new Date(val);
              return `${d.getDate()}/${d.getMonth() + 1}`;
            }}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={{ stroke: "#cbd5e1" }}
          />
          <YAxis
            tickFormatter={(val) => {
              if (Math.abs(val) >= 100000) return `${(val / 100000).toFixed(1)}L`;
              if (Math.abs(val) >= 1000) return `${(val / 1000).toFixed(0)}k`;
              return String(val);
            }}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={{ stroke: "#cbd5e1" }}
          />
          <Tooltip
            formatter={(val: any) => [formatCurrency(Number(val), currency), "Projected Balance"]}
            labelFormatter={(label) => formatDate(String(label))}
            contentStyle={{
              backgroundColor: "#1e293b",
              borderColor: "#334155",
              borderRadius: "0.5rem",
              color: "#f8fafc",
              fontSize: "0.75rem",
            }}
          />
          {minBalance < 0 && (
            <ReferenceLine y={0} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: "Zero Balance", fill: "#f43f5e", fontSize: 10 }} />
          )}
          <Area
            type="monotone"
            dataKey="balance"
            stroke="#4f46e5"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#balanceGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
