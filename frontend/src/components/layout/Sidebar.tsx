"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Receipt,
  TrendingUp,
  ShieldCheck,
  Target,
  Briefcase,
  Sliders,
  Activity,
  Newspaper,
  Bot,
  Settings,
  Sparkles,
  Zap,
  ChevronRight,
} from "lucide-react";

export interface NavGroup {
  label: string;
  items: Array<{
    name: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string;
    badgeVariant?: "cyan" | "emerald" | "amber";
  }>;
}

export const NAVIGATION_GROUPS: NavGroup[] = [
  {
    label: "Executive & Cash Flow",
    items: [
      { name: "Overview", href: "/overview", icon: LayoutDashboard },
      { name: "Transactions Ledger", href: "/transactions", icon: Receipt },
      { name: "Cash Flow Forecast", href: "/cash-flow", icon: TrendingUp },
      { name: "Emergency Runway", href: "/emergency-fund", icon: ShieldCheck },
    ],
  },
  {
    label: "Portfolio & Quantitative Risk",
    items: [
      { name: "Portfolios & Holdings", href: "/portfolio", icon: Briefcase },
      { name: "MPT Optimization", href: "/optimization", icon: Sliders },
      { name: "Stress & Monte Carlo", href: "/simulations", icon: Activity, badge: "PRO", badgeVariant: "emerald" },
      { name: "Financial Goals & SIP", href: "/goals", icon: Target },
    ],
  },
  {
    label: "Intelligence & Platform",
    items: [
      { name: "FinBERT Market News", href: "/news", icon: Newspaper },
      { name: "Financial AI Assistant", href: "/assistant", icon: Bot, badge: "AI", badgeVariant: "cyan" },
      { name: "Settings & Security", href: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar({ className, onClose }: { className?: string; onClose?: () => void }) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex flex-col w-72 bg-[#0A0F1A] text-slate-200 border-r border-[#1B273E] shrink-0 select-none shadow-2xl z-20 transition-all",
        className
      )}
    >
      {/* Brand Logo & Name */}
      <div className="h-20 flex items-center px-6 gap-3.5 border-b border-[#1B273E] bg-[#0A0F1A]/90 backdrop-blur-md">
        <div className="relative w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-500 via-teal-500 to-emerald-500 flex items-center justify-center text-slate-950 shadow-md shadow-cyan-500/25 ring-1 ring-white/30">
          <Sparkles className="w-6 h-6 animate-pulse" />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#0A0F1A]" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-base font-extrabold tracking-tight text-white leading-tight">
              FINANCIAL<span className="text-cyan-400">AI</span>
            </span>
            <span className="px-1.5 py-0.2 text-[9px] font-bold rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/80">
              v11.0
            </span>
          </div>
          <span className="text-[11px] text-slate-400 font-medium tracking-wider uppercase mt-0.5">
            Command Center
          </span>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 px-3.5 py-5 space-y-6 overflow-y-auto">
        {NAVIGATION_GROUPS.map((group, gIdx) => (
          <div key={gIdx} className="space-y-1">
            <div className="px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              {group.label}
            </div>
            {group.items.map((item) => {
              const isActive =
                pathname === item.href || (item.href !== "/overview" && pathname.startsWith(item.href));
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 group relative",
                    isActive
                      ? "bg-gradient-to-r from-cyan-500/15 via-teal-500/10 to-transparent text-cyan-300 font-bold border-l-2 border-cyan-400 shadow-sm"
                      : "text-slate-400 hover:text-slate-100 hover:bg-[#141D2E] hover:translate-x-0.5"
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon
                      className={cn(
                        "w-4 h-4 shrink-0 transition-colors",
                        isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-cyan-400"
                      )}
                    />
                    <span className="truncate">{item.name}</span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    {item.badge && (
                      <span
                        className={cn(
                          "text-[10px] px-2 py-0.5 rounded-full font-extrabold uppercase tracking-wider border",
                          item.badgeVariant === "emerald"
                            ? "bg-emerald-950/80 text-emerald-400 border-emerald-800/80"
                            : "bg-cyan-950/80 text-cyan-300 border-cyan-800/80"
                        )}
                      >
                        {item.badge}
                      </span>
                    )}
                    {isActive && <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />}
                  </div>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Engine Status & Telemetry Footer */}
      <div className="p-4 border-t border-[#1B273E] bg-[#0C121F]/80 text-[11px] text-slate-400 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-semibold text-slate-300 text-[11px]">System Engine</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase">
            Grounded Active
          </span>
        </div>
        <div className="text-slate-400 text-[10px] flex items-center gap-1.5 pt-0.5">
          <Zap className="w-3 h-3 text-cyan-400 shrink-0" />
          <span className="truncate">Deterministic MPT + FinBERT Ingest</span>
        </div>
      </div>
    </aside>
  );
}
