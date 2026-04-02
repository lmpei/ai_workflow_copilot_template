"use client";

import { useEffect, useMemo, useState } from "react";

import {
  createWorkspaceResearchAnalysisRun,
  getResearchAnalysisRun,
  isApiClientError,
  listWorkspaceResearchAnalysisRuns,
  sendWorkspaceChat,
} from "../../lib/api";
import type {
  ChatSource,
  ChatToolStep,
  ResearchAnalysisRunRecord,
  ResearchAnalysisRunStatus,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type ChatPanelProps = {
  workspaceId: string;
  assistantLabel?: string;
  workflowLabel?: string;
  introTitle?: string;
  introBody?: string;
  placeholder?: string;
  suggestedPrompts?: string[];
  primaryActionLabel?: string;
  outputTitle?: string;
  modes?: Array<{
    value: "rag" | "research_tool_assisted";
    label: string;
    description: string;
  }>;
  supportsBackgroundRuns?: boolean;
  onStatusChange?: (status: {
    entryCount: number;
    isSubmitting: boolean;
    currentDraft: string;
    lastTraceId: string | null;
    latestAnalysisRunId: string | null;
    latestAnalysisRunStatus: ResearchAnalysisRunStatus | null;
    latestAnalysisRunQuestion: string | null;
  }) => void;
};

type ChatEntry = {
  question: string;
  answer: string;
  traceId: string;
  mode: "rag" | "research_tool_assisted";
  toolSteps: ChatToolStep[];
  sources: ChatSource[];
};

const RUN_TERMINAL_STATUSES: ResearchAnalysisRunStatus[] = ["completed", "degraded", "failed"];
const RUN_ACTIVE_STATUSES: ResearchAnalysisRunStatus[] = ["pending", "running"];

function PromptCard({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        backgroundColor: active ? "#0f172a" : isHovered ? "#eff6ff" : "#ffffff",
        border: `1px solid ${active ? "#0f172a" : isHovered ? "#60a5fa" : "#cbd5e1"}`,
        borderRadius: 16,
        color: active ? "#f8fafc" : "#0f172a",
        cursor: "pointer",
        display: "grid",
        fontWeight: 700,
        justifyItems: "start",
        minHeight: 60,
        padding: 12,
        textAlign: "left",
        transition: "all 160ms ease",
      }}
      type="button"
    >
      <span style={{ lineHeight: 1.45 }}>{label}</span>
    </button>
  );
}

function StatusBadge({ status }: { status: ResearchAnalysisRunStatus }) {
  const palette: Record<ResearchAnalysisRunStatus, { label: string; color: string; background: string }> = {
    pending: { label: "Queued", color: "#92400e", background: "#fef3c7" },
    running: { label: "Running", color: "#1d4ed8", background: "#dbeafe" },
    completed: { label: "Completed", color: "#166534", background: "#dcfce7" },
    degraded: { label: "Degraded", color: "#7c2d12", background: "#ffedd5" },
    failed: { label: "Failed", color: "#b91c1c", background: "#fee2e2" },
  };
  const token = palette[status];
  return (
    <span
      style={{
        backgroundColor: token.background,
        borderRadius: 999,
        color: token.color,
        display: "inline-flex",
        fontSize: 12,
        fontWeight: 800,
        minHeight: 28,
        padding: "0 10px",
        alignItems: "center",
      }}
    >
      {token.label}
    </span>
  );
}

function ToolSteps({ toolSteps }: { toolSteps: ChatToolStep[] }) {
  if (toolSteps.length === 0) {
    return null;
  }

  return (
    <section
      style={{
        backgroundColor: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: 14,
        display: "grid",
        gap: 10,
        marginTop: 12,
        padding: 12,
      }}
    >
      <strong style={{ color: "#0f172a", fontSize: 14 }}>Tool steps in this pass</strong>
      <div style={{ display: "grid", gap: 8 }}>
        {toolSteps.map((step, index) => (
          <div
            key={`${step.tool_name}-${index}`}
            style={{
              backgroundColor: "#ffffff",
              border: "1px solid #dbe4f0",
              borderRadius: 12,
              display: "grid",
              gap: 4,
              padding: 10,
            }}
          >
            <div style={{ color: "#0f172a", fontSize: 13, fontWeight: 700 }}>{step.summary}</div>
            {step.detail ? <div style={{ color: "#475569", fontSize: 13 }}>{step.detail}</div> : null}
          </div>
        ))}
      </div>
    </section>
  );
}

