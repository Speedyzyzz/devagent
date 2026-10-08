"use client";

import React from "react";
import { SessionState, SessionStatus } from "@/lib/types";
import { Activity, CheckCircle2, XCircle, AlertCircle, StopCircle, ShieldCheck } from "lucide-react";

interface SessionStatusProps {
  session: SessionState | null;
  onCancel?: () => void;
  onOpenBenchmarkStats?: () => void;
}

export function SessionStatusBadge({ session, onCancel, onOpenBenchmarkStats }: SessionStatusProps) {
  const status: SessionStatus = session?.status || "CREATED";

  const getStatusColor = () => {
    switch (status) {
      case "COMPLETED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "FAILED":
      case "TIMEOUT":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "CANCELLED":
        return "bg-zinc-500/10 text-zinc-400 border-zinc-500/20";
      default:
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    }
  };

  const isRunning = [
    "INITIALIZING",
    "RECONNAISSING",
    "INVESTIGATING",
    "PATCHING",
    "VERIFYING",
    "CORRECTING",
  ].includes(status);

  return (
    <header className="w-full flex items-center justify-between px-6 py-4 border-b border-white/[0.06] bg-[#070A11]/80 backdrop-blur-xl sticky top-0 z-40">
      {/* Brand & Badge */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <span className="font-mono font-black text-white text-xs tracking-wider">DA</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-white">DevAgent</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.06] border border-white/[0.08] text-zinc-400 font-medium">
                v1.0 sandbox
              </span>
            </div>
            <p className="text-[11px] text-zinc-500 font-medium">Policy-Constrained Autonomous Debugger</p>
          </div>
        </div>

        {session && (
          <div className="hidden md:flex items-center gap-2 pl-4 border-l border-white/[0.08]">
            <span className="text-[11px] font-mono text-zinc-400">ID:</span>
            <span className="text-[11px] font-mono text-zinc-300 font-semibold px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.06]">
              {session.session_id}
            </span>
          </div>
        )}
      </div>

      {/* Live Telemetry & Actions */}
      <div className="flex items-center gap-3">
        {session && (
          <div className="hidden lg:flex items-center gap-4 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.06] text-xs font-mono text-zinc-400">
            <div className="flex items-center gap-1.5">
              <span className="text-zinc-500">Turn:</span>
              <span className="text-zinc-200 font-semibold">{session.iteration}/{session.max_iterations}</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-zinc-700" />
            <div className="flex items-center gap-1.5">
              <span className="text-zinc-500">Tools:</span>
              <span className="text-zinc-200 font-semibold">{session.tool_calls_count}</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-zinc-700" />
            <div className="flex items-center gap-1.5">
              <span className="text-zinc-500">Tests:</span>
              <span className="text-zinc-200 font-semibold">{session.verification_attempts}</span>
            </div>
          </div>
        )}

        {/* Status Pill */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold ${getStatusColor()}`}>
          {isRunning ? (
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
            </span>
          ) : status === "COMPLETED" ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          ) : status === "FAILED" ? (
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-zinc-400" />
          )}
          <span className="font-mono tracking-wider text-[11px] uppercase">{status}</span>
        </div>

        {/* Benchmark Stats Button */}
        {onOpenBenchmarkStats && (
          <button
            onClick={onOpenBenchmarkStats}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-zinc-300 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Benchmark (5/5)</span>
          </button>
        )}

        {/* Cancel Button */}
        {isRunning && onCancel && (
          <button
            onClick={onCancel}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 text-xs font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <StopCircle className="w-3.5 h-3.5" />
            <span>Stop Agent</span>
          </button>
        )}
      </div>
    </header>
  );
}
