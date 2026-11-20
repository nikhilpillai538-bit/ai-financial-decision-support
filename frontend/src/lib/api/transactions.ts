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
    return apiClient<TransactionListResponse>("/transactions", {
      method: "GET",
      params: params as any,
    });
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

    return apiClient<CSVImportResult>("/transactions/import-csv", {
      method: "POST",
      body: formData,
    });
  },
};
