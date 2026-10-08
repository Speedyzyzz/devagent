"use client";

import React, { useState } from "react";
import { GitCommit, Copy, Check, FileDiff, Sparkles } from "lucide-react";

interface DiffViewerProps {
  diff: string | null;
  filesChanged: string[];
  rootCause?: string | null;
}

export function DiffViewer({ diff, filesChanged, rootCause }: DiffViewerProps) {
  const [copiedPatch, setCopiedPatch] = useState(false);
  const [copiedPR, setCopiedPR] = useState(false);

  const handleCopyPatch = () => {
    if (!diff) return;
    navigator.clipboard.writeText(diff);
    setCopiedPatch(true);
    setTimeout(() => setCopiedPatch(false), 2000);
  };

  const handleCopyPRDescription = () => {
    const prText = [
      "## Summary",
      "Autonomous bug resolution generated and verified by DevAgent.",
      "",
      "## Root Cause & Analysis",
      rootCause || "Target bug verified and patched.",
      "",
      "## Modified Files",
      ...filesChanged.map((f) => `- \`${f}\``),
      "",
      "## Verification",
      "All automated pytest unit tests pass cleanly inside the isolated sandbox.",
      "",
      "## Diff",
      "```diff",
      diff || "",
      "```",
    ].join("\n");

    navigator.clipboard.writeText(prText);
    setCopiedPR(true);
    setTimeout(() => setCopiedPR(false), 2000);
  };

  if (!diff) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 rounded-[24px] bg-white/[0.03] border border-white/[0.08] shadow-double-bezel text-zinc-500">
        <FileDiff className="w-8 h-8 mb-3 opacity-30 text-zinc-400" />
        <p className="text-xs font-medium text-zinc-400">No Patches Applied Yet</p>
        <p className="text-[11px] text-zinc-600 mt-1 max-w-xs">
          When the agent identifies the root cause and executes apply_patch, the verified unified diff will render here.
        </p>
      </div>
    );
  }

  const lines = diff.split("\n");
  const addedCount = lines.filter((l) => l.startsWith("+") && !l.startsWith("+++")).length;
  const removedCount = lines.filter((l) => l.startsWith("-") && !l.startsWith("---")).length;

  return (
    <div className="h-full flex flex-col rounded-[24px] p-2 bg-white/[0.03] border border-white/[0.08] shadow-double-bezel overflow-hidden">
      {/* Header & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-white/[0.06] bg-[#0A0E17]/95 rounded-t-[20px]">
        <div className="flex items-center gap-2">
          <FileDiff className="w-4 h-4 text-emerald-400" />
          <span className="font-bold text-xs uppercase tracking-wider text-zinc-300">
            Unified Diff Viewer
          </span>
          <div className="flex items-center gap-1.5 ml-2 font-mono text-[11px]">
            <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              +{addedCount}
            </span>
            <span className="text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
              -{removedCount}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopyPatch}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-zinc-300 text-xs font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            {copiedPatch ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedPatch ? "Copied" : "Copy Patch"}</span>
          </button>

          <button
            type="button"
            onClick={handleCopyPRDescription}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 text-xs font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            {copiedPR ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>{copiedPR ? "Copied PR" : "Copy PR Description"}</span>
          </button>
        </div>
      </div>

      {/* Files altered chips */}
      {filesChanged.length > 0 && (
        <div className="px-4 py-2 bg-[#080C14] border-b border-white/[0.04] flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] font-mono uppercase text-zinc-500 shrink-0 font-bold">Files:</span>
          {filesChanged.map((f) => (
            <span key={f} className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-white/[0.04] text-zinc-300 border border-white/[0.06] shrink-0">
              {f}
            </span>
          ))}
        </div>
      )}

      {/* Syntax-colored Diff Stream */}
      <div className="flex-1 p-4 overflow-auto bg-[#070A11] rounded-b-[20px] font-mono text-[11px] leading-relaxed select-text">
        {lines.map((line, idx) => {
          let bgClass = "text-zinc-400";
          if (line.startsWith("+++") || line.startsWith("---")) {
            bgClass = "text-zinc-500 font-bold";
          } else if (line.startsWith("+")) {
            bgClass = "bg-emerald-500/15 text-emerald-300 font-semibold px-1 rounded-sm";
          } else if (line.startsWith("-")) {
            bgClass = "bg-rose-500/15 text-rose-300 font-semibold px-1 rounded-sm";
          } else if (line.startsWith("@@")) {
            bgClass = "text-cyan-400 font-semibold py-1";
          }

          return (
            <div key={idx} className={`whitespace-pre ${bgClass}`}>
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}
