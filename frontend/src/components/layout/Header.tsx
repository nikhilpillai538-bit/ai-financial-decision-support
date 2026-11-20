"use client";

import React from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import { LogOut, Menu, User as UserIcon, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function Header({ onMenuClick }: { onMenuClick?: () => void }) {
  const { user, logout } = useAuth();

  return (
    <header className="h-20 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 px-6 md:px-10 flex items-center justify-between shrink-0 sticky top-0 z-10 shadow-xs">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="md:hidden p-2.5 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-6 h-6" />
        </button>
        <div className="hidden sm:flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Personal Financial Decision Support & Modern Portfolio Analytics</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {user ? (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 bg-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-500/20">
                {user.email ? user.email.charAt(0).toUpperCase() : <UserIcon className="w-5 h-5" />}
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100 max-w-[200px] truncate leading-tight">
                  {user.email}
                </span>
                <span className="text-xs font-medium text-emerald-600">
                  Authenticated Identity
                </span>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="text-slate-700 hover:text-rose-600 hover:border-rose-300 hover:bg-rose-50 text-xs font-semibold gap-2 py-2 px-3.5"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden md:inline-block">Sign out</span>
            </Button>
          </div>
        ) : (
          <div className="text-sm text-slate-400 font-medium">Not authenticated</div>
        )}
      </div>
    </header>
  );
}
