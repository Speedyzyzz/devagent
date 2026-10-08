"use client";

import { useEffect, useState, useRef } from "react";
import { getStreamUrl, getSession } from "@/lib/api";
import { SessionState, SessionStatus, TimelineStep } from "@/lib/types";

export function useAgentStream(sessionId: string | null) {
  const [session, setSession] = useState<SessionState | null>(null);
  const [timeline, setTimeline] = useState<TimelineStep[]>([]);
  const [activeDiff, setActiveDiff] = useState<string | null>(null);
  const [rootCauseReport, setRootCauseReport] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isDone, setIsDone] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setSession(null);
      setTimeline([]);
      setActiveDiff(null);
      setRootCauseReport(null);
      setIsConnected(false);
      setIsDone(false);
      return;
    }

    // Fetch initial state
    getSession(sessionId)
      .then((s) => {
        setSession(s);
        if (s.final_diff) setActiveDiff(s.final_diff);
        if (s.root_cause) setRootCauseReport(s.root_cause);
      })
      .catch((err) => console.error("Initial session fetch error:", err));

    const streamUrl = getStreamUrl(sessionId);
    const es = new EventSource(streamUrl);
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
    };

    es.onerror = () => {
      setIsConnected(false);
    };

    const handleMessage = (event: MessageEvent) => {
      try {
        const payload = JSON.parse(event.data);
        const { type, step: stepNum, timestamp, data } = payload;

        setTimeline((prev) => {
          const updated = [...prev];
          let currentStep = updated.find((s) => s.step === stepNum);

          if (!currentStep) {
            currentStep = {
              step: stepNum || updated.length + 1,
              timestamp: timestamp || new Date().toISOString(),
              title: `Step ${stepNum || updated.length + 1}`,
              toolCalls: [],
              status: "running",
            };
            updated.push(currentStep);
          }

          if (type === "agent.telemetry") {
            currentStep.telemetry = {
              investigation: data.investigation,
              hypothesis: data.hypothesis,
              action_plan: data.action_plan,
            };
          } else if (type === "tool.called") {
            currentStep.toolCalls.push({
              id: data.call_id,
              name: data.tool,
              arguments: data.arguments,
            });
          } else if (type === "tool.completed") {
            const tc = currentStep.toolCalls.find((c) => c.name === data.tool);
            if (tc) {
              tc.result = data.result;
              tc.success = true;
            }
          } else if (type === "tool.failed") {
            const tc = currentStep.toolCalls.find((c) => c.name === data.tool);
            if (tc) {
              tc.error = data.error;
              tc.success = false;
            }
          } else if (type === "patch.created") {
            currentStep.diff = data.diff;
            setActiveDiff(data.diff);
            setSession((s) =>
              s
                ? {
                    ...s,
                    files_changed: Array.from(new Set([...s.files_changed, data.file])),
                    final_diff: data.diff,
                  }
                : null
            );
          } else if (type === "verification.completed") {
            currentStep.verification = {
              passed: data.passed,
              stdout: data.stdout,
              exit_code: data.exit_code,
              duration: data.duration,
            };
          } else if (type === "agent.completed") {
            currentStep.status = "completed";
            setIsDone(true);
            if (data.final_diff) setActiveDiff(data.final_diff);
            if (data.root_cause) setRootCauseReport(data.root_cause);
            setSession((s) => (s ? { ...s, status: "COMPLETED" as SessionStatus, root_cause: data.root_cause } : null));
            es.close();
          } else if (type === "agent.failed") {
            currentStep.status = "failed";
            setIsDone(true);
            setSession((s) => (s ? { ...s, status: "FAILED" as SessionStatus, error: data.reason } : null));
            es.close();
          } else if (type === "agent.cancelled") {
            currentStep.status = "failed";
            setIsDone(true);
            setSession((s) => (s ? { ...s, status: "CANCELLED" as SessionStatus } : null));
            es.close();
          }

          return updated;
        });
      } catch (err) {
        console.error("SSE message parsing error:", err);
      }
    };

    // Listen to custom SSE event types
    const eventTypes = [
      "agent.started",
      "agent.step.started",
      "agent.telemetry",
      "tool.called",
      "tool.completed",
      "tool.failed",
      "patch.created",
      "verification.started",
      "verification.completed",
      "agent.completed",
      "agent.failed",
      "agent.cancelled",
    ];

    eventTypes.forEach((et) => {
      es.addEventListener(et, handleMessage);
    });

    return () => {
      es.close();
    };
  }, [sessionId]);

  return {
    session,
    timeline,
    activeDiff,
    rootCauseReport,
    isConnected,
    isDone,
  };
}
