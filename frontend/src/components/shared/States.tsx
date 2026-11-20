import React from "react";
import { AlertCircle, AlertTriangle, Inbox, Loader2 } from "lucide-react";
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
        "flex flex-col items-center justify-center p-12 text-center text-slate-500 dark:text-slate-400",
        className
      )}
    >
      <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mb-3" />
      <p className="text-sm font-medium">{message}</p>
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
        "flex flex-col items-center justify-center p-10 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-900/50",
        className
      )}
    >
      <div className="p-3 bg-white dark:bg-slate-800 rounded-full shadow-xs mb-3 text-slate-400">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h4>
      <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mt-1 mb-4">{description}</p>
      {action && <div>{action}</div>}
      {!action && actionLabel && (
        <button
          onClick={onAction}
          className="inline-flex items-center justify-center px-4 py-2 text-xs font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
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
        "p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-900 dark:bg-rose-950/40 dark:border-rose-800 dark:text-rose-200 flex items-start justify-between gap-3",
        className
      )}
    >
      <div className="flex items-start gap-3 flex-1">
        <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
        <div className="flex-1 text-xs">
          <strong className="font-semibold block">{title}</strong>
          <p className="mt-0.5 opacity-90">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 underline font-medium hover:text-rose-800 dark:hover:text-rose-100 transition-colors"
            >
              Retry request
            </button>
          )}
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-rose-700 hover:text-rose-900 font-bold p-1 text-xs"
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
        "p-3 rounded-lg border border-amber-200 bg-amber-50 text-amber-900 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-200 flex items-center gap-2.5 text-xs",
        className
      )}
    >
      <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
      <span>{message}</span>
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
        "p-5 rounded-2xl bg-slate-50/70 dark:bg-slate-900/60 border border-slate-200/90 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 leading-relaxed font-medium",
        className
      )}
    >
      <span className="font-bold uppercase tracking-wider text-xs text-slate-700 dark:text-slate-300 block mb-1">
        Regulatory Disclaimer
      </span>
      {text}
    </div>
  );
}
