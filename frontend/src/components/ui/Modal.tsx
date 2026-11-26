"use client";

import React, { useEffect } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl";
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = "md",
}: ModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidths = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        className={cn(
          "relative w-full bg-[#111827] rounded-2xl shadow-2xl border border-[#202D45] p-5 sm:p-6 z-10 animate-slide-up",
          maxWidths[maxWidth]
        )}
      >
        <div className="flex items-start justify-between pb-4 border-b border-[#1C273C]">
          <div>
            <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
              {title}
            </h3>
            {description && (
              <p className="text-xs text-slate-400 mt-1">
                {description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white rounded-lg p-1.5 hover:bg-slate-800/80 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="pt-4">{children}</div>
      </div>
    </div>
  );
}
