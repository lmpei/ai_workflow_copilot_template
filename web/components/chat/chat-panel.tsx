"use client";

import { useEffect, useMemo, useState } from "react";

import {
  createWorkspaceResearchAnalysisRun,
  getResearchAnalysisRun,
  getWorkspaceConnectorStatus,
  grantWorkspaceConnectorConsent,
  isApiClientError,
  listWorkspaceResearchAnalysisRuns,
  sendWorkspaceChat,
} from "../../lib/api";
import type {
  ChatSource,
  ChatToolStep,
  ResearchAnalysisRunRecord,
  ResearchAnalysisRunStatus,
  WorkspaceConnectorStatusRecord,
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
    value: "rag" | "research_tool_assisted" | "research_external_context";
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
  mode: "rag" | "research_tool_assisted" | "research_external_context";
  toolSteps: ChatToolStep[];
  sources: ChatSource[];
};

const RUN_TERMINAL_STATUSES: ResearchAnalysisRunStatus[] = ["completed", "degraded", "failed"];
const RUN_ACTIVE_STATUSES: ResearchAnalysisRunStatus[] = ["pending", "running"];
const RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID = "research_external_context";

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
    pending: { label: "排队中", color: "#92400e", background: "#fef3c7" },
    running: { label: "运行中", color: "#1d4ed8", background: "#dbeafe" },
    completed: { label: "已完成", color: "#166534", background: "#dcfce7" },
    degraded: { label: "降级完成", color: "#7c2d12", background: "#ffedd5" },
    failed: { label: "失败", color: "#b91c1c", background: "#fee2e2" },
  };
  const token = palette[status];
  return (
    <span
      style={{
        alignItems: "center",
        backgroundColor: token.background,
        borderRadius: 999,
        color: token.color,
        display: "inline-flex",
        fontSize: 12,
        fontWeight: 800,
        minHeight: 28,
        padding: "0 10px",
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
      <strong style={{ color: "#0f172a", fontSize: 14 }}>本次分析步骤</strong>
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
      <summary>查看分析依据</summary>
      {sources.length === 0 ? (
        <p style={{ color: "#64748b", marginBottom: 0 }}>这一轮没有返回可见的证据。</p>
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
              <div style={{ alignItems: "center", display: "flex", gap: 8, justifyContent: "space-between" }}>
                <strong>{source.document_title}</strong>
                <span
                  style={{
                    backgroundColor: source.source_kind === "external_context" ? "#ede9fe" : "#e0f2fe",
                    borderRadius: 999,
                    color: source.source_kind === "external_context" ? "#5b21b6" : "#0c4a6e",
                    fontSize: 12,
                    fontWeight: 700,
                    padding: "4px 10px",
                  }}
                >
                  {source.source_kind === "external_context" ? "外部信息" : "工作区资料"}
                </span>
              </div>
              <div style={{ color: "#475569", fontSize: 13 }}>
                分片 {source.chunk_index} / 文档 {source.document_id}
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
          <div style={{ color: "#cbd5e1", fontSize: 12, fontWeight: 700, marginBottom: 6 }}>你的问题</div>
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
                工具辅助试点
              </span>
            ) : null}
            {entry.mode === "research_external_context" ? (
              <span
                style={{
                  backgroundColor: "#ede9fe",
                  borderRadius: 999,
                  color: "#5b21b6",
                  fontSize: 12,
                  fontWeight: 700,
                  padding: "4px 10px",
                }}
              >
                外部信息试点
              </span>
            ) : null}
            <span style={{ color: "#64748b", fontSize: 12 }}>追踪 ID：{entry.traceId}</span>
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
    pending: "这次分析已经进入队列，很快会开始。",
    running: "系统正在读取资料、规划下一步，并合成结果。",
    completed: "这次有边界的分析已经成功完成。",
    degraded: "这次分析已诚实完成，但证据路径较弱，系统已经明确标出。",
    failed: "后台分析在完成前失败了。",
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
            后台分析运行
          </span>
          <strong style={{ color: "#0f172a", lineHeight: 1.6 }}>{run.question}</strong>
        </div>
        <StatusBadge status={run.status} />
      </div>

      <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{outcomeCopy[run.status]}</p>

      <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
        <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
          <span style={{ color: "#64748b", fontSize: 12 }}>分析焦点</span>
          <strong style={{ color: "#0f172a" }}>{run.analysis_focus ?? "等待系统确定分析焦点"}</strong>
        </div>
        <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
          <span style={{ color: "#64748b", fontSize: 12 }}>搜索词</span>
          <strong style={{ color: "#0f172a" }}>{run.search_query ?? "暂时还没有"}</strong>
        </div>
      </div>

      {run.resumed_from_run_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          延续自运行：<strong style={{ color: "#0f172a" }}>{run.resumed_from_run_id}</strong>
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
          <strong style={{ color: "#0f172a" }}>压缩后的运行记忆</strong>
          <div style={{ color: "#334155", lineHeight: 1.7 }}>{run.run_memory.summary}</div>
          <div style={{ color: "#475569", fontSize: 13 }}>
            证据状态：<strong style={{ color: "#0f172a" }}>{run.run_memory.evidence_state}</strong>
          </div>
          <div style={{ color: "#475569", fontSize: 13 }}>
            建议下一步：{run.run_memory.recommended_next_step}
          </div>
          {run.run_memory.source_titles.length > 0 ? (
            <div style={{ color: "#475569", fontSize: 13 }}>
              保留下来的资料标题：{run.run_memory.source_titles.join("、")}
            </div>
          ) : null}
        </section>
      ) : null}

      {run.trace_id ? <div style={{ color: "#64748b", fontSize: 13 }}>追踪 ID：{run.trace_id}</div> : null}
      {run.degraded_reason ? <div style={{ color: "#9a3412", fontSize: 13 }}>降级原因：{run.degraded_reason}</div> : null}
      {run.error_message ? <div style={{ color: "#b91c1c", fontSize: 13 }}>错误：{run.error_message}</div> : null}

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
  workflowLabel = "Research 工作流",
  introTitle = "从一个研究问题开始",
  introBody = "先点一个提示问题，或者直接输入你的研究问题，然后开始分析。",
  placeholder = "例如：总结当前资料里最强的市场信号，并告诉我在形成正式结论前还缺少哪些关键证据。",
  suggestedPrompts,
  primaryActionLabel = "开始分析",
  outputTitle = "分析过程与结论",
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
  const [connectorStatus, setConnectorStatus] = useState<WorkspaceConnectorStatusRecord | null>(null);
  const [isGrantingConnectorConsent, setIsGrantingConnectorConsent] = useState(false);

  const availableModes = useMemo(
    () =>
      modes && modes.length > 0
        ? modes
        : [{ value: "rag" as const, label: "标准分析", description: "直接基于当前资料完成一次有依据的分析。" }],
    [modes],
  );

  const [mode, setMode] = useState<"rag" | "research_tool_assisted" | "research_external_context">(
    availableModes[0]?.value ?? "rag",
  );

  const prompts = useMemo(
    () =>
      suggestedPrompts && suggestedPrompts.length > 0
        ? suggestedPrompts
        : [
            "总结当前资料里最重要的发现。",
            "告诉我还缺哪些资料，才能推进下一步研究。",
            "指出哪些结论目前还不够稳，需要继续验证。",
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
  const requiresExternalContextConnector = mode === "research_external_context";

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
          setErrorMessage(isApiClientError(error) ? error.message : "无法加载后台分析运行记录。");
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
        const refreshedRuns = await Promise.all(activeRuns.map((run) => getResearchAnalysisRun(session.accessToken, run.id)));
        if (!cancelled) {
          setAnalysisRuns((currentRuns) => mergeRuns(currentRuns, refreshedRuns));
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "无法刷新后台分析运行状态。");
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

  useEffect(() => {
    if (!session || !requiresExternalContextConnector) {
      setConnectorStatus(null);
      return;
    }

    let cancelled = false;
    const loadConnectorStatus = async () => {
      try {
        const status = await getWorkspaceConnectorStatus(
          session.accessToken,
          workspaceId,
          RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        );
        if (!cancelled) {
          setConnectorStatus(status);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "无法加载连接器授权状态。");
        }
      }
    };

    void loadConnectorStatus();
    return () => {
      cancelled = true;
    };
  }, [requiresExternalContextConnector, session, workspaceId]);

  const handleGrantConnectorConsent = async () => {
    if (!session) {
      return;
    }

    setIsGrantingConnectorConsent(true);
    setErrorMessage(null);
    try {
      const status = await grantWorkspaceConnectorConsent(
        session.accessToken,
        workspaceId,
        RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        {
          consent_note: "允许这个工作区使用一次有边界的 Research 外部信息试点。",
        },
      );
      setConnectorStatus(status);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法完成连接器授权。");
    } finally {
      setIsGrantingConnectorConsent(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session || !question.trim()) {
      return;
    }

    const trimmedQuestion = question.trim();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if ((mode === "research_tool_assisted" || mode === "research_external_context") && supportsBackgroundRuns) {
        const run = await createWorkspaceResearchAnalysisRun(session.accessToken, workspaceId, {
          question: trimmedQuestion,
          conversation_id: latestRun?.conversation_id,
          mode,
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法启动这次分析。");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Research 工作流">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="请先登录，再开始 Research 工作流。" />;
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
          <span style={{ color: "#64748b", fontSize: 13 }}>这些提示卡片可以点击，点击后会直接填入输入框。</span>
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

      {requiresExternalContextConnector ? (
        <section
          style={{
            backgroundColor: connectorStatus?.consent_state === "granted" ? "#ecfdf5" : "#fff7ed",
            border: `1px solid ${connectorStatus?.consent_state === "granted" ? "#bbf7d0" : "#fed7aa"}`,
            borderRadius: 18,
            display: "grid",
            gap: 10,
            padding: 16,
          }}
        >
          <strong style={{ color: "#0f172a" }}>外部信息试点</strong>
          <div style={{ color: "#475569", lineHeight: 1.7 }}>
            {connectorStatus?.consent_state === "granted"
              ? "这个工作区已经完成授权。下一轮分析可以把工作区资料和已批准的外部信息结合起来。"
              : "这个工作区还没有授权连接器。你仍然可以运行试点，但在授权前系统会诚实降级。"}
          </div>
          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
            <button
              disabled={connectorStatus?.consent_state === "granted" || isGrantingConnectorConsent}
              onClick={() => {
                void handleGrantConnectorConsent();
              }}
              style={{
                backgroundColor: connectorStatus?.consent_state === "granted" ? "#dcfce7" : "#0f172a",
                border: "none",
                borderRadius: 999,
                color: connectorStatus?.consent_state === "granted" ? "#166534" : "#ffffff",
                fontSize: 13,
                fontWeight: 800,
                minHeight: 40,
                padding: "0 14px",
              }}
              type="button"
            >
              {connectorStatus?.consent_state === "granted"
                ? "已授权"
                : isGrantingConnectorConsent
                  ? "授权中..."
                  : "授权连接器"}
            </button>
            {connectorStatus?.consent_state === "granted" && connectorStatus.granted_at ? (
              <span style={{ color: "#166534", fontSize: 13 }}>
                这个工作区已于 {new Date(connectorStatus.granted_at).toLocaleString()} 完成授权
              </span>
            ) : null}
          </div>
        </section>
      ) : null}

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 8 }}>
          <span style={{ color: "#0f172a", fontSize: 14, fontWeight: 800 }}>当前研究问题</span>
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
            {isSubmitting ? "启动中..." : primaryActionLabel}
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
            {entries.length + analysisRuns.length > 0 ? `${entries.length + analysisRuns.length} 次分析记录` : "还没有分析记录"}
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
            先开始一轮分析。这里会显示后台运行状态、系统结论、追踪链接和有依据的资料来源。
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
            <strong>正在提交分析请求</strong>
            <span style={{ color: "#475569" }}>服务端接受后，这次运行会立刻出现在这里。</span>
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
