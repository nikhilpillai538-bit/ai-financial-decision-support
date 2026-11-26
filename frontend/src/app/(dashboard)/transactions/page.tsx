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
  Download,
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

  const downloadSampleCSV = () => {
    const csvContent =
      "date,description,amount,transaction_type,category\n" +
      "2026-11-02,Freelance Consulting Payment,35000.00,income,Salary & Income\n" +
      "2026-11-04,Swiggy Food Delivery,640.00,expense,Dining & Food\n" +
      "2026-11-06,Shell Auto Petrol,2100.00,expense,Transportation\n" +
      "2026-11-07,DMart Supermarket Groceries,4320.00,expense,Groceries\n" +
      "2026-11-12,Dividend Credit TCS,1200.00,income,Investments & Savings\n" +
      "2026-11-15,Electricity Bill Payment,2350.00,expense,Utilities\n";

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "sample_transactions.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await transactionsApi.listTransactions({
        category: selectedCategory || undefined,
        limit: 100,
      });
      const items = Array.isArray(res) ? res : (res?.items || []);
      const count = Array.isArray(res) ? res.length : (res?.total_count ?? items.length);
      setTransactions(items);
      setTotalCount(count);
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
    const desc = (t.description || "").toLowerCase();
    const cat = (t.category || "").toLowerCase();
    const amt = String(t.amount || "");
    return desc.includes(term) || cat.includes(term) || amt.includes(term);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#1A263D]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Transactions Ledger
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
            Log financial activities, categorize transactions, and import statements into the verified store.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsImportModalOpen(true)}
            className="gap-1.5 border-[#202D45] text-slate-300 hover:text-white"
          >
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span>Import CSV</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddModalOpen(true)}
            className="gap-1.5 shadow-md shadow-cyan-950/40"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Transaction</span>
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchTransactions} />}

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search by description, category, or amount..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-xs sm:text-sm bg-[#0E1524] border border-[#202D45] rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 transition-all text-white placeholder:text-slate-400"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="w-4 h-4 text-slate-400 shrink-0" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3.5 py-2 text-xs sm:text-sm bg-[#0E1524] border border-[#202D45] rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 w-full sm:w-56 text-slate-200 font-medium"
              >
                <option value="" className="bg-[#0E1524] text-slate-400">All Categories</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c} className="bg-[#0E1524] text-white">
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
        <CardHeader className="py-4 px-5 sm:px-6 flex flex-row items-center justify-between border-b border-[#1C273C]">
          <div>
            <CardTitle>Transaction Ledger</CardTitle>
            <CardDescription>
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
                <Button variant="primary" size="sm" onClick={() => setIsAddModalOpen(true)}>
                  Add First Transaction
                </Button>
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs sm:text-sm text-left">
                <thead className="bg-[#0C121F] text-slate-400 uppercase tracking-wider text-[11px] font-bold border-y border-[#1C273C]">
                  <tr>
                    <th className="py-3 px-5 sm:px-6">Date</th>
                    <th className="py-3 px-5 sm:px-6">Description</th>
                    <th className="py-3 px-5 sm:px-6">Category</th>
                    <th className="py-3 px-5 sm:px-6 text-center">Type</th>
                    <th className="py-3 px-5 sm:px-6 text-right">Amount</th>
                    <th className="py-3 px-5 sm:px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1C273C]">
                  {filteredTransactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-[#141C2C]/50 transition-colors">
                      <td className="py-3.5 px-5 sm:px-6 text-slate-400 font-mono text-xs whitespace-nowrap">
                        {formatDate(tx.date)}
                      </td>
                      <td className="py-3.5 px-5 sm:px-6 font-semibold text-white max-w-sm truncate">
                        {tx.description}
                      </td>
                      <td className="py-3.5 px-5 sm:px-6">
                        <Badge variant="default">{tx.category}</Badge>
                      </td>
                      <td className="py-3.5 px-5 sm:px-6 text-center">
                        <Badge variant={tx.transaction_type === "income" ? "success" : "default"}>
                          {tx.transaction_type.toUpperCase()}
                        </Badge>
                      </td>
                      <td
                        className={`py-3.5 px-5 sm:px-6 text-right font-bold text-xs sm:text-sm font-mono whitespace-nowrap ${
                          tx.transaction_type === "income"
                            ? "text-emerald-400"
                            : "text-slate-100"
                        }`}
                      >
                        {tx.transaction_type === "income" ? "+" : "-"}
                        {formatCurrency(tx.amount, "INR")}
                      </td>
                      <td className="py-3.5 px-5 sm:px-6 text-right">
                        <button
                          onClick={() => handleDeleteTransaction(tx.id)}
                          className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-950/30 transition-colors"
                          title="Delete transaction"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
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
                className="w-full px-3.5 py-2.5 text-xs sm:text-sm bg-[#0E1524] border border-[#202D45] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 font-medium"
              >
                <option value="expense" className="bg-[#0E1524] text-white">Expense</option>
                <option value="income" className="bg-[#0E1524] text-white">Income</option>
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
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Category
              </label>
              <select
                value={txCategory}
                onChange={(e) => setTxCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 text-xs sm:text-sm bg-[#0E1524] border border-[#202D45] rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 font-medium"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c} className="bg-[#0E1524] text-white">
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
            <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800/80 text-emerald-200 text-xs space-y-2 animate-fade-in">
              <div className="flex items-center gap-1.5 font-bold text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>CSV Processing Complete</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center pt-1 font-mono">
                <div className="bg-[#0E1524] p-2 rounded-lg border border-[#202D45]">
                  <span className="block text-slate-400 text-[10px] uppercase">Total</span>
                  <span className="font-bold text-white text-sm">{importResult.total_rows}</span>
                </div>
                <div className="bg-[#0E1524] p-2 rounded-lg border border-[#202D45]">
                  <span className="block text-emerald-400 text-[10px] uppercase">Imported</span>
                  <span className="font-bold text-emerald-400 text-sm">{importResult.imported_count}</span>
                </div>
                <div className="bg-[#0E1524] p-2 rounded-lg border border-[#202D45]">
                  <span className="block text-amber-400 text-[10px] uppercase">Duplicates</span>
                  <span className="font-bold text-amber-400 text-sm">{importResult.duplicate_count}</span>
                </div>
              </div>
              {importResult.errors && importResult.errors.length > 0 && (
                <div className="text-rose-400 pt-1 text-[11px]">
                  <p className="font-semibold">Skipped / Error Rows:</p>
                  <ul className="list-disc pl-4 space-y-0.5 max-h-24 overflow-y-auto">
                    {importResult.errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="border border-dashed border-[#23324C] rounded-2xl p-6 text-center space-y-3 bg-[#0D1422]/60">
            <Upload className="w-8 h-8 text-cyan-400 mx-auto" />
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-cyan-950/80 file:text-cyan-300 hover:file:bg-cyan-900/80 cursor-pointer"
            />
            <div className="text-[11px] text-slate-400 space-y-1.5">
              <p>Expected columns: <code className="font-mono bg-[#111827] border border-[#202D45] px-1.5 py-0.5 rounded text-cyan-300">date, description, amount, transaction_type, category</code></p>
              <div className="pt-1">
                <button
                  type="button"
                  onClick={downloadSampleCSV}
                  className="inline-flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 font-bold text-xs hover:underline"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Sample CSV Template</span>
                </button>
              </div>
            </div>
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
