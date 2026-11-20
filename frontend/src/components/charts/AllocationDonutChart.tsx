"use client";

import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import { formatPercentage } from "@/lib/formatters";

const ASSET_COLORS: Record<string, string> = {
  equity: "#4f46e5", // Indigo
  debt: "#0ea5e9", // Sky
  mutual_fund: "#8b5cf6", // Purple
  etf: "#06b6d4", // Cyan
  cash: "#10b981", // Emerald
  commodities_gold: "#f59e0b", // Amber
  other: "#64748b", // Slate
};

export interface AllocationSlice {
  name: string;
  value: number; // percentage or amount
  asset_class: string;
}

export function AllocationDonutChart({
  data,
  height = 260,
}: {
  data: AllocationSlice[];
  height?: number;
}) {
  if (!data || data.length === 0 || data.every((d) => d.value === 0)) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-400">
        No asset allocation data recorded yet.
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            innerRadius={60}
            outerRadius={85}
            paddingAngle={3}
            dataKey="value"
            nameKey="name"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={ASSET_COLORS[entry.asset_class.toLowerCase()] || "#64748b"}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: any) => [formatPercentage(Number(value)), "Allocation"]}
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
            layout="horizontal"
            align="center"
            verticalAlign="bottom"
            wrapperStyle={{ fontSize: "0.75rem", paddingTop: "12px" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
