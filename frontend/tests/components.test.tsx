import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricCard } from "../src/components/shared/MetricCard";
import { Badge } from "../src/components/ui/Badge";
import { Button } from "../src/components/ui/Button";
import { EmptyState, ErrorBanner } from "../src/components/shared/States";

describe("Shared UI Components", () => {
  describe("MetricCard", () => {
    it("renders title, value, subtitle, and trend badge", () => {
      render(
        <MetricCard
          title="Total Net Worth"
          value="₹12,50,000"
          subtitle="All asset classes"
          trend={{ value: "+8.5%", isPositive: true }}
        />
      );

      expect(screen.getByText("Total Net Worth")).toBeInTheDocument();
      expect(screen.getByText("₹12,50,000")).toBeInTheDocument();
      expect(screen.getByText("All asset classes")).toBeInTheDocument();
      expect(screen.getByText("+8.5%")).toBeInTheDocument();
    });

    it("renders missing values (—) without breaking", () => {
      render(<MetricCard title="Missing Metric" value="—" />);
      expect(screen.getByText("Missing Metric")).toBeInTheDocument();
      expect(screen.getByText("—")).toBeInTheDocument();
    });
  });

  describe("Badge", () => {
    it("renders variant styles correctly", () => {
      const { rerender } = render(<Badge variant="success">Completed</Badge>);
      expect(screen.getByText("Completed")).toBeInTheDocument();
      expect(screen.getByText("Completed")).toHaveClass("text-emerald-700");

      rerender(<Badge variant="danger">Failed</Badge>);
      expect(screen.getByText("Failed")).toHaveClass("text-rose-700");

      rerender(<Badge variant="warning">Pending</Badge>);
      expect(screen.getByText("Pending")).toHaveClass("text-amber-700");
    });
  });

  describe("Button", () => {
    it("renders loading state spinner and disables button", () => {
      render(
        <Button isLoading disabled>
          Submit Transaction
        </Button>
      );
      const btn = screen.getByRole("button");
      expect(btn).toBeDisabled();
      expect(btn.querySelector(".animate-spin")).toBeInTheDocument();
    });
  });

  describe("States", () => {
    it("renders EmptyState with title, description, and action button", () => {
      render(
        <EmptyState
          title="No Transactions Found"
          description="You have not imported any bank statements yet."
          actionLabel="Import CSV"
          onAction={() => {}}
        />
      );
      expect(screen.getByText("No Transactions Found")).toBeInTheDocument();
      expect(screen.getByText("You have not imported any bank statements yet.")).toBeInTheDocument();
      expect(screen.getByText("Import CSV")).toBeInTheDocument();
    });

    it("renders ErrorBanner with alert message", () => {
      render(<ErrorBanner message="Database connection timeout" />);
      expect(screen.getByText("Database connection timeout")).toBeInTheDocument();
    });
  });
});
