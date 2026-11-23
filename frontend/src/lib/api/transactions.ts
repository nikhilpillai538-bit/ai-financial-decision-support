import { apiClient } from "./client";
import {
  CSVImportResult,
  FinancialSummary,
  Transaction,
  TransactionListResponse,
  TransactionType,
} from "@/types";

export interface TransactionFilterParams {
  category?: string;
  start_date?: string;
  end_date?: string;
  min_amount?: string | number;
  max_amount?: string | number;
  limit?: number;
  offset?: number;
}

export interface CreateTransactionPayload {
  date: string;
  amount: string;
  transaction_type: TransactionType;
  category: string;
  description: string;
}

export const transactionsApi = {
  async listTransactions(params: TransactionFilterParams = {}): Promise<TransactionListResponse> {
    const raw = await apiClient<any>("/transactions", {
      method: "GET",
      params: params as any,
    });

    const items: Transaction[] = Array.isArray(raw)
      ? raw
      : Array.isArray(raw?.items)
      ? raw.items
      : [];

    return {
      items,
      total_count: Array.isArray(raw) ? raw.length : (raw?.total_count ?? items.length),
      limit: raw?.limit ?? (params.limit || items.length),
      offset: raw?.offset ?? (params.offset || 0),
    };
  },

  async createTransaction(payload: CreateTransactionPayload): Promise<Transaction> {
    return apiClient<Transaction>("/transactions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getTransaction(id: string): Promise<Transaction> {
    return apiClient<Transaction>(`/transactions/${id}`);
  },

  async deleteTransaction(id: string): Promise<void> {
    await apiClient(`/transactions/${id}`, {
      method: "DELETE",
    });
  },

  async getFinancialSummary(): Promise<FinancialSummary> {
    return apiClient<FinancialSummary>("/transactions/summary");
  },

  async importCSV(file: File): Promise<CSVImportResult> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await apiClient<any>("/transactions/import-csv", {
      method: "POST",
      body: formData,
    });

    const errorStrings: string[] = Array.isArray(res?.errors)
      ? res.errors.map((e: any) =>
          typeof e === "string" ? e : `Row ${e?.row ?? "?"}: ${e?.reason ?? "Unknown error"}`
        )
      : [];

    return {
      total_rows: res?.total_rows ?? 0,
      imported_count: res?.imported ?? res?.imported_count ?? 0,
      duplicate_count: res?.duplicates_skipped ?? res?.duplicate_count ?? 0,
      skipped_count: res?.rejected ?? res?.skipped_count ?? 0,
      errors: errorStrings,
    };
  },
};
