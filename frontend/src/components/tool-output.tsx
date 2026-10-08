"use client";

import React, { useState } from "react";
import { ToolCallItem } from "@/lib/types";
import { ChevronRight, ChevronDown, Check, X, Terminal, Search, Folder, FileCode, Play } from "lucide-react";

interface ToolOutputProps {
  toolCall: ToolCallItem;
}

export function ToolOutput({ toolCall }: ToolOutputProps) {
  const [isOpen, setIsOpen] = useState(false);

  const getToolIcon = () => {
    switch (toolCall.name) {
      case "list_directory":
        return <Folder className="w-3.5 h-3.5 text-blue-400" />;
      case "search_code":
        return <Search className="w-3.5 h-3.5 text-amber-400" />;
      case "read_file_lines":
        return <FileCode className="w-3.5 h-3.5 text-emerald-400" />;
      case "apply_patch":
        return <Terminal className="w-3.5 h-3.5 text-purple-400" />;
      case "execute_verification":
        return <Play className="w-3.5 h-3.5 text-cyan-400" />;
      default:
        return <Terminal className="w-3.5 h-3.5 text-zinc-400" />;
    }
  };

  const getArgumentSummary = () => {
    const args = toolCall.arguments || {};
    if (toolCall.name === "search_code") return `"${args.query}"`;
    if (toolCall.name === "read_file_lines") return `${args.path}:${args.start_line}-${args.end_line}`;
    if (toolCall.name === "apply_patch") return `${args.path}`;
    if (toolCall.name === "execute_verification") return `${args.runner} ${(args.args || []).join(" ")}`;
    if (toolCall.name === "list_directory") return `path="${args.path || "."}"`;
    return JSON.stringify(args);
  };

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden my-1.5 transition-all">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-2.5 text-left hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          {isOpen ? (
            <ChevronDown className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
          )}
          <div className="p-1 rounded-md bg-white/[0.04] border border-white/[0.06]">
            {getToolIcon()}
          </div>
          <span className="font-mono text-xs font-bold text-zinc-200">{toolCall.name}</span>
          <span className="font-mono text-[11px] text-zinc-400 truncate">
            {getArgumentSummary()}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0 ml-2">
          {toolCall.success === true && (
            <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <Check className="w-3 h-3" />
              <span>OK</span>
            </span>
          )}
          {toolCall.success === false && (
            <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
              <X className="w-3 h-3" />
              <span>ERR</span>
            </span>
          )}
        </div>
      </button>

      {isOpen && (
        <div className="p-3 bg-[#070A11]/90 border-t border-white/[0.04] space-y-2 font-mono text-[11px]">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">Arguments</span>
            <pre className="p-2 rounded-lg bg-black/40 border border-white/[0.04] text-zinc-300 overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(toolCall.arguments, null, 2)}
            </pre>
          </div>

          {toolCall.result && (
            <div>
              <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1">Result</span>
              <pre className="p-2 rounded-lg bg-black/40 border border-white/[0.04] text-zinc-300 overflow-x-auto whitespace-pre-wrap max-h-60 overflow-y-auto">
                {JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}

          {toolCall.error && (
            <div>
              <span className="text-[10px] uppercase font-bold text-rose-400 block mb-1">Error</span>
              <pre className="p-2 rounded-lg bg-rose-950/30 border border-rose-500/20 text-rose-300 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(toolCall.error, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
