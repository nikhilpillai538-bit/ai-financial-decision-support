"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import {
  LoadingState,
  ErrorBanner,
  RegulatoryDisclaimer,
} from "@/components/shared/States";
import { aiApi } from "@/lib/api/ai";
import { portfolioApi } from "@/lib/api/portfolio";
import {
  AIMessage,
  AIThreadSummary,
  FinancialHealthReport,
  Portfolio,
} from "@/types";
import { formatCurrency, formatDate } from "@/lib/formatters";
import {
  Bot,
  User,
  Send,
  PlusCircle,
  MessageSquare,
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  HelpCircle,
  Activity,
  Layers,
  ArrowRight,
  Cpu,
} from "lucide-react";

const STARTER_PROMPTS = [
  "How is my 30-day cash flow forecast looking?",
  "Do I have sufficient emergency fund coverage for 6 months of expenses?",
  "Explain the current asset allocation drift in my portfolio.",
  "What is the mathematical rationale behind my MPT optimal weights?",
];

export default function AssistantPage() {
  const [threads, setThreads] = useState<AIThreadSummary[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>("");

  // UI States
  const [isLoadingThreads, setIsLoadingThreads] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Health Report Modal
  const [showReportModal, setShowReportModal] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [healthReport, setHealthReport] = useState<FinancialHealthReport | null>(null);

  // Scenario Modal
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [scenarioType, setScenarioType] = useState<"expense" | "income_reduction" | "market_drop">("expense");
  const [scenarioAmount, setScenarioAmount] = useState("200000");
  const [isEvaluatingScenario, setIsEvaluatingScenario] = useState(false);
  const [scenarioResult, setScenarioResult] = useState<any>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (activeThreadId) {
      loadThreadMessages(activeThreadId);
    }
  }, [activeThreadId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  async function loadInitialData() {
    setIsLoadingThreads(true);
    try {
      const [thList, portList] = await Promise.all([
        aiApi.listThreads().catch(() => []),
        portfolioApi.listPortfolios().catch(() => []),
      ]);
      setThreads(thList);
      setPortfolios(portList);
      if (thList.length > 0) {
        setActiveThreadId(thList[0].thread_id);
      }
    } catch (err: any) {
      console.error("Error loading assistant threads:", err);
    } finally {
      setIsLoadingThreads(false);
    }
  }

  async function loadThreadMessages(threadId: string) {
    setIsLoadingMessages(true);
    try {
      const detail = await aiApi.getThread(threadId);
      setMessages(detail.messages || []);
    } catch (err: any) {
      console.error("Error loading thread messages:", err);
    } finally {
      setIsLoadingMessages(false);
    }
  }

  function handleStartNewThread() {
    setActiveThreadId(null);
    setMessages([]);
  }

  async function handleSendMessage(textToSend?: string) {
    const text = (textToSend || inputText).trim();
    if (!text || isSending) return;

    setInputText("");
    setError(null);

    // Optimistically add user message
    const tempUserMsg: AIMessage = {
      id: "temp-" + Date.now(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsSending(true);

    try {
      const res = await aiApi.sendMessage({
        message: text,
        thread_id: activeThreadId || undefined,
        portfolio_id: selectedPortfolioId || undefined,
      });

      const assistantMsg: AIMessage = {
        id: "resp-" + Date.now(),
        role: "assistant",
        content: res.message,
        created_at: new Date().toISOString(),
        domains_retrieved: res.domains_retrieved,
        verified_metrics: res.verified_metrics,
        suggested_followups: res.suggested_followups,
        warnings: res.warnings,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // If this was a new thread, update activeThreadId and reload threads list
      if (!activeThreadId && res.thread_id) {
        setActiveThreadId(res.thread_id);
        const thList = await aiApi.listThreads().catch(() => []);
        setThreads(thList);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to generate AI response. Financial services remain operational.");
    } finally {
      setIsSending(false);
    }
  }

  async function handleGenerateHealthReport() {
    setIsGeneratingReport(true);
    setShowReportModal(true);
    try {
      const rep = await aiApi.generateHealthReport(selectedPortfolioId || undefined);
      setHealthReport(rep);
    } catch (err: any) {
      setError(err?.message || "Failed to generate financial health synthesis");
    } finally {
      setIsGeneratingReport(false);
    }
  }

  async function handleRunScenario(e: React.FormEvent) {
    e.preventDefault();
    setIsEvaluatingScenario(true);
    try {
      const res = await aiApi.evaluateScenario(scenarioType, {
        amount: scenarioAmount,
        portfolio_id: selectedPortfolioId || undefined,
      });
      setScenarioResult(res);
    } catch (err: any) {
      setError(err?.message || "Scenario simulation failed");
    } finally {
      setIsEvaluatingScenario(false);
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#202D45] pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
              <Sparkles className="w-7 h-7 text-cyan-400" />
              AI Financial Decision Assistant
            </h1>
            <Badge variant="cyan" className="font-mono text-[10px] uppercase tracking-wider">
              Grounded AI Engine
            </Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1.5 font-normal">
            Evidence-grounded explanations, verified calculations, and comprehensive financial synthesis without hallucinations.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Button
            variant="outline"
            size="md"
            onClick={() => {
              setScenarioResult(null);
              setShowScenarioModal(true);
            }}
          >
            <Activity className="w-4 h-4 mr-2" />
            What-If Scenario
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleGenerateHealthReport}
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Health Synthesis
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Main Chat Interface */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 min-h-[640px]">
        {/* Threads Sidebar */}
        <Card className="md:col-span-1 flex flex-col h-[640px] overflow-hidden">
          <div className="p-3 border-b border-[#202D45]">
            <Button
              variant="outline"
              size="sm"
              onClick={handleStartNewThread}
              className="w-full justify-start text-xs gap-2"
            >
              <PlusCircle className="w-4 h-4 text-cyan-400" />
              New Chat Thread
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-[#202D45] p-2 space-y-1">
            {isLoadingThreads ? (
              <div className="p-4 text-center text-xs text-slate-400">Loading conversations...</div>
            ) : threads.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">
                No past chat threads. Start a conversation below.
              </div>
            ) : (
              threads.map((t) => (
                <button
                  key={t.thread_id}
                  onClick={() => setActiveThreadId(t.thread_id)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors ${
                    activeThreadId === t.thread_id
                      ? "bg-[#162032] border-l-2 border-cyan-400 text-white font-medium"
                      : "text-slate-400 hover:bg-[#162032]/40 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-1.5 truncate">
                    <MessageSquare className="w-3.5 h-3.5 shrink-0 text-cyan-400" />
                    <span className="truncate">{t.title || "Financial Conversation"}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono mt-1 pl-5">
                    {formatDate(t.last_message_at || t.created_at)}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Context Selector */}
          {portfolios.length > 0 && (
            <div className="p-3 border-t border-[#202D45] bg-[#0A0F1D] text-xs">
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Portfolio Grounding:
              </label>
              <select
                value={selectedPortfolioId}
                onChange={(e) => setSelectedPortfolioId(e.target.value)}
                className="w-full text-xs rounded-lg border border-[#202D45] bg-[#0E1524] p-2 text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                <option value="">All Portfolios / Aggregate</option>
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </Card>

        {/* Chat Messages Panel */}
        <Card className="md:col-span-3 flex flex-col h-[640px] overflow-hidden">
          {/* Header */}
          <div className="p-3.5 border-b border-[#202D45] flex items-center justify-between bg-[#0A0F1D]">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-semibold text-white">
                Grounding Engine: Financial Context Retrieval + FinBERT
              </span>
            </div>
            <span className="text-[11px] font-mono text-cyan-400/80">
              Deterministic Calculations Authoritative
            </span>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {isLoadingMessages ? (
              <LoadingState message="Retrieving conversation history..." />
            ) : messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-14 h-14 rounded-2xl bg-[#0E1524] border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-glow-cyan">
                  <Bot className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    How can I assist your financial decision-making today?
                  </h3>
                  <p className="text-xs text-slate-400 max-w-md mt-1 leading-relaxed">
                    Ask questions regarding your cash flow, emergency reserves, portfolio allocation drift, or market news impact.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-lg pt-2">
                  {STARTER_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(prompt)}
                      className="text-left text-xs p-3 rounded-xl border border-[#202D45] hover:border-cyan-500/50 hover:bg-cyan-950/20 text-slate-300 hover:text-cyan-200 transition-colors leading-relaxed"
                    >
                      &ldquo;{prompt}&rdquo;
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={msg.id || idx}
                  className={`flex gap-3 ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-xl bg-cyan-950/60 border border-cyan-500/30 flex items-center justify-center shrink-0 mt-0.5 text-cyan-400">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-2xl rounded-2xl p-4 text-xs space-y-3 leading-relaxed ${
                      msg.role === "user"
                        ? "bg-gradient-to-r from-cyan-600 to-teal-600 text-white shadow-md shadow-cyan-950/50 ml-12"
                        : "bg-[#0E1524] border border-[#202D45] text-slate-200 mr-12"
                    }`}
                  >
                    {/* Content */}
                    <div className="whitespace-pre-wrap leading-relaxed">
                      {msg.content}
                    </div>

                    {/* Domains Retrieved Pills */}
                    {msg.domains_retrieved && msg.domains_retrieved.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-[#202D45] text-[10px]">
                        <span className="text-slate-400 font-medium">Grounded in:</span>
                        {msg.domains_retrieved.map((d, dIdx) => (
                          <span
                            key={dIdx}
                            className="bg-[#162032] border border-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded capitalize font-mono"
                          >
                            {d.replace("_", " ")}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Verified Metrics Card */}
                    {msg.verified_metrics && Object.keys(msg.verified_metrics).length > 0 && (
                      <div className="bg-[#0A0F1D] border border-[#202D45] rounded-xl p-3 space-y-1.5 text-[11px]">
                        <span className="font-semibold text-cyan-300 block text-[10px] uppercase tracking-wider font-mono">
                          Backend Verified Metrics:
                        </span>
                        <div className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono">
                          {Object.entries(msg.verified_metrics).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-slate-400 capitalize font-sans">{k.replace("_", " ")}:</span>
                              <span className="font-bold text-white">
                                {typeof v === "number" ? v.toLocaleString() : String(v)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Warnings */}
                    {msg.warnings && msg.warnings.length > 0 && (
                      <div className="bg-amber-950/40 border border-amber-500/30 rounded-lg p-2.5 text-amber-300 text-[11px]">
                        {msg.warnings.join(" ")}
                      </div>
                    )}

                    {/* Suggested Followups */}
                    {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                      <div className="pt-2 border-t border-[#202D45] space-y-1.5">
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
                          Suggested Inquiries:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.suggested_followups.map((fu, fuIdx) => (
                            <button
                              key={fuIdx}
                              onClick={() => handleSendMessage(fu)}
                              className="text-[11px] bg-[#162032] border border-[#202D45] hover:border-cyan-400 text-slate-300 hover:text-cyan-200 px-2.5 py-1 rounded-lg transition-colors text-left"
                            >
                              {fu}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-xl bg-[#162032] border border-[#202D45] flex items-center justify-center shrink-0 mt-0.5 text-slate-300">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))
            )}

            {isSending && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-xl bg-cyan-950/60 border border-cyan-500/30 flex items-center justify-center shrink-0 mt-0.5 text-cyan-400">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-[#0E1524] border border-[#202D45] rounded-2xl p-3 text-xs text-slate-300 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                  <span>Synthesizing evidence-based financial insights...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-3 border-t border-[#202D45] bg-[#0A0F1D]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <Input
                type="text"
                placeholder="Ask about cash flow, emergency funds, portfolio rebalancing, or news impact..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isSending}
                className="flex-1 text-xs"
              />
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isSending}
                disabled={!inputText.trim()}
                className="gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                Send
              </Button>
            </form>
            <p className="text-[10px] text-slate-400 text-center mt-1.5">
              Financial guidance is for educational and decision support only. The system cannot execute trades.
            </p>
          </div>
        </Card>
      </div>

      {/* Health Report Modal */}
      <Modal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        title="Comprehensive Financial Health Synthesis"
      >
        {isGeneratingReport ? (
          <LoadingState message="Synthesizing multi-domain financial health indicators..." />
        ) : healthReport ? (
          <div className="space-y-4 text-xs">
            {/* Score header */}
            {healthReport.health_score !== undefined && (
              <div className="flex items-center justify-between p-3.5 bg-cyan-950/40 border border-cyan-500/30 rounded-xl">
                <span className="font-semibold text-white">Aggregate Financial Health Score:</span>
                <span className="text-xl font-mono font-extrabold text-cyan-300">
                  {healthReport.health_score} / 100
                </span>
              </div>
            )}

            {/* Executive summary */}
            <div>
              <h4 className="font-semibold text-white mb-1.5">Executive Summary</h4>
              <p className="text-slate-300 leading-relaxed bg-[#0A0F1D] p-3.5 rounded-xl border border-[#202D45]">
                {healthReport.executive_summary}
              </p>
            </div>

            {/* Domain breakdown */}
            {healthReport.domain_insights && (
              <div className="space-y-2">
                <h4 className="font-semibold text-white">Domain Findings</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {Object.entries(healthReport.domain_insights).map(([domain, text]) => (
                    <div key={domain} className="p-3 rounded-xl border border-[#202D45] bg-[#0A0F1D]">
                      <span className="font-semibold text-cyan-300 capitalize block mb-1">
                        {domain.replace("_", " ")}
                      </span>
                      <p className="text-slate-400 text-[11px] leading-relaxed">{text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings */}
            {healthReport.warnings && healthReport.warnings.length > 0 && (
              <div className="bg-amber-950/40 p-3 rounded-xl border border-amber-500/30 text-amber-300 space-y-1">
                <span className="font-semibold block">Attention Required:</span>
                {healthReport.warnings.map((w, i) => (
                  <div key={i}>• {w}</div>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <Button size="sm" variant="outline" onClick={() => setShowReportModal(false)}>
                Close Report
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-4 text-xs text-slate-400">
            Unable to load health report.
          </div>
        )}
      </Modal>

      {/* What-If Scenario Modal */}
      <Modal
        isOpen={showScenarioModal}
        onClose={() => setShowScenarioModal(false)}
        title="Simulate What-If Financial Scenario"
      >
        <form onSubmit={handleRunScenario} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-300 mb-1.5 uppercase tracking-wider text-[11px]">
              Select Scenario Type
            </label>
            <select
              value={scenarioType}
              onChange={(e) => setScenarioType(e.target.value as any)}
              className="w-full text-xs rounded-lg border border-[#202D45] bg-[#0E1524] p-2.5 text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value="expense">Major Unplanned Expense (Medical / Home / Auto)</option>
              <option value="income_reduction">Income Reduction (Job Transition / 30% Pay Cut)</option>
              <option value="market_drop">Market Correction (20% Equity Valuation Decline)</option>
            </select>
          </div>

          <Input
            label={scenarioType === "market_drop" ? "Correction Percentage (e.g. 0.20 for 20%)" : "Amount (₹)"}
            type="number"
            value={scenarioAmount}
            onChange={(e) => setScenarioAmount(e.target.value)}
            required
          />

          <Button type="submit" variant="primary" size="sm" className="w-full" isLoading={isEvaluatingScenario}>
            Simulate Impact
          </Button>

          {scenarioResult && (
            <div className="p-3.5 bg-[#0A0F1D] border border-cyan-500/30 rounded-xl space-y-2 mt-3">
              <h4 className="font-semibold text-cyan-300">Simulation Output:</h4>
              <p className="text-slate-300 leading-relaxed">
                {scenarioResult.explanation || scenarioResult.impact_summary || JSON.stringify(scenarioResult)}
              </p>
            </div>
          )}
        </form>
      </Modal>

      <RegulatoryDisclaimer />
    </div>
  );
}
