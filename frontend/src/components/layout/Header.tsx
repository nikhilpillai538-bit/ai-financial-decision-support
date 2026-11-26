"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import { LogOut, Menu, User as UserIcon, ShieldCheck, Activity, Clock } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function Header({ onMenuClick }: { onMenuClick?: () => void }) {
  const { user, logout } = useAuth();
  const [currentTime, setCurrentTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        }) + " UTC"
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 md:h-20 bg-[#0A0F1A]/95 backdrop-blur-md border-b border-[#1B273E] px-4 md:px-8 flex items-center justify-between shrink-0 sticky top-0 z-10 shadow-sm transition-all">
      {/* Left side: Mobile Toggle & System Context */}
      <div className="flex items-center gap-3.5">
        <button
          onClick={onMenuClick}
          className="md:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/40 border border-cyan-800/50 text-cyan-300 text-xs font-semibold">
            <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>Fintech AI Command Center</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 font-medium border-l border-slate-800 pl-3">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="truncate">Deterministic Analytics · Non-Custodial</span>
          </div>
        </div>
      </div>

      {/* Right side: Telemetry & Authenticated User Profile */}
      <div className="flex items-center gap-3 sm:gap-5">
        {currentTime && (
          <div className="hidden xl:flex items-center gap-1.5 text-xs text-slate-400 font-mono bg-[#0D1422] px-2.5 py-1 rounded-lg border border-slate-800">
            <Clock className="w-3 h-3 text-cyan-400" />
            <span>{currentTime}</span>
          </div>
        )}

        {user ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5 bg-[#0F1728] border border-[#21304A] py-1 px-2.5 sm:py-1.5 sm:px-3 rounded-xl shadow-xs">
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-teal-500 text-slate-950 font-bold text-xs sm:text-sm flex items-center justify-center shadow-xs">
                {user.email ? user.email.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
              </div>
              <div className="hidden md:flex flex-col text-left">
                <span className="text-xs font-bold text-slate-100 max-w-[170px] truncate leading-tight">
                  {user.email}
                </span>
                <span className="text-[10px] font-semibold text-emerald-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  Verified Identity
                </span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="border-slate-800 text-slate-300 hover:text-rose-400 hover:border-rose-900/60 hover:bg-rose-950/30 text-xs font-medium gap-1.5 py-1.5 px-3 rounded-xl transition-all"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline-block">Sign out</span>
            </Button>
          </div>
        ) : (
          <div className="text-xs text-slate-400 font-medium">Session Terminated</div>
        )}
      </div>
    </header>
  );
}