function SourceList({ sources, traceId }: { sources: ChatSource[]; traceId: string | null }) {
  return (
    <details style={{ marginTop: 12 }}>
      <summary>View grounded sources</summary>
      {sources.length === 0 ? (
        <p style={{ color: "#64748b", marginBottom: 0 }}>No grounded sources were returned for this pass.</p>
      ) : (
        <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
          {sources.map((source) => (
            <div
              key={`${traceId ?? "run"}-${source.chunk_id}`}
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: 14,
                display: "grid",
                gap: 6,
                padding: 12,
              }}
            >
              <strong>{source.document_title}</strong>
              <div style={{ color: "#475569", fontSize: 13 }}>
                Chunk {source.chunk_index} / Document {source.document_id}
              </div>
              <div style={{ color: "#334155", lineHeight: 1.7 }}>{source.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </details>
  );
}

function ChatBubble({ assistantLabel, entry }: { assistantLabel: string; entry: ChatEntry }) {
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: "20px 20px 8px 20px",
            color: "#f8fafc",
            maxWidth: "min(720px, 100%)",
            padding: "16px 18px",
          }}
        >
          <div style={{ color: "#cbd5e1", fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Your question</div>
          <div style={{ lineHeight: 1.75, whiteSpace: "pre-wrap" }}>{entry.question}</div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-start" }}>
        <div
          style={{
            backgroundColor: "#ffffff",
            border: "1px solid #dbe4f0",
            borderRadius: "20px 20px 20px 8px",
            boxShadow: "0 18px 40px rgba(15, 23, 42, 0.06)",
            maxWidth: "min(860px, 100%)",
            padding: "18px 20px",
          }}
        >
          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
            <span
              style={{
                backgroundColor: "#e0f2fe",
                borderRadius: 999,
                color: "#0c4a6e",
                fontSize: 12,
                fontWeight: 700,
                padding: "4px 10px",
              }}
            >
              {assistantLabel}
            </span>
            {entry.mode === "research_tool_assisted" ? (
              <span
                style={{
                  backgroundColor: "#ecfccb",
                  borderRadius: 999,
                  color: "#3f6212",
                  fontSize: 12,
                  fontWeight: 700,
                  padding: "4px 10px",
                }}
              >
                Tool-assisted pilot
              </span>
            ) : null}
            <span style={{ color: "#64748b", fontSize: 12 }}>Trace ID: {entry.traceId}</span>
          </div>
          <div style={{ color: "#1e293b", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>{entry.answer}</div>
          <ToolSteps toolSteps={entry.toolSteps} />
          <SourceList sources={entry.sources} traceId={entry.traceId} />
        </div>
      </div>
    </div>
  );
}

function AnalysisRunCard({ run }: { run: ResearchAnalysisRunRecord }) {
  const outcomeCopy: Record<ResearchAnalysisRunStatus, string> = {
    pending: "The run has been queued and will start shortly.",
    running: "The assistant is reading connected material, planning the next step, and synthesizing a result.",
    completed: "The bounded analysis pass completed successfully.",
    degraded: "The pass completed honestly, but the evidence path was weak and has been called out.",
    failed: "The background analysis run failed before it could complete.",
  };

  return (
    <section
      style={{
        backgroundColor: "#ffffff",
        border: "1px solid #dbe4f0",
        borderRadius: 20,
        boxShadow: "0 18px 40px rgba(15, 23, 42, 0.06)",
        display: "grid",
        gap: 14,
        padding: 18,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "space-between" }}>
        <div style={{ display: "grid", gap: 4 }}>
          <span style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
            Background analysis run
          </span>
          <strong style={{ color: "#0f172a", lineHeight: 1.6 }}>{run.question}</strong>
        </div>
        <StatusBadge status={run.status} />
      </div>

      <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{outcomeCopy[run.status]}</p>

      <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
        <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
          <span style={{ color: "#64748b", fontSize: 12 }}>Analysis focus</span>
          <strong style={{ color: "#0f172a" }}>{run.analysis_focus ?? "Waiting for the planner to set focus"}</strong>
        </div>
        <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
          <span style={{ color: "#64748b", fontSize: 12 }}>Search query</span>
          <strong style={{ color: "#0f172a" }}>{run.search_query ?? "Not available yet"}</strong>
        </div>
      </div>

      {run.resumed_from_run_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          Resumed from run: <strong style={{ color: "#0f172a" }}>{run.resumed_from_run_id}</strong>
        </div>
      ) : null}

      {run.run_memory ? (
        <section
          style={{
            backgroundColor: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: 16,
            display: "grid",
            gap: 8,
            padding: 14,
          }}
        >
          <strong style={{ color: "#0f172a" }}>Compacted run memory</strong>
          <div style={{ color: "#334155", lineHeight: 1.7 }}>{run.run_memory.summary}</div>
          <div style={{ color: "#475569", fontSize: 13 }}>
            Evidence state: <strong style={{ color: "#0f172a" }}>{run.run_memory.evidence_state}</strong>
          </div>
          <div style={{ color: "#475569", fontSize: 13 }}>
            Recommended next step: {run.run_memory.recommended_next_step}
          </div>
          {run.run_memory.source_titles.length > 0 ? (
            <div style={{ color: "#475569", fontSize: 13 }}>
              Source titles carried forward: {run.run_memory.source_titles.join(", ")}
            </div>
          ) : null}
        </section>
      ) : null}

      {run.trace_id ? <div style={{ color: "#64748b", fontSize: 13 }}>Trace ID: {run.trace_id}</div> : null}
      {run.degraded_reason ? <div style={{ color: "#9a3412", fontSize: 13 }}>Degraded reason: {run.degraded_reason}</div> : null}
      {run.error_message ? <div style={{ color: "#b91c1c", fontSize: 13 }}>Error: {run.error_message}</div> : null}

      {run.answer ? (
        <div
          style={{
            backgroundColor: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: 16,
            color: "#1e293b",
            lineHeight: 1.8,
            padding: 14,
            whiteSpace: "pre-wrap",
          }}
        >
          {run.answer}
        </div>
      ) : null}

      <ToolSteps toolSteps={run.tool_steps} />
      <SourceList sources={run.sources} traceId={run.trace_id ?? null} />
    </section>
  );
}

function mergeRuns(
  currentRuns: ResearchAnalysisRunRecord[],
  incomingRuns: ResearchAnalysisRunRecord[],
): ResearchAnalysisRunRecord[] {
  const byId = new Map<string, ResearchAnalysisRunRecord>();
  [...currentRuns, ...incomingRuns].forEach((run) => {
    byId.set(run.id, run);
  });
  return [...byId.values()].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

export default function ChatPanel({
  workspaceId,
  assistantLabel = "Research Assistant",
  workflowLabel = "Research workflow",
  introTitle = "Start from one research question",
  introBody = "Pick one prompt or type your own question, then start the analysis.",
  placeholder = "For example: summarize the strongest market signals in the current material and tell me what evidence is still missing before we can make a formal conclusion.",
  suggestedPrompts,
  primaryActionLabel = "Start analysis",
  outputTitle = "Analysis flow and conclusions",
  modes,
  supportsBackgroundRuns = false,
  onStatusChange,
}: ChatPanelProps) {
  const { session, isReady } = useAuthSession();
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [analysisRuns, setAnalysisRuns] = useState<ResearchAnalysisRunRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const availableModes = useMemo(
    () =>
      modes && modes.length > 0
        ? modes
        : [{ value: "rag" as const, label: "Standard analysis", description: "Use the current material directly for one grounded analysis pass." }],
    [modes],
  );
  const [mode, setMode] = useState<"rag" | "research_tool_assisted">(availableModes[0]?.value ?? "rag");

  const prompts = useMemo(
    () =>
      suggestedPrompts && suggestedPrompts.length > 0
        ? suggestedPrompts
        : [
            "Summarize the most important findings in the current material.",
            "Tell me which missing material would unblock the next research step.",
            "Point out which conclusions are still weak and need more verification.",
          ],
    [suggestedPrompts],
  );

  const modeMeta = useMemo(
    () => availableModes.find((candidate) => candidate.value === mode) ?? availableModes[0],
    [availableModes, mode],
  );

  const activeRuns = useMemo(
    () => analysisRuns.filter((run) => RUN_ACTIVE_STATUSES.includes(run.status)),
    [analysisRuns],
  );
  const latestRun = analysisRuns[0] ?? null;
  const lastTraceId = latestRun?.trace_id ?? entries.at(-1)?.traceId ?? null;

  useEffect(() => {
    if (!availableModes.some((candidate) => candidate.value === mode)) {
      setMode(availableModes[0]?.value ?? "rag");
    }
  }, [availableModes, mode]);

  useEffect(() => {
    onStatusChange?.({
      entryCount: entries.length + analysisRuns.length,
      isSubmitting: isSubmitting || activeRuns.length > 0,
      currentDraft: question,
      lastTraceId,
      latestAnalysisRunId: latestRun?.id ?? null,
      latestAnalysisRunStatus: latestRun?.status ?? null,
      latestAnalysisRunQuestion: latestRun?.question ?? null,
    });
  }, [activeRuns.length, analysisRuns.length, entries.length, isSubmitting, lastTraceId, latestRun, onStatusChange, question]);

  useEffect(() => {
    if (!session || !supportsBackgroundRuns) {
      setAnalysisRuns([]);
      return;
    }

    let cancelled = false;
    const loadRuns = async () => {
      setIsLoadingRuns(true);
      try {
        const runs = await listWorkspaceResearchAnalysisRuns(session.accessToken, workspaceId, 8);
        if (!cancelled) {
          setAnalysisRuns(runs);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "Unable to load background analysis runs.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingRuns(false);
        }
      }
    };

    void loadRuns();
    return () => {
      cancelled = true;
    };
  }, [session, supportsBackgroundRuns, workspaceId]);

  useEffect(() => {
    if (!session || activeRuns.length === 0) {
      return;
    }

    let cancelled = false;
    const refreshActiveRuns = async () => {
      try {
        const refreshedRuns = await Promise.all(
          activeRuns.map((run) => getResearchAnalysisRun(session.accessToken, run.id)),
        );
        if (!cancelled) {
          setAnalysisRuns((currentRuns) => mergeRuns(currentRuns, refreshedRuns));
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "Unable to refresh the background analysis run.");
        }
      }
    };

    void refreshActiveRuns();
    const timer = window.setInterval(() => {
      void refreshActiveRuns();
    }, 2500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeRuns, session]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || !question.trim()) {
      return;
    }

    const trimmedQuestion = question.trim();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (mode === "research_tool_assisted" && supportsBackgroundRuns) {
        const run = await createWorkspaceResearchAnalysisRun(session.accessToken, workspaceId, {
          question: trimmedQuestion,
          conversation_id: latestRun?.conversation_id,
          mode: "research_tool_assisted",
        });
        setAnalysisRuns((currentRuns) => mergeRuns(currentRuns, [run]));
      } else {
        const response = await sendWorkspaceChat(session.accessToken, workspaceId, {
          question: trimmedQuestion,
          mode,
        });
        setEntries((currentEntries) => [
          ...currentEntries,
          {
            question: trimmedQuestion,
            answer: response.answer,
            traceId: response.trace_id,
            mode: response.mode,
            toolSteps: response.tool_steps,
            sources: response.sources,
          },
        ]);
      }
      setQuestion("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to start the analysis.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Research workflow">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in before starting a research workflow." />;
  }

  return (
    <section
      style={{
        background: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,1) 100%)",
        border: "1px solid #dbe4f0",
        borderRadius: 28,
        boxShadow: "0 28px 56px rgba(15, 23, 42, 0.08)",
        display: "grid",
        gap: 16,
        minHeight: 680,
        padding: 20,
      }}
    >
      <section style={{ display: "grid", gap: 10 }}>
        <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
          <span style={{ color: "#0f172a99", fontSize: 12, fontWeight: 700, letterSpacing: "0.14em" }}>{workflowLabel}</span>
          <span style={{ color: "#64748b", fontSize: 13 }}>Prompt cards are clickable and insert directly into the draft box.</span>
        </div>
        {availableModes.length > 1 ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {availableModes.map((candidate) => {
                const active = candidate.value === mode;
                return (
                  <button
                    key={candidate.value}
                    onClick={() => setMode(candidate.value)}
                    style={{
                      backgroundColor: active ? "#0f172a" : "#ffffff",
                      border: `1px solid ${active ? "#0f172a" : "#cbd5e1"}`,
                      borderRadius: 999,
                      color: active ? "#f8fafc" : "#0f172a",
                      fontSize: 13,
                      fontWeight: 700,
                      minHeight: 40,
                      padding: "0 14px",
                    }}
                    type="button"
                  >
                    {candidate.label}
                  </button>
                );
              })}
            </div>
            <div style={{ color: "#475569", fontSize: 14, lineHeight: 1.7 }}>{modeMeta?.description}</div>
          </div>
        ) : null}
        <div style={{ display: "grid", gap: 4 }}>
          <strong style={{ color: "#0f172a", fontSize: 20 }}>{introTitle}</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{introBody}</p>
        </div>
        <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
          {prompts.map((prompt) => (
            <PromptCard active={question === prompt} key={prompt} label={prompt} onClick={() => setQuestion(prompt)} />
          ))}
        </div>
      </section>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 8 }}>
          <span style={{ color: "#0f172a", fontSize: 14, fontWeight: 800 }}>Current research question</span>
          <textarea
            onChange={(event) => setQuestion(event.target.value)}
            placeholder={placeholder}
            required
            rows={5}
            style={{
              borderRadius: 22,
              border: "1px solid #cbd5e1",
              minHeight: 138,
              padding: "18px 20px",
              resize: "vertical",
            }}
            value={question}
          />
        </label>
        {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
        <div style={{ display: "flex", justifyContent: "flex-start" }}>
          <button
            disabled={isSubmitting}
            style={{
              backgroundColor: "#0f172a",
              border: "none",
              borderRadius: 999,
              color: "#ffffff",
              fontSize: 16,
              fontWeight: 800,
              minHeight: 48,
              minWidth: 148,
              padding: "0 22px",
            }}
            type="submit"
          >
            {isSubmitting ? "Starting..." : primaryActionLabel}
          </button>
        </div>
      </form>

      <section
        style={{
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: 24,
          display: "grid",
          gap: 14,
          minHeight: 320,
          padding: 18,
        }}
      >
        <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
          <strong style={{ color: "#0f172a", fontSize: 18 }}>{outputTitle}</strong>
          <span style={{ color: "#64748b", fontSize: 13 }}>
            {entries.length + analysisRuns.length > 0 ? `${entries.length + analysisRuns.length} passes recorded` : "No analysis pass yet"}
          </span>
        </div>

        {entries.length === 0 && analysisRuns.length === 0 && !isSubmitting && !isLoadingRuns ? (
          <div
            style={{
              alignItems: "center",
              color: "#64748b",
              display: "grid",
              justifyItems: "start",
              lineHeight: 1.8,
              minHeight: 180,
              padding: 8,
            }}
          >
            Start one analysis pass. This area will show background run status, assistant conclusions, trace links, and grounded sources.
          </div>
        ) : null}

        {isSubmitting ? (
          <section
            style={{
              backgroundColor: "#eff6ff",
              border: "1px solid #bfdbfe",
              borderRadius: 18,
              color: "#0f172a",
              display: "grid",
              gap: 6,
              padding: 16,
            }}
          >
            <strong>Submitting the analysis request</strong>
            <span style={{ color: "#475569" }}>The run will appear here as soon as the server accepts it.</span>
          </section>
        ) : null}

        {analysisRuns.length > 0 ? (
          <div style={{ display: "grid", gap: 16 }}>
            {analysisRuns.map((run) => (
              <AnalysisRunCard key={run.id} run={run} />
            ))}
          </div>
        ) : null}

        {entries.length > 0 ? (
          <div style={{ display: "grid", gap: 20 }}>
            {entries.map((entry) => (
              <ChatBubble assistantLabel={assistantLabel} entry={entry} key={entry.traceId} />
            ))}
          </div>
        ) : null}
      </section>
    </section>
  );
}
