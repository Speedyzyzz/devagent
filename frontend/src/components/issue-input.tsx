"use client";

import React, { useState } from "react";
import { BenchmarkCase } from "@/lib/types";
import { ArrowRight, Sparkles, Terminal, Bug, Play, ShieldAlert } from "lucide-react";

interface IssueInputProps {
  benchmarkCases: BenchmarkCase[];
  onSubmit: (data: {
    issue: string;
    verification_instruction?: string;
    provider: string;
    case_id?: string;
  }) => void;
  isLoading: boolean;
}

export function IssueInput({ benchmarkCases, onSubmit, isLoading }: IssueInputProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<string>("case_001_guest_session");
  const [customIssue, setCustomIssue] = useState<string>("");
  const [customVerification, setCustomVerification] = useState<string>("");
  const [provider, setProvider] = useState<string>("mock");
  const [mode, setMode] = useState<"preset" | "custom">("preset");

  const selectedCase = benchmarkCases.find((c) => c.id === selectedCaseId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "preset" && selectedCase) {
      onSubmit({
        issue: selectedCase.issue,
        verification_instruction: selectedCase.verification
          ? `${selectedCase.verification.runner} ${selectedCase.verification.args.join(" ")}`
          : undefined,
        provider,
        case_id: selectedCase.id,
      });
    } else if (mode === "custom") {
      if (!customIssue.trim()) return;
      onSubmit({
        issue: customIssue,
        verification_instruction: customVerification.trim() || undefined,
        provider,
      });
    }
  };

  return (
    <div className="w-full rounded-[24px] p-2 bg-white/[0.03] border border-white/[0.08] shadow-double-bezel">
      <div className="rounded-[20px] bg-[#0A0E17]/95 p-6 backdrop-blur-xl border border-white/[0.04]">
        {/* Header & Tabs */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] uppercase font-bold tracking-[0.2em] px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Sandbox Execution
              </span>
              <span className="text-zinc-500 text-xs">•</span>
              <span className="text-zinc-400 text-xs font-mono">Isolated Workspace</span>
            </div>
            <h2 className="text-xl font-bold tracking-tight text-white">Investigate & Fix Repository Bug</h2>
          </div>

          <div className="flex items-center gap-1.5 p-1 rounded-full bg-white/[0.04] border border-white/[0.06]">
            <button
              type="button"
              onClick={() => setMode("preset")}
              className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                mode === "preset" ? "bg-white text-black shadow-sm" : "text-zinc-400 hover:text-white"
              }`}
            >
              Benchmark Suite (5)
            </button>
            <button
              type="button"
              onClick={() => setMode("custom")}
              className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                mode === "custom" ? "bg-white text-black shadow-sm" : "text-zinc-400 hover:text-white"
              }`}
            >
              Custom Issue
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {mode === "preset" ? (
            <div className="space-y-4">
              <label className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <Bug className="w-3.5 h-3.5 text-blue-400" />
                Select Injected Benchmark Bug
              </label>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {benchmarkCases.map((c) => {
                  const isSelected = c.id === selectedCaseId;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setSelectedCaseId(c.id)}
                      className={`text-left p-3.5 rounded-2xl border transition-all text-xs ${
                        isSelected
                          ? "bg-blue-500/[0.08] border-blue-500/40 text-white shadow-[0_0_20px_rgba(59,130,246,0.15)] ring-1 ring-blue-500/30"
                          : "bg-white/[0.02] border-white/[0.06] text-zinc-400 hover:border-white/[0.12] hover:text-zinc-200"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold text-zinc-200 truncate">{c.name}</span>
                        {isSelected && <span className="w-2 h-2 rounded-full bg-blue-400" />}
                      </div>
                      <p className="line-clamp-2 text-[11px] text-zinc-500 leading-relaxed font-normal mb-2">
                        {c.issue}
                      </p>
                      {c.verification && (
                        <div className="flex items-center gap-1.5 font-mono text-[10px] text-zinc-400 bg-white/[0.03] px-2 py-1 rounded-md border border-white/[0.04]">
                          <Terminal className="w-3 h-3 text-zinc-500" />
                          <span>{c.verification.runner} {c.verification.args[0]}</span>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2 block">
                  Issue Description
                </label>
                <textarea
                  value={customIssue}
                  onChange={(e) => setCustomIssue(e.target.value)}
                  placeholder="Describe the bug, expected vs actual behavior, or error logs..."
                  rows={3}
                  className="w-full rounded-2xl bg-white/[0.03] border border-white/[0.08] p-4 text-xs font-sans text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 resize-none"
                />
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2 block">
                  Verification Instruction (Optional)
                </label>
                <input
                  type="text"
                  value={customVerification}
                  onChange={(e) => setCustomVerification(e.target.value)}
                  placeholder="e.g. pytest tests/test_checkout.py"
                  className="w-full rounded-xl bg-white/[0.03] border border-white/[0.08] px-4 py-2.5 text-xs font-mono text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/50"
                />
              </div>
            </div>
          )}

          {/* Engine & Provider Controls */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 pt-4 border-t border-white/[0.06]">
            <div className="flex items-center gap-3">
              <span className="text-xs text-zinc-400 font-medium">Provider:</span>
              <div className="flex items-center gap-1 p-1 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                <button
                  type="button"
                  onClick={() => setProvider("mock")}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition-all ${
                    provider === "mock" ? "bg-blue-600 text-white shadow-sm" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Mock (Deterministic)
                </button>
                <button
                  type="button"
                  onClick={() => setProvider("gemini")}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition-all ${
                    provider === "gemini" ? "bg-blue-600 text-white shadow-sm" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Gemini Flash
                </button>
                <button
                  type="button"
                  onClick={() => setProvider("openai")}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition-all ${
                    provider === "openai" ? "bg-blue-600 text-white shadow-sm" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  OpenAI
                </button>
              </div>
            </div>

            {/* Launch CTA with Button-in-Button architecture */}
            <button
              type="submit"
              disabled={isLoading}
              className="group relative inline-flex items-center justify-between gap-3 bg-white hover:bg-zinc-100 text-black pl-5 pr-2 py-2 rounded-full font-bold text-xs tracking-tight shadow-lg shadow-white/10 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              <span>{isLoading ? "Autonomous Run In Progress..." : "Launch DevAgent"}</span>
              <div className="w-7 h-7 rounded-full bg-black flex items-center justify-center transition-transform group-hover:translate-x-0.5">
                <ArrowRight className="w-3.5 h-3.5 text-white" />
              </div>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
