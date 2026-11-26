"use client";

import React, { useState, useEffect } from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import { formatPercentage } from "@/lib/formatters";

const ASSET_COLORS: Record<string, string> = {
  equity: "#06B6D4", // Electric Cyan
  debt: "#3B82F6", // Royal Blue
  mutual_fund: "#8B5CF6", // Purple
  etf: "#14B8A6", // Teal
  cash: "#10B981", // Mint Emerald
  commodities_gold: "#F59E0B", // Amber Gold
  other: "#64748B", // Slate
};

export interface AllocationSlice {
  name: string;
  value: number; // percentage or amount
  asset_class: string;
}

export function AllocationDonutChart({
  data,
  height = 280,
}: {
  data: AllocationSlice[];
  height?: number;
}) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!data || data.length === 0 || data.every((d) => d.value === 0)) {
    return (
      <div className="flex flex-col items-center justify-center h-52 text-xs text-slate-400 border border-dashed border-[#202D45] rounded-xl bg-[#0D1422]/40 p-4">
        <span className="font-semibold text-slate-300 mb-1">No Allocation Distribution</span>
        <span className="text-[11px] text-slate-400">Add active portfolio positions to compute asset-class weights</span>
      </div>
    );
  }

  if (!isMounted) {
    return (
      <div
        style={{ width: "100%", height }}
        className="flex items-center justify-center bg-[#0D1422]/40 rounded-xl animate-pulse text-xs text-slate-400"
      >
        Rendering allocation matrix...
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }} className="relative">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            innerRadius={68}
            outerRadius={95}
            paddingAngle={3}
            dataKey="value"
            nameKey="name"
            stroke="#111827"
            strokeWidth={2}
          >
            {data.map((entry, index) => {
              const key = entry.asset_class?.toLowerCase() || "other";
              const fill = ASSET_COLORS[key] || "#64748B";
              return <Cell key={`cell-${index}`} fill={fill} />;
            })}
          </Pie>
          <Tooltip
            formatter={(value: any) => [formatPercentage(Number(value)), "Allocation"]}
            contentStyle={{
              backgroundColor: "#0C121E",
              borderColor: "#22314E",
              borderRadius: "0.75rem",
              color: "#F8FAFC",
              fontSize: "0.75rem",
              boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
              padding: "8px 12px",
            }}
            itemStyle={{ color: "#38BDF8", fontWeight: 600 }}
          />
          <Legend
            iconType="circle"
            layout="horizontal"
            align="center"
            verticalAlign="bottom"
            wrapperStyle={{ fontSize: "0.75rem", paddingTop: "14px", color: "#94A3B8" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
