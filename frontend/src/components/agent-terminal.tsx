"use client";

import React, { useEffect, useRef } from "react";
import { TimelineStep } from "@/lib/types";
import { ToolOutput } from "./tool-output";
import { Terminal, Lightbulb, Compass, CheckCircle2, XCircle, Loader2 } from "lucide-react";

interface AgentTerminalProps {
  timeline: TimelineStep[];
  isConnected: boolean;
  isDone: boolean;
}

export function AgentTerminal({ timeline, isConnected, isDone }: AgentTerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [timeline]);

  return (
    <div className="h-full flex flex-col rounded-[24px] p-2 bg-white/[0.03] border border-white/[0.08] shadow-double-bezel overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-[#0A0E17]/95 rounded-t-[20px]">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-blue-400" />
          <span className="font-bold text-xs uppercase tracking-wider text-zinc-300">
            Agent Execution Timeline
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-400" : "bg-zinc-600"}`} />
          <span className="text-[11px] font-mono text-zinc-400">
            {isConnected ? "Live Stream Connected" : "Stream Idle"}
          </span>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 p-4 overflow-y-auto space-y-4 bg-[#0A0E17]/95 rounded-b-[20px] font-sans scroll-smooth"
      >
        {timeline.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-zinc-500">
            <Terminal className="w-8 h-8 mb-3 opacity-40 text-blue-400" />
            <p className="text-xs font-medium text-zinc-400">Awaiting Agent Invocation</p>
            <p className="text-[11px] text-zinc-600 mt-1 max-w-xs">
              Select a benchmark case or enter an issue to watch DevAgent map the repo, search symbols, patch, and verify.
            </p>
          </div>
        ) : (
          timeline.map((step, idx) => {
            const isLast = idx === timeline.length - 1;
            const isRunning = isLast && !isDone;

            return (
              <div
                key={step.step}
                className="rounded-2xl border border-white/[0.06] bg-[#0E1422]/70 p-4 transition-all"
              >
                {/* Step Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      Step {step.step}
                    </span>
                    <span className="text-[11px] font-mono text-zinc-500">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div>
                    {isRunning ? (
                      <span className="flex items-center gap-1.5 text-[10px] font-mono text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/20">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>RUNNING</span>
                      </span>
                    ) : step.status === "completed" ? (
                      <span className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>COMPLETED</span>
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-[10px] font-mono text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full border border-rose-500/20">
                        <XCircle className="w-3 h-3" />
                        <span>FAILED</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Telemetry: Investigation, Hypothesis, Action */}
                {step.telemetry && (
                  <div className="space-y-2 mb-3 text-xs leading-relaxed">
                    {step.telemetry.investigation && (
                      <div className="flex items-start gap-2 p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                        <Compass className="w-3.5 h-3.5 text-zinc-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="text-[10px] uppercase font-bold text-zinc-500 block">Observation</span>
                          <span className="text-zinc-300">{step.telemetry.investigation}</span>
                        </div>
                      </div>
                    )}

                    {step.telemetry.hypothesis && (
                      <div className="flex items-start gap-2 p-2.5 rounded-xl bg-amber-500/[0.04] border border-amber-500/10">
                        <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="text-[10px] uppercase font-bold text-amber-500/80 block">Hypothesis</span>
                          <span className="text-amber-200/90">{step.telemetry.hypothesis}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tool Calls */}
                {step.toolCalls.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold text-zinc-500 block px-1">Tool Executions</span>
                    {step.toolCalls.map((tc) => (
                      <ToolOutput key={tc.id} toolCall={tc} />
                    ))}
                  </div>
                )}

                {/* Verification result preview if present */}
                {step.verification && (
                  <div className="mt-2 p-2.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 font-mono text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] uppercase font-bold text-cyan-400">Verification Runner</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${step.verification.passed ? "text-emerald-400 bg-emerald-500/20" : "text-rose-400 bg-rose-500/20"}`}>
                        {step.verification.passed ? "TEST PASSED" : "TEST FAILED"}
                      </span>
                    </div>
                    {step.verification.stdout && (
                      <pre className="text-[10px] text-zinc-400 overflow-x-auto whitespace-pre-wrap max-h-32 overflow-y-auto">
                        {step.verification.stdout.slice(0, 500)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
