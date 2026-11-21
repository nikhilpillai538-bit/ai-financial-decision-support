"use client";

import React, { useEffect, useState } from "react";
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
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!items || items.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-400">
        No drift comparison metrics available.
      </div>
    );
  }

  const chartData = items.map((it: any) => {
    const rawCurr = it.current_weight_percentage ?? it.current_weight ?? 0;
    const numCurr = typeof rawCurr === "number" ? rawCurr : parseFloat(rawCurr) || 0;
    const current = Math.abs(numCurr) <= 1 && numCurr !== 0 ? numCurr * 100 : numCurr;

    const rawTgt = it.target_weight_percentage ?? it.target_weight ?? 0;
    const numTgt = typeof rawTgt === "number" ? rawTgt : parseFloat(rawTgt) || 0;
    const target = Math.abs(numTgt) <= 1 && numTgt !== 0 ? numTgt * 100 : numTgt;

    const rawDrift = it.absolute_drift_percentage_points ?? it.drift ?? 0;
    const numDrift = typeof rawDrift === "number" ? rawDrift : parseFloat(rawDrift) || 0;
    const drift = Math.abs(numDrift) <= 1 && numDrift !== 0 ? numDrift * 100 : numDrift;

    return {
      asset_class: it.asset_class || "Asset",
      current: Number(current.toFixed(2)),
      target: Number(target.toFixed(2)),
      drift: Number(drift.toFixed(2)),
    };
  });

  if (!isMounted) {
    return (
      <div
        style={{ width: "100%", height, minHeight: height }}
        className="flex items-center justify-center bg-slate-50 rounded-lg animate-pulse text-xs text-slate-400"
      >
        Loading drift chart...
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height, minHeight: height }}>
      <ResponsiveContainer width="100%" height="100%">
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
