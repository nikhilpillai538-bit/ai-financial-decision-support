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
      <div className="min-h-screen flex items-center justify-center bg-[#090D16]">
        <LoadingState message="Establishing secure fintech cryptographic session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen bg-[#090D16] text-slate-100 overflow-hidden font-sans antialiased relative">
      {/* Background subtle radial gradient */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-600/5 rounded-full blur-3xl pointer-events-none -z-0" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-teal-600/5 rounded-full blur-3xl pointer-events-none -z-0" />

      {/* Desktop Sidebar */}
      <Sidebar className="hidden md:flex" />

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex animate-fade-in">
          <div
            className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />
          <Sidebar
            className="relative z-10 w-72 animate-slide-up"
            onClose={() => setMobileMenuOpen(false)}
          />
        </div>
      )}

      {/* Main App Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden z-10">
        <Header onMenuClick={() => setMobileMenuOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-[#090D16]/95">
          <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8 animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
