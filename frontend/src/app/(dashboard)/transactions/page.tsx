"use client";

import React, { useEffect, useState } from "react";
import {
  Plus,
  Upload,
  Search,
  Trash2,
  Receipt,
  CheckCircle2,
  Filter,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { LoadingState, EmptyState, ErrorBanner } from "@/components/shared/States";
import { formatCurrency, formatDate } from "@/lib/formatters";
import { transactionsApi } from "@/lib/api/transactions";
import { CSVImportResult, Transaction, TransactionType } from "@/types";

export default function TransactionsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // Add Transaction Form State
  const [txDate, setTxDate] = useState(new Date().toISOString().split("T")[0]);
  const [txAmount, setTxAmount] = useState("");
  const [txType, setTxType] = useState<TransactionType>("expense");
  const [txCategory, setTxCategory] = useState("Dining & Food");
  const [txDescription, setTxDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // CSV Import State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<CSVImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const CATEGORIES = [
    "Dining & Food",
    "Groceries",
    "Housing & Rent",
    "Utilities",
    "Transportation",
    "Healthcare & Medical",
    "Shopping & Retail",
    "Entertainment",
    "Salary & Income",
    "Investments & Savings",
    "Other",
  ];

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await transactionsApi.listTransactions({
        category: selectedCategory || undefined,
        limit: 50,
      });
      setTransactions(res.items || []);
      setTotalCount(res.total_count || 0);
    } catch (err: any) {
      setError(err?.message || "Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [selectedCategory]);

  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!txAmount || !txDescription) return;

    setIsSubmitting(true);
    try {
      await transactionsApi.createTransaction({
        date: txDate,
        amount: txAmount,
        transaction_type: txType,
        category: txCategory,
        description: txDescription,
      });
      setIsAddModalOpen(false);
      setTxAmount("");
      setTxDescription("");
      await fetchTransactions();
    } catch (err: any) {
      alert(`Error creating transaction: ${err?.detail || err?.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteTransaction = async (id: string) => {
    if (!confirm("Are you sure you want to delete this transaction record?")) return;
    try {
      await transactionsApi.deleteTransaction(id);
      await fetchTransactions();
    } catch (err: any) {
      alert(`Error deleting transaction: ${err?.detail || err?.message}`);
    }
  };

  const handleImportCSV = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsImporting(true);
    setImportError(null);
    setImportResult(null);

    try {
      const res = await transactionsApi.importCSV(selectedFile);
      setImportResult(res);
      setSelectedFile(null);
      await fetchTransactions();
    } catch (err: any) {
      setImportError(err?.detail || err?.message || "Failed to import CSV file.");
    } finally {
      setIsImporting(false);
    }
  };

  const filteredTransactions = transactions.filter((t) => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      t.description.toLowerCase().includes(term) ||
      t.category.toLowerCase().includes(term) ||
      t.amount.includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Transactions Ledger
          </h1>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
            Log financial activities, categorize transactions, and import statements
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="md"
            onClick={() => setIsImportModalOpen(true)}
            className="gap-2 shadow-xs"
          >
            <Upload className="w-4 h-4" />
            <span>Import CSV</span>
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() => setIsAddModalOpen(true)}
            className="gap-2 shadow-md shadow-indigo-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Transaction</span>
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchTransactions} />}

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-5">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <div className="relative flex-1 w-full">
              <Search className="w-5 h-5 absolute left-4 top-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by description, category, or amount..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-2.5 text-sm md:text-base bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all text-slate-900 dark:text-slate-100 placeholder:text-slate-400"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="w-5 h-5 text-slate-400 shrink-0" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-4 py-2.5 text-sm md:text-base bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 w-full sm:w-56 text-slate-700 dark:text-slate-200 font-medium"
              >
                <option value="">All Categories</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardHeader className="py-5 px-6 flex flex-row items-center justify-between border-b border-slate-100 dark:border-slate-800">
          <div>
            <CardTitle className="text-base md:text-lg">Transaction Ledger</CardTitle>
            <CardDescription className="text-sm">
              Showing {filteredTransactions.length} of {totalCount} verified records
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <LoadingState message="Fetching transaction ledger..." />
          ) : filteredTransactions.length === 0 ? (
            <EmptyState
              title="No transactions found"
              description="No transaction records match the selected filter. Add a transaction or import a statement."
              icon={<Receipt className="w-8 h-8" />}
              action={
                <Button variant="primary" size="md" onClick={() => setIsAddModalOpen(true)}>
                  Add First Transaction
                </Button>
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50/80 dark:bg-slate-800/60 text-slate-500 uppercase tracking-wider text-xs font-bold border-y border-slate-100 dark:border-slate-800">
                  <tr>
                    <th className="py-4 px-6">Date</th>
                    <th className="py-4 px-6">Description</th>
                    <th className="py-4 px-6">Category</th>
                    <th className="py-4 px-6 text-center">Type</th>
                    <th className="py-4 px-6 text-right">Amount</th>
                    <th className="py-4 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {filteredTransactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-4 px-6 text-slate-500 font-medium whitespace-nowrap">
                        {formatDate(tx.date)}
                      </td>
                      <td className="py-4 px-6 font-semibold text-slate-900 dark:text-slate-100 max-w-sm truncate">
                        {tx.description}
                      </td>
                      <td className="py-4 px-6">
                        <Badge variant="default">{tx.category}</Badge>
                      </td>
                      <td className="py-4 px-6 text-center">
                        <Badge variant={tx.transaction_type === "income" ? "success" : "default"}>
                          {tx.transaction_type.toUpperCase()}
                        </Badge>
                      </td>
                      <td
                        className={`py-4 px-6 text-right font-bold text-base whitespace-nowrap ${
                          tx.transaction_type === "income"
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-slate-900 dark:text-slate-100"
                        }`}
                      >
                        {tx.transaction_type === "income" ? "+" : "-"}
                        {formatCurrency(tx.amount, "INR")}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => handleDeleteTransaction(tx.id)}
                          className="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition-colors"
                          title="Delete transaction"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Transaction Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Transaction"
        description="Log a new financial transaction manually"
      >
        <form onSubmit={handleCreateTransaction} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Date"
              type="date"
              value={txDate}
              onChange={(e) => setTxDate(e.target.value)}
              required
            />
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Type
              </label>
              <select
                value={txType}
                onChange={(e) => setTxType(e.target.value as TransactionType)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Amount (INR)"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="e.g. 1500.00"
              value={txAmount}
              onChange={(e) => setTxAmount(e.target.value)}
              required
            />
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Category
              </label>
              <select
                value={txCategory}
                onChange={(e) => setTxCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Input
            label="Description"
            placeholder="e.g. Grocery shopping at supermarket"
            value={txDescription}
            onChange={(e) => setTxDescription(e.target.value)}
            required
          />

          <div className="flex justify-end gap-2 pt-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
              Save Transaction
            </Button>
          </div>
        </form>
      </Modal>

      {/* CSV Import Modal */}
      <Modal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        title="Import CSV Statement"
        description="Upload bank/credit card transactions CSV"
      >
        <form onSubmit={handleImportCSV} className="space-y-4">
          {importError && <ErrorBanner message={importError} />}

          {importResult && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Import Finished</span>
              </div>
              <p>Total Rows: {importResult.total_rows}</p>
              <p>Successfully Imported: {importResult.imported_count}</p>
              <p>Duplicate Rows Skipped: {importResult.duplicate_count}</p>
              {importResult.errors.length > 0 && (
                <p className="text-rose-600">Errors: {importResult.errors.join(", ")}</p>
              )}
            </div>
          )}

          <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-6 text-center">
            <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            />
            <p className="text-[11px] text-slate-400 mt-2">
              Expected CSV columns: Date, Amount, Type, Category, Description
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsImportModalOpen(false)}
            >
              Close
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!selectedFile}
              isLoading={isImporting}
            >
              Upload & Process
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
