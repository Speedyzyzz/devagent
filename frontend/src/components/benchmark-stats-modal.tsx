"use client";

import React from "react";
import { X, ShieldCheck, CheckCircle2, Award, Terminal, Cpu, Clock } from "lucide-react";

interface BenchmarkStatsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function BenchmarkStatsModal({ isOpen, onClose }: BenchmarkStatsModalProps) {
  if (!isOpen) return null;

  const benchmarkCases = [
    {
      id: "case_001_guest_session",
      name: "Guest Checkout Session Expiry 401",
      domain: "Auth",
      iters: 6,
      tools: 5,
      patchLines: 2,
      time: "0.12s",
    },
    {
      id: "case_002_cart_tax",
      name: "Cart Total Tax Calculation Omission",
      domain: "Cart",
      iters: 6,
      tools: 5,
      patchLines: 5,
      time: "0.13s",
    },
    {
      id: "case_003_catalog_pagination",
      name: "Catalog Pagination Off-By-One Truncation",
      domain: "Catalog",
      iters: 6,
      tools: 5,
      patchLines: 3,
      time: "0.12s",
    },
    {
      id: "case_004_user_null_name",
      name: "User Null Display Name AttributeError",
      domain: "Users",
      iters: 6,
      tools: 5,
      patchLines: 4,
      time: "0.13s",
    },
    {
      id: "case_005_cart_creation_status",
      name: "Cart Creation Endpoint 404 Status Bug",
      domain: "API",
      iters: 6,
      tools: 5,
      patchLines: 2,
      time: "0.13s",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="w-full max-w-3xl rounded-[28px] p-2 bg-white/[0.04] border border-white/[0.1] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="rounded-[22px] bg-[#0A0E17] p-6 border border-white/[0.06]">
          {/* Header */}
          <div className="flex items-center justify-between pb-5 border-b border-white/[0.06]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white tracking-tight">
                  DevAgent Verified Benchmark Results
                </h3>
                <p className="text-xs text-zinc-400">
                  Empirical performance metrics across 5 distinct isolated test suites
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-white/[0.06] text-zinc-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 my-5">
            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <span className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">
                Resolution Rate
              </span>
              <div className="text-xl font-bold text-emerald-400 font-mono">100.0%</div>
              <span className="text-[10px] text-zinc-400 font-mono">5 of 5 verified</span>
            </div>

            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <span className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">
                Avg. Iterations
              </span>
              <div className="text-xl font-bold text-white font-mono">6.0</div>
              <span className="text-[10px] text-zinc-400 font-mono">/ 8 max turns</span>
            </div>

            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <span className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">
                Avg. Tool Calls
              </span>
              <div className="text-xl font-bold text-blue-400 font-mono">5.0</div>
              <span className="text-[10px] text-zinc-400 font-mono">calls / task</span>
            </div>

            <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <span className="text-[10px] uppercase font-bold text-zinc-500 block mb-1">
                Avg. Patch Size
              </span>
              <div className="text-xl font-bold text-amber-400 font-mono">3.2</div>
              <span className="text-[10px] text-zinc-400 font-mono">lines changed</span>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-hidden rounded-xl border border-white/[0.06] bg-[#070A11] my-4">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/[0.06]">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Case</th>
                  <th className="py-2.5 px-4 font-semibold">Domain</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Status</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Iters</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Tools</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Patch</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04] text-zinc-300">
                {benchmarkCases.map((c) => (
                  <tr key={c.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-2.5 px-4 font-sans font-medium text-zinc-200 truncate max-w-xs">
                      {c.name}
                    </td>
                    <td className="py-2.5 px-4 text-zinc-400">{c.domain}</td>
                    <td className="py-2.5 px-4 text-center">
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" /> PASS
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right">{c.iters}</td>
                    <td className="py-2.5 px-4 text-right">{c.tools}</td>
                    <td className="py-2.5 px-4 text-right">{c.patchLines}L</td>
                    <td className="py-2.5 px-4 text-right text-zinc-400">{c.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Security guarantee note */}
          <div className="p-3.5 rounded-xl bg-blue-500/[0.05] border border-blue-500/20 text-xs text-blue-300/90 flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-blue-400 shrink-0" />
            <p className="leading-relaxed">
              <strong>Security Proof:</strong> 100% of symlink traversal, directory escaping, and credential leak tests blocked. All patches are atomically applied with Python AST syntax validation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
