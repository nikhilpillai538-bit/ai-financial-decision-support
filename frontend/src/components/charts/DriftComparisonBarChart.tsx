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
      <div className="flex flex-col items-center justify-center h-48 text-xs text-slate-400 border border-dashed border-[#202D45] rounded-xl bg-[#0D1422]/40 p-4">
        <span className="font-semibold text-slate-300 mb-1">No Drift Metrics Available</span>
        <span className="text-[11px] text-slate-400">Configure target weights and holdings to evaluate portfolio drift</span>
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
        className="flex items-center justify-center bg-[#0D1422]/40 rounded-xl animate-pulse text-xs text-slate-400"
      >
        Calculating target variance...
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height, minHeight: height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1C283F" />
          <XAxis dataKey="asset_class" tick={{ fontSize: 11, fill: "#64748B" }} axisLine={{ stroke: "#24334F" }} />
          <YAxis
            tickFormatter={(val) => `${val}%`}
            tick={{ fontSize: 11, fill: "#64748B" }}
            axisLine={{ stroke: "#24334F" }}
          />
          <Tooltip
            formatter={(val: any, name: any) => [
              formatPercentage(Number(val)),
              name === "current" ? "Current Weight" : "Target Weight",
            ]}
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
          <Bar dataKey="current" name="Current %" fill="#06B6D4" radius={[4, 4, 0, 0]} />
          <Bar dataKey="target" name="Target %" fill="#475569" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
