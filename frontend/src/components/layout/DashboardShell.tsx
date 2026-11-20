"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { LoadingState } from "@/components/shared/States";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <LoadingState message="Verifying secure session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden font-sans antialiased text-slate-900 dark:text-slate-100">
      {/* Desktop Sidebar */}
      <Sidebar className="hidden md:flex" />

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs"
            onClick={() => setMobileMenuOpen(false)}
          />
          <Sidebar className="relative z-10 w-72" onClose={() => setMobileMenuOpen(false)} />
        </div>
      )}

      {/* Main App Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header onMenuClick={() => setMobileMenuOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-10 bg-slate-50/60 dark:bg-slate-950/60">
          <div className="max-w-7xl mx-auto space-y-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
