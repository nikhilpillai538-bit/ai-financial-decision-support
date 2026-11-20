/**
 * Formatting utilities for financial currency, percentages, ratios, and dates.
 * Strictly avoids converting null/missing metrics into "0" or "₹0.00".
 */

export function formatCurrency(
  value: string | number | null | undefined,
  currency: string = "INR",
  options?: { showPlusSign?: boolean; decimals?: number }
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) {
    return "—";
  }

  const decimals = options?.decimals !== undefined ? options.decimals : 2;
  const isPositive = num > 0;
  const absNum = Math.abs(num);

  let formatted = "";
  const upperCurrency = (currency || "INR").toUpperCase();

  try {
    if (upperCurrency === "INR") {
      formatted = new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(absNum);
    } else {
      formatted = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: upperCurrency,
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(absNum);
    }
  } catch {
    // Fallback if currency code is unusual
    formatted = `${upperCurrency} ${absNum.toFixed(decimals)}`;
  }

  if (num < 0) {
    return `-${formatted}`;
  }
  if (options?.showPlusSign && isPositive) {
    return `+${formatted}`;
  }
  return formatted;
}

export function formatPercentage(
  value: string | number | null | undefined,
  optionsOrDecimals?: { showPlusSign?: boolean; decimals?: number; isRatio?: boolean } | number,
  legacyShowPlusSign?: boolean
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  let num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) {
    return "—";
  }

  let decimals = 2;
  let showPlusSign = false;
  let isRatio: boolean | undefined = undefined;

  if (typeof optionsOrDecimals === "number") {
    decimals = optionsOrDecimals;
    if (legacyShowPlusSign !== undefined) {
      showPlusSign = legacyShowPlusSign;
    }
  } else if (typeof optionsOrDecimals === "object") {
    if (optionsOrDecimals.decimals !== undefined) decimals = optionsOrDecimals.decimals;
    if (optionsOrDecimals.showPlusSign !== undefined) showPlusSign = optionsOrDecimals.showPlusSign;
    if (optionsOrDecimals.isRatio !== undefined) isRatio = optionsOrDecimals.isRatio;
  }

  // If isRatio is explicitly true, or if undefined and magnitude is <= 1.0 (and non-zero), scale by 100
  if (isRatio === true || (isRatio === undefined && Math.abs(num) > 0 && Math.abs(num) <= 1.0)) {
    num = num * 100;
  }

  const formatted = `${Math.abs(num).toFixed(decimals)}%`;

  if (num < 0) {
    return `-${formatted}`;
  }
  if (showPlusSign && num > 0) {
    return `+${formatted}`;
  }
  return formatted;
}

export function formatDate(
  dateStr: string | null | undefined,
  options?: { includeTime?: boolean }
): string {
  if (!dateStr) return "—";

  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return "—";

    if (options?.includeTime) {
      return d.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "—";
  }
}

export function formatNumber(
  value: string | number | null | undefined,
  decimals?: number
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) {
    return "—";
  }

  const minDecimals = decimals !== undefined ? decimals : (Number.isInteger(num) ? 0 : 2);
  const maxDecimals = decimals !== undefined ? decimals : 2;

  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: minDecimals,
    maximumFractionDigits: maxDecimals,
  }).format(num);
}
