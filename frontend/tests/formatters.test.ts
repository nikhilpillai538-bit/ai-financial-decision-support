import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatPercentage,
  formatDate,
  formatNumber,
} from "../src/lib/formatters";

describe("Financial Formatters", () => {
  describe("formatCurrency", () => {
    it("formats INR currency correctly with ₹ symbol", () => {
      const res = formatCurrency(100000, "INR");
      expect(res).toContain("₹");
      expect(res).toContain("1,00,000");
    });

    it("formats USD currency correctly with $ symbol", () => {
      const res = formatCurrency(1250.5, "USD");
      expect(res).toContain("$");
      expect(res).toContain("1,250.50");
    });

    it("handles string numeric inputs safely", () => {
      const res = formatCurrency("4500.75", "INR");
      expect(res).toContain("₹");
      expect(res).toContain("4,500.75");
    });

    it("strictly returns em dash (—) for null, undefined, empty, or NaN values", () => {
      expect(formatCurrency(null)).toBe("—");
      expect(formatCurrency(undefined)).toBe("—");
      expect(formatCurrency("")).toBe("—");
      expect(formatCurrency("abc")).toBe("—");
    });

    it("formats 0 as ₹0.00 without emitting em dash", () => {
      const res = formatCurrency(0, "INR");
      expect(res).toContain("₹");
      expect(res).toContain("0.00");
    });
  });

  describe("formatPercentage", () => {
    it("formats decimal ratio as percentage", () => {
      expect(formatPercentage(0.125)).toBe("12.50%");
      expect(formatPercentage("0.0825")).toBe("8.25%");
    });

    it("supports optional plus sign prefix", () => {
      expect(formatPercentage(0.05, 2, true)).toBe("+5.00%");
      expect(formatPercentage(-0.03, 2, true)).toBe("-3.00%");
    });

    it("strictly returns em dash (—) for missing percentage values", () => {
      expect(formatPercentage(null)).toBe("—");
      expect(formatPercentage(undefined)).toBe("—");
      expect(formatPercentage("")).toBe("—");
      expect(formatPercentage("invalid")).toBe("—");
    });
  });

  describe("formatDate", () => {
    it("formats standard ISO date string to readable format", () => {
      const formatted = formatDate("2026-10-22T10:00:00Z");
      expect(formatted).toContain("2026");
      expect(formatted).toContain("Oct");
      expect(formatted).toContain("22");
    });

    it("returns em dash for null or invalid dates", () => {
      expect(formatDate(null)).toBe("—");
      expect(formatDate(undefined)).toBe("—");
      expect(formatDate("not-a-date")).toBe("—");
    });
  });

  describe("formatNumber", () => {
    it("formats integers and decimals with comma separators", () => {
      expect(formatNumber(1234567)).toBe("1,234,567");
      expect(formatNumber("98765.432", 2)).toBe("98,765.43");
    });

    it("returns em dash for null or missing numeric values", () => {
      expect(formatNumber(null)).toBe("—");
      expect(formatNumber(undefined)).toBe("—");
      expect(formatNumber("bad-number")).toBe("—");
    });
  });
});
