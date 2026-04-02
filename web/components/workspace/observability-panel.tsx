"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  isApiClientError,
  listWorkspaceResearchAnalysisRunReviews,
  listWorkspaceTraces,
} from "../../lib/api";
import type {
  JsonObject,
  ResearchAnalysisReviewRecord,
  ResearchAnalysisReviewResponse,
  TraceRecord,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type ObservabilityPanelProps = {
  workspaceId: string;
};

type ToolStepRecord = {
  tool_name: string;
  summary: string;
  detail?: string | null;
};

function formatCost(value: number): string {
  return `$${value.toFixed(4)}`;
}

function readString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function readToolSteps(trace: TraceRecord): ToolStepRecord[] {
  const rawValue = trace.response_json["tool_steps"];
  if (!Array.isArray(rawValue)) {
    return [];
  }

  return rawValue.filter((item): item is ToolStepRecord => {
    if (!item || typeof item !== "object") {
      return false;
    }
    const candidate = item as Record<string, unknown>;
    return typeof candidate.tool_name === "string" && typeof candidate.summary === "string";
  });
}

function getPilotDegradedReason(trace: TraceRecord): string | null {
  return readString(trace.response_json["degraded_reason"]) ?? readString(trace.metadata_json["degraded_reason"]);
}

function getPilotOutcomeLabel(trace: TraceRecord): string {
  if (trace.error_message) {
    return "Pilot failed";
  }

  const degradedReason = getPilotDegradedReason(trace);
  if (degradedReason === "no_documents") {
    return "Degraded honestly: no documents";
  }
  if (degradedReason === "no_grounded_matches") {
    return "Degraded honestly: no grounded matches";
  }

  const sources = trace.response_json["sources"];
  if (Array.isArray(sources) && sources.length > 0) {
    return "Grounded evidence available";
  }

  return "Pilot completed";
}

function isPilotTrace(trace: TraceRecord): boolean {
  return trace.trace_type === "research_tool_assisted" || trace.trace_type === "research_tool_assisted_run";
}

function renderJson(payload: JsonObject): string {
  return JSON.stringify(payload, null, 2);
}

function formatReviewIssue(issue: string): string {
  switch (issue) {
    case "run_failed":
      return "Run ended in failed state";
    case "missing_trace_link":
      return "Trace link missing";
    case "invalid_trace_type":
      return "Trace type is not research_tool_assisted_run";
    case "missing_prompt":
      return "Prompt missing from trace metadata";
    case "missing_answer":
      return "Answer missing for non-failed run";
    case "missing_tool_steps":
      return "Tool steps are not visible";
    case "missing_run_memory":
      return "Compacted run memory is missing";
    case "missing_grounding_or_honest_degraded_reason":
      return "Neither grounded evidence nor honest degraded reason is visible";
    case "missing_resumed_memory_visibility":
      return "Resumed-memory linkage is not visible";
    default:
      return issue;
  }
}

function renderReviewCard(review: ResearchAnalysisReviewRecord) {
  return (
    <div
      key={review.run_id}
      style={{
        backgroundColor: "#ffffff",
        border: `1px solid ${review.passed ? "#bbf7d0" : "#fecaca"}`,
        borderRadius: 10,
        display: "grid",
        gap: 6,
        padding: 10,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "space-between" }}>
        <strong style={{ color: "#0f172a" }}>{review.question}</strong>
        <span style={{ color: review.passed ? "#166534" : "#b91c1c", fontSize: 13, fontWeight: 700 }}>
          {review.passed ? "Pass" : "Needs review"}
        </span>
      </div>
      <div style={{ color: "#475569", fontSize: 13 }}>
        Status: {review.status}
        {review.trace_id ? ` | Trace: ${review.trace_id}` : ""}
      </div>
      {review.resumed_from_run_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>Resumed from run: {review.resumed_from_run_id}</div>
      ) : null}
      {review.degraded_reason ? (
        <div style={{ color: "#475569", fontSize: 13 }}>Degraded reason: {review.degraded_reason}</div>
      ) : null}
      {review.run_memory_summary ? (
        <div style={{ color: "#334155" }}>
          <strong>Compacted memory:</strong> {review.run_memory_summary}
        </div>
      ) : null}
      {review.issues.length > 0 ? (
        <div style={{ display: "grid", gap: 4 }}>
          <strong style={{ color: "#0f172a" }}>Regression issues</strong>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {review.issues.map((issue) => (
              <li key={`${review.run_id}-${issue}`} style={{ color: "#475569" }}>
                {formatReviewIssue(issue)}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div style={{ color: "#166534" }}>All bounded regression checks passed for this run.</div>
      )}
    </div>
  );
}

export default function ObservabilityPanel({ workspaceId }: ObservabilityPanelProps) {
  const { session, isReady } = useAuthSession();
  const [traces, setTraces] = useState<TraceRecord[]>([]);
  const [review, setReview] = useState<ResearchAnalysisReviewResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadObservability = useCallback(async () => {
    if (!session) {
      setTraces([]);
      setReview(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [traceItems, reviewResponse] = await Promise.all([
        listWorkspaceTraces(session.accessToken, workspaceId, 20),
        listWorkspaceResearchAnalysisRunReviews(session.accessToken, workspaceId, 8),
      ]);
      setTraces(traceItems);
      setReview(reviewResponse);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load recent observability data.");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadObservability();
  }, [loadObservability]);

  const pilotTraces = useMemo(() => traces.filter(isPilotTrace), [traces]);
  const degradedPilotCount = useMemo(
    () => pilotTraces.filter((trace) => getPilotDegradedReason(trace) !== null).length,
    [pilotTraces],
  );

  if (!isReady) {
    return <SectionCard title="Observability">Loading recent traces...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in before reviewing workspace traces and evaluation signals." />;
  }

  return (
    <SectionCard
      title="Recent traces"
      description="Review the latest persisted chat, task, and bounded Research run traces for this workspace."
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
        <p style={{ color: "#475569", margin: 0 }}>This panel shows recent traces plus the bounded regression review for background Research runs.</p>
        <button onClick={() => void loadObservability()} type="button">
          {isLoading ? "Refreshing..." : "Refresh observability"}
        </button>
      </div>

      {review && review.reviewed_count > 0 ? (
        <section
          style={{
            backgroundColor: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: 14,
            display: "grid",
            gap: 8,
            marginBottom: 14,
            padding: 12,
          }}
        >
          <strong style={{ color: "#0f172a" }}>Research run regression review</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            Baseline {review.baseline_version} reviewed {review.reviewed_count} recent terminal runs. {review.passing_count} passed and {review.failing_count} need operator review.
          </p>
          <div style={{ display: "grid", gap: 8 }}>
            {review.items.map(renderReviewCard)}
          </div>
        </section>
      ) : null}

      {pilotTraces.length > 0 ? (
        <section
          style={{
            backgroundColor: "#f8fafc",
            border: "1px solid #dbe4f0",
            borderRadius: 14,
            display: "grid",
            gap: 6,
            marginBottom: 14,
            padding: 12,
          }}
        >
          <strong style={{ color: "#0f172a" }}>Research tool-assisted pilot review</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            The latest {pilotTraces.length} pilot traces include {degradedPilotCount} honest degraded paths. You should be able to see the analysis focus, search query, tool steps, and degradation reason without opening raw JSON first.
          </p>
        </section>
      ) : null}

      {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      {!isLoading && traces.length === 0 ? <p>No traces have been recorded for this workspace yet.</p> : null}

      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {traces.map((trace) => {
          const analysisFocus = readString(trace.response_json["analysis_focus"]) ?? readString(trace.metadata_json["analysis_focus"]);
          const searchQuery = readString(trace.response_json["search_query"]) ?? readString(trace.metadata_json["search_query"]);
          const toolSteps = readToolSteps(trace);
          const degradedReason = getPilotDegradedReason(trace);
          const resumedFromRunId = readString(trace.response_json["resumed_from_run_id"]) ?? readString(trace.metadata_json["resumed_from_run_id"]);
          const runMemory = (trace.response_json["run_memory"] ?? trace.metadata_json["run_memory"]) as JsonObject | undefined;
          const runMemorySummary = runMemory ? readString(runMemory["summary"]) : null;
          const runMemoryNextStep = runMemory ? readString(runMemory["recommended_next_step"]) : null;

          return (
            <li
              key={trace.id}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                marginBottom: 12,
                padding: 12,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 8 }}>
                <strong>{trace.trace_type}</strong>
                <span>{new Date(trace.created_at).toLocaleString()}</span>
              </div>
              <div>Trace id: {trace.id}</div>
              <div>Latency: {trace.latency_ms} ms</div>
              <div>
                Tokens: input {trace.token_input} / output {trace.token_output}
              </div>
              <div>Estimated cost: {formatCost(trace.estimated_cost)}</div>
              {trace.task_id ? <div>Task id: {trace.task_id}</div> : null}
              {trace.agent_run_id ? <div>Agent run id: {trace.agent_run_id}</div> : null}
              {trace.tool_call_id ? <div>Tool call id: {trace.tool_call_id}</div> : null}
              {trace.eval_run_id ? <div>Eval run id: {trace.eval_run_id}</div> : null}
              {trace.parent_trace_id ? <div>Parent trace id: {trace.parent_trace_id}</div> : null}
              {trace.error_message ? (
                <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 8 }}>
                  <strong>Error:</strong> {trace.error_message}
                </p>
              ) : null}

              {isPilotTrace(trace) ? (
                <section
                  style={{
                    backgroundColor: "#f8fafc",
                    border: "1px solid #dbe4f0",
                    borderRadius: 12,
                    display: "grid",
                    gap: 10,
                    marginTop: 12,
                    padding: 12,
                  }}
                >
                  <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <strong style={{ color: "#0f172a" }}>Pilot visibility</strong>
                    <span style={{ color: "#475569", fontSize: 13 }}>{getPilotOutcomeLabel(trace)}</span>
                  </div>
                  {analysisFocus ? (
                    <div>
                      <strong>Analysis focus:</strong> {analysisFocus}
                    </div>
                  ) : null}
                  {searchQuery ? (
                    <div>
                      <strong>Search query:</strong> {searchQuery}
                    </div>
                  ) : null}
                  {degradedReason ? (
                    <div>
                      <strong>Degraded reason:</strong> {degradedReason}
                    </div>
                  ) : null}
                  {resumedFromRunId ? (
                    <div>
                      <strong>Resumed from run:</strong> {resumedFromRunId}
                    </div>
                  ) : null}
                  {runMemorySummary ? (
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong>Compacted run memory</strong>
                      <div>{runMemorySummary}</div>
                      {runMemoryNextStep ? <div style={{ color: "#64748b" }}>Next step: {runMemoryNextStep}</div> : null}
                    </div>
                  ) : null}
                  {toolSteps.length > 0 ? (
                    <div style={{ display: "grid", gap: 8 }}>
                      <strong>Tool steps</strong>
                      {toolSteps.map((step, index) => (
                        <div
                          key={`${trace.id}-${step.tool_name}-${index}`}
                          style={{
                            backgroundColor: "#ffffff",
                            border: "1px solid #dbe4f0",
                            borderRadius: 10,
                            display: "grid",
                            gap: 4,
                            padding: 10,
                          }}
                        >
                          <div style={{ color: "#0f172a", fontWeight: 700 }}>{step.tool_name}</div>
                          <div style={{ color: "#334155" }}>{step.summary}</div>
                          {step.detail ? <div style={{ color: "#64748b", fontSize: 13 }}>{step.detail}</div> : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: "#64748b" }}>This pilot trace did not record any visible tool steps.</div>
                  )}
                </section>
              ) : null}

              <details style={{ marginTop: 10 }}>
                <summary>Trace payload</summary>
                <pre style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
                  {renderJson({
                    request_json: trace.request_json,
                    response_json: trace.response_json,
                    metadata_json: trace.metadata_json,
                  })}
                </pre>
              </details>
            </li>
          );
        })}
      </ul>
    </SectionCard>
  );
}
