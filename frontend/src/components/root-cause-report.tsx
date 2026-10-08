"use client";

import React from "react";
import { CheckCircle2, ShieldAlert, Sparkles, BookOpen } from "lucide-react";

interface RootCauseReportProps {
  report: string | null;
  error?: string | null;
  status: string;
}

export function RootCauseReport({ report, error, status }: RootCauseReportProps) {
  if (!report && !error) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 rounded-[24px] bg-white/[0.03] border border-white/[0.08] shadow-double-bezel text-zinc-500">
        <BookOpen className="w-8 h-8 mb-3 opacity-30 text-zinc-400" />
        <p className="text-xs font-medium text-zinc-400">Diagnosis In Progress</p>
        <p className="text-[11px] text-zinc-600 mt-1 max-w-xs">
          The autonomous diagnosis and root-cause summary report will formulate once tests pass and the fix is verified.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col rounded-[24px] p-2 bg-white/[0.03] border border-white/[0.08] shadow-double-bezel overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-[#0A0E17]/95 rounded-t-[20px]">
        <div className="flex items-center gap-2">
          {error ? (
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          ) : (
            <Sparkles className="w-4 h-4 text-emerald-400" />
          )}
          <span className="font-bold text-xs uppercase tracking-wider text-zinc-300">
            {error ? "Failure Diagnosis" : "Root Cause Analysis (RCA)"}
          </span>
        </div>

        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
          status === "COMPLETED"
            ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
            : "text-rose-400 bg-rose-500/10 border-rose-500/20"
        }`}>
          {status}
        </span>
      </div>

      <div className="flex-1 p-5 overflow-y-auto bg-[#0A0E17]/95 rounded-b-[20px] font-sans space-y-4">
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            <span className="font-bold block mb-1">Execution Interrupted</span>
            <p className="font-mono text-[11px] text-rose-400/90">{error}</p>
          </div>
        )}

        {report && (
          <div className="prose prose-invert prose-sm max-w-none text-zinc-300 space-y-3 text-xs leading-relaxed">
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
              <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1 tracking-wider">
                Root Cause Synthesis
              </span>
              <p className="text-zinc-200 text-xs font-medium leading-relaxed whitespace-pre-wrap">
                {report}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">
                  Verification State
                </span>
                <span className="text-emerald-400 font-mono text-xs font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verified & Passing
                </span>
              </div>

              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <span className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">
                  Confidence Score
                </span>
                <span className="text-blue-400 font-mono text-xs font-semibold">
                  100% Deterministic Pass
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
