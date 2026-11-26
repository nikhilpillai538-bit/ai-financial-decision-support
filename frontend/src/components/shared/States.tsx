import React from "react";
import { AlertCircle, AlertTriangle, Inbox, Loader2, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

export function LoadingState({
  message = "Loading financial data...",
  className,
}: {
  message?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-12 text-center text-slate-400 animate-fade-in",
        className
      )}
    >
      <div className="relative mb-3.5">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <div className="absolute inset-0 rounded-full blur-md bg-cyan-500/20" />
      </div>
      <p className="text-xs sm:text-sm font-semibold tracking-wide text-slate-300">{message}</p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  actionLabel,
  onAction,
  icon,
  className,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center border border-dashed border-[#23324C] rounded-2xl bg-[#0D1422]/60",
        className
      )}
    >
      <div className="p-3.5 bg-[#141C2E] border border-[#23324C] rounded-2xl shadow-sm mb-3.5 text-cyan-400">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-sm sm:text-base font-bold text-white">{title}</h4>
      <p className="text-xs text-slate-400 max-w-sm mt-1 mb-5 leading-relaxed">{description}</p>
      {action && <div>{action}</div>}
      {!action && actionLabel && (
        <button
          onClick={onAction}
          className="inline-flex items-center justify-center px-4 py-2 text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-400 to-teal-400 rounded-xl hover:from-cyan-300 hover:to-teal-300 transition-all shadow-md shadow-cyan-950/40"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export function ErrorBanner({
  title = "Error loading data",
  message,
  onRetry,
  onDismiss,
  className,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "p-4 rounded-xl border border-rose-800/80 bg-rose-950/40 text-rose-200 flex items-start justify-between gap-3 shadow-sm animate-fade-in",
        className
      )}
    >
      <div className="flex items-start gap-3 flex-1">
        <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div className="flex-1 text-xs">
          <strong className="font-bold block text-white">{title}</strong>
          <p className="mt-0.5 opacity-90 leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 inline-flex items-center gap-1 font-bold text-rose-300 hover:text-white underline transition-colors"
            >
              Retry request
            </button>
          )}
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-rose-400 hover:text-white font-bold p-1 text-xs rounded transition-colors"
          aria-label="Dismiss"
        >
          ✕
        </button>
      )}
    </div>
  );
}

export function WarningBanner({
  message,
  className,
}: {
  message: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "p-3.5 rounded-xl border border-amber-800/70 bg-amber-950/40 text-amber-200 flex items-center gap-2.5 text-xs shadow-sm",
        className
      )}
    >
      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
      <span className="font-medium leading-relaxed">{message}</span>
    </div>
  );
}

export function RegulatoryDisclaimer({
  text = "Decision-support only: The financial analytics, projections, optimization algorithms, and AI responses provided by this platform are for informational and educational purposes only. They do not constitute fiduciary financial advice, investment recommendations, or automated trading instructions.",
  className,
}: {
  text?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "p-4 sm:p-5 rounded-2xl bg-[#0B101A] border border-[#1A263D] text-[11px] sm:text-xs text-slate-400 leading-relaxed font-normal shadow-xs",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-1.5 text-slate-300 font-bold uppercase tracking-wider text-[10px]">
        <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
        <span>Regulatory & Analytical Disclaimer</span>
      </div>
      {text}
    </div>
  );
}
