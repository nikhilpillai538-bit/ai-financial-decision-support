"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { PortfolioDriftItem } from "@/types";
import { formatPercentage } from "@/lib/formatters";

export function DriftComparisonBarChart({
  items,
  height = 260,
}: {
  items: PortfolioDriftItem[];
  height?: number;
}) {
  if (!items || items.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-400">
        No drift comparison metrics available.
      </div>
    );
  }

  const chartData = items.map((it) => ({
    asset_class: it.asset_class,
    current: (parseFloat(it.current_weight) || 0) * 100,
    target: (parseFloat(it.target_weight) || 0) * 100,
    drift: (parseFloat(it.drift) || 0) * 100,
  }));

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis dataKey="asset_class" tick={{ fontSize: 11, fill: "#64748b" }} />
          <YAxis
            tickFormatter={(val) => `${val}%`}
            tick={{ fontSize: 11, fill: "#64748b" }}
          />
          <Tooltip
            formatter={(val: any, name: any) => [
              formatPercentage(Number(val)),
              name === "current" ? "Current Weight" : "Target Weight",
            ]}
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
          <Bar dataKey="current" name="Current %" fill="#4f46e5" radius={[4, 4, 0, 0]} />
          <Bar dataKey="target" name="Target %" fill="#94a3b8" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
