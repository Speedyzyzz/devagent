"use client";

import React, { useState, useEffect } from "react";
import { createSession, cancelSession, getBenchmarkCases } from "@/lib/api";
import { BenchmarkCase } from "@/lib/types";
import { useAgentStream } from "@/hooks/use-agent-stream";
import { SessionStatusBadge } from "@/components/session-status";
import { IssueInput } from "@/components/issue-input";
import { AgentTerminal } from "@/components/agent-terminal";
import { DiffViewer } from "@/components/diff-viewer";
import { RootCauseReport } from "@/components/root-cause-report";
import { BenchmarkStatsModal } from "@/components/benchmark-stats-modal";

export default function Home() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [benchmarkCases, setBenchmarkCases] = useState<BenchmarkCase[]>([]);
  const [isStarting, setIsStarting] = useState(false);
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false);

  // Hook into live SSE telemetry
  const { session, timeline, activeDiff, rootCauseReport, isConnected, isDone } =
    useAgentStream(activeSessionId);

  // Load benchmark suite cases on mount
  useEffect(() => {
    getBenchmarkCases()
      .then(setBenchmarkCases)
      .catch((err) => {
        console.warn("Could not fetch benchmark cases directly, using fallbacks:", err);
        setBenchmarkCases([
          {
            id: "case_001_guest_session",
            name: "Guest Checkout Session Expiry 401",
            issue: "Users receive a 401 error when checking out after their guest session expires. Fallback to create_anonymous_session().",
            verification: { runner: "pytest", args: ["tests/test_auth.py"] },
          },
          {
            id: "case_002_cart_tax",
            name: "Cart Total Tax Calculation Omission",
            issue: "Cart total formula omits sales tax. Net subtotal (subtotal - discount) must apply tax_rate and be added to final total.",
            verification: { runner: "pytest", args: ["tests/test_cart.py"] },
          },
          {
            id: "case_003_catalog_pagination",
            name: "Catalog Pagination Off-By-One Truncation",
            issue: "Pagination returns 4 items instead of 5 for a page_size of 5. Correct the slice index.",
            verification: { runner: "pytest", args: ["tests/test_catalog.py"] },
          },
          {
            id: "case_004_user_null_name",
            name: "User Null Display Name AttributeError",
            issue: "format_user_header crashes with AttributeError when display_name is None. Fall back to ANONYMOUS.",
            verification: { runner: "pytest", args: ["tests/test_users.py"] },
          },
          {
            id: "case_005_cart_creation_status",
            name: "Cart Creation Endpoint 404 Status Bug",
            issue: "create_cart_endpoint returns HTTP status code 404 instead of 201 Created.",
            verification: { runner: "pytest", args: ["tests/test_api_cart.py"] },
          },
        ]);
      });
  }, []);

  const handleStartSession = async (payload: {
    issue: string;
    verification_instruction?: string;
    provider: string;
    case_id?: string;
  }) => {
    setIsStarting(true);
    try {
      const resp = await createSession(payload);
      setActiveSessionId(resp.session_id);
    } catch (err) {
      console.error("Failed to start session:", err);
      alert("Error starting agent session. Ensure backend is running at http://localhost:8000");
    } finally {
      setIsStarting(false);
    }
  };

  const handleCancelSession = async () => {
    if (!activeSessionId) return;
    try {
      await cancelSession(activeSessionId);
    } catch (err) {
      console.error("Failed to cancel session:", err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas text-zinc-100">
      {/* Top Telemetry Header */}
      <SessionStatusBadge
        session={session}
        onCancel={handleCancelSession}
        onOpenBenchmarkStats={() => setShowBenchmarkModal(true)}
      />

      {/* Main Container */}
      <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1680px] w-full mx-auto space-y-6">
        {/* Top Control Section: Issue input & presets */}
        <section>
          <IssueInput
            benchmarkCases={benchmarkCases}
            onSubmit={handleStartSession}
            isLoading={isStarting || (session?.status !== undefined && !isDone && session.status !== "FAILED" && session.status !== "COMPLETED")}
          />
        </section>

        {/* 3-Zone Mission Control Layout */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[680px]">
          {/* Left Zone (5 Cols): Agent Terminal & Step-by-Step Timeline */}
          <div className="lg:col-span-5 h-[680px]">
            <AgentTerminal
              timeline={timeline}
              isConnected={isConnected}
              isDone={isDone}
            />
          </div>

          {/* Right Zone (7 Cols): Root Cause Report & Interactive Diff Viewer */}
          <div className="lg:col-span-7 flex flex-col gap-6 h-[680px]">
            {/* Top Right: Root Cause Analysis */}
            <div className="h-[280px]">
              <RootCauseReport
                report={rootCauseReport}
                error={session?.error}
                status={session?.status || "CREATED"}
              />
            </div>

            {/* Bottom Right: Interactive Diff Viewer */}
            <div className="flex-1 min-h-[360px]">
              <DiffViewer
                diff={activeDiff}
                filesChanged={session?.files_changed || []}
                rootCause={rootCauseReport}
              />
            </div>
          </div>
        </section>
      </main>

      {/* Benchmark Stats Modal */}
      <BenchmarkStatsModal
        isOpen={showBenchmarkModal}
        onClose={() => setShowBenchmarkModal(false)}
      />
    </div>
  );
}
