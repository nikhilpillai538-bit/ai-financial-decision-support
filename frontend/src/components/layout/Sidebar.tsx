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
} from "lucide-react";

export const NAVIGATION_ITEMS = [
  { name: "Overview", href: "/overview", icon: LayoutDashboard },
  { name: "Transactions", href: "/transactions", icon: Receipt },
  { name: "Cash Flow", href: "/cash-flow", icon: TrendingUp },
  { name: "Emergency Fund", href: "/emergency-fund", icon: ShieldCheck },
  { name: "Investment Goals", href: "/goals", icon: Target },
  { name: "Portfolios", href: "/portfolio", icon: Briefcase },
  { name: "MPT Optimization", href: "/optimization", icon: Sliders },
  { name: "Stress & Simulations", href: "/simulations", icon: Activity, badge: "NEW" },
  { name: "Market News", href: "/news", icon: Newspaper },
  { name: "AI Assistant", href: "/assistant", icon: Bot, badge: "AI" },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar({ className, onClose }: { className?: string; onClose?: () => void }) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex flex-col w-72 bg-slate-950 text-slate-100 border-r border-slate-800/80 shrink-0 select-none shadow-elevated z-20",
        className
      )}
    >
      {/* Brand Logo & Name */}
      <div className="h-20 flex items-center px-6 gap-3.5 border-b border-slate-800/70 bg-slate-950/80 backdrop-blur-md">
        <div className="w-11 h-11 rounded-2xl bg-linear-to-tr from-indigo-600 via-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/30 ring-1 ring-white/20">
          <Sparkles className="w-6 h-6 animate-pulse" />
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-extrabold tracking-tight text-white leading-tight">
            Financial AI
          </span>
          <span className="text-xs text-indigo-400 font-semibold tracking-wide uppercase">
            Portfolio Decision Suite
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
          Decision Platform
        </div>
        {NAVIGATION_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/overview" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={cn(
                "flex items-center justify-between px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-150 group",
                isActive
                  ? "bg-linear-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-600/25 font-bold"
                  : "text-slate-400 hover:text-white hover:bg-slate-900/90 hover:translate-x-0.5"
              )}
            >
              <div className="flex items-center gap-3.5">
                <Icon
                  className={cn(
                    "w-5 h-5 shrink-0 transition-colors",
                    isActive ? "text-white" : "text-slate-400 group-hover:text-indigo-400"
                  )}
                />
                <span className="tracking-tight">{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full font-bold uppercase tracking-wider",
                    isActive
                      ? "bg-white/20 text-white"
                      : "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Engine Status & Footer */}
      <div className="p-5 border-t border-slate-800/80 bg-slate-900/40 text-xs text-slate-400 space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-slate-300">Financial Engine</span>
          <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            Online (v11.0)
          </span>
        </div>
        <div className="text-slate-400 text-xs flex items-center gap-1">
          <Zap className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>Deterministic MPT + FinBERT Grounded</span>
        </div>
      </div>
    </aside>
  );
}
