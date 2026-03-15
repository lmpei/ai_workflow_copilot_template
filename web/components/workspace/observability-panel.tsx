"use client";

import { useCallback, useEffect, useState } from "react";

import { isApiClientError, listWorkspaceTraces } from "../../lib/api";
import type { TraceRecord } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type ObservabilityPanelProps = {
  workspaceId: string;
};

function formatCost(value: number): string {
  return `$${value.toFixed(4)}`;
}

export default function ObservabilityPanel({ workspaceId }: ObservabilityPanelProps) {
  const { session, isReady } = useAuthSession();
  const [traces, setTraces] = useState<TraceRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadTraces = useCallback(async () => {
    if (!session) {
      setTraces([]);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      setTraces(await listWorkspaceTraces(session.accessToken, workspaceId, 20));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load traces");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadTraces();
  }, [loadTraces]);

  if (!isReady) {
    return <SectionCard title="Observability">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to inspect workspace traces and eval execution signals." />;
  }

  return (
    <SectionCard
      title="Recent traces"
      description="Inspect the latest persisted traces for chat, task, agent, tool, and eval execution."
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
        <p style={{ margin: 0, color: "#475569" }}>Showing up to 20 most recent traces for this workspace.</p>
        <button onClick={() => void loadTraces()} type="button">
          {isLoading ? "Refreshing..." : "Refresh traces"}
        </button>
      </div>
      {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      {!isLoading && traces.length === 0 ? <p>No traces recorded yet.</p> : null}
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {traces.map((trace) => (
          <li
            key={trace.id}
            style={{
              border: "1px solid #cbd5e1",
              borderRadius: 12,
              marginBottom: 12,
              padding: 12,
            }}
          >
            <div style={{ alignItems: "center", display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 8 }}>
              <strong>{trace.trace_type}</strong>
              <span>{new Date(trace.created_at).toLocaleString()}</span>
            </div>
            <div>Trace ID: {trace.id}</div>
            <div>Latency: {trace.latency_ms} ms</div>
            <div>
              Tokens: {trace.token_input} in / {trace.token_output} out
            </div>
            <div>Estimated cost: {formatCost(trace.estimated_cost)}</div>
            {trace.task_id ? <div>Task ID: {trace.task_id}</div> : null}
            {trace.agent_run_id ? <div>Agent run ID: {trace.agent_run_id}</div> : null}
            {trace.tool_call_id ? <div>Tool call ID: {trace.tool_call_id}</div> : null}
            {trace.eval_run_id ? <div>Eval run ID: {trace.eval_run_id}</div> : null}
            {trace.parent_trace_id ? <div>Parent trace ID: {trace.parent_trace_id}</div> : null}
            {trace.error_message ? (
              <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 8 }}>
                <strong>Error:</strong> {trace.error_message}
              </p>
            ) : null}
            <details style={{ marginTop: 10 }}>
              <summary>Trace payload</summary>
              <pre style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
                {JSON.stringify(
                  {
                    request_json: trace.request_json,
                    response_json: trace.response_json,
                    metadata_json: trace.metadata_json,
                  },
                  null,
                  2,
                )}
              </pre>
            </details>
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}
