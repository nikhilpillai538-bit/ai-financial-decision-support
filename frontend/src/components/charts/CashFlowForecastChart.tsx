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
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-xs text-slate-400 border border-dashed border-[#202D45] rounded-xl bg-[#0D1422]/40 p-4">
        <span className="font-semibold text-slate-300 mb-1">No Forecast Timeline Data</span>
        <span className="text-[11px] text-slate-400">Generate a cash-flow projection to model liquidity balance</span>
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

  if (!isMounted) {
    return (
      <div
        style={{ width: "100%", height }}
        className="flex items-center justify-center bg-[#0D1422]/40 rounded-xl animate-pulse text-xs text-slate-400"
      >
        Projecting liquidity curve...
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1C283F" />
          <XAxis
            dataKey="date"
            tickFormatter={(val) => {
              const d = new Date(val);
              return `${d.getDate()}/${d.getMonth() + 1}`;
            }}
            tick={{ fontSize: 11, fill: "#64748B" }}
            axisLine={{ stroke: "#24334F" }}
          />
          <YAxis
            tickFormatter={(val) => {
              if (Math.abs(val) >= 10000000) return `${(val / 10000000).toFixed(1)}Cr`;
              if (Math.abs(val) >= 100000) return `${(val / 100000).toFixed(1)}L`;
              if (Math.abs(val) >= 1000) return `${(val / 1000).toFixed(0)}k`;
              return String(val);
            }}
            tick={{ fontSize: 11, fill: "#64748B" }}
            axisLine={{ stroke: "#24334F" }}
          />
          <Tooltip
            formatter={(val: any) => [formatCurrency(Number(val), currency), "Projected Balance"]}
            labelFormatter={(label) => formatDate(String(label))}
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
          {minBalance < 0 && (
            <ReferenceLine
              y={0}
              stroke="#F43F5E"
              strokeDasharray="4 4"
              label={{ value: "Zero Balance Threshold", fill: "#F43F5E", fontSize: 10, position: "top" }}
            />
          )}
          <Area
            type="monotone"
            dataKey="balance"
            stroke="#06B6D4"
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#balanceGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
