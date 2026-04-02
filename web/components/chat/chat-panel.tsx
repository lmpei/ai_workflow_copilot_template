"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties, FormEvent } from "react";

import {
  createWorkspaceResearchAnalysisRun,
  getResearchAnalysisRun,
  getWorkspaceConnectorStatus,
  grantWorkspaceConnectorConsent,
  isApiClientError,
  listWorkspaceResearchAnalysisRuns,
  listWorkspaceResearchExternalResourceSnapshots,
  revokeWorkspaceConnectorConsent,
  sendWorkspaceChat,
} from "../../lib/api";
import type {
  ChatSource,
  ChatToolStep,
  ResearchAnalysisRunRecord,
  ResearchAnalysisRunStatus,
  ResearchExternalResourceSnapshotRecord,
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
  externalResourceSnapshot?: ResearchExternalResourceSnapshotRecord | null;
};

const RUN_ACTIVE_STATUSES: ResearchAnalysisRunStatus[] = ["pending", "running"];
const RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID = "research_external_context";

const cardStyle: CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #dbe4f0",
  borderRadius: 18,
  display: "grid",
  gap: 12,
  padding: 16,
};

function mergeRuns(currentRuns: ResearchAnalysisRunRecord[], incomingRuns: ResearchAnalysisRunRecord[]) {
  const byId = new Map<string, ResearchAnalysisRunRecord>();
  [...currentRuns, ...incomingRuns].forEach((run) => byId.set(run.id, run));
  return [...byId.values()].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

function mergeSnapshots(
  currentSnapshots: ResearchExternalResourceSnapshotRecord[],
  incomingSnapshots: ResearchExternalResourceSnapshotRecord[],
) {
  const byId = new Map<string, ResearchExternalResourceSnapshotRecord>();
  [...currentSnapshots, ...incomingSnapshots].forEach((snapshot) => byId.set(snapshot.id, snapshot));
  return [...byId.values()].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "";
  }

  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function getRunStatusLabel(status: ResearchAnalysisRunStatus) {
  switch (status) {
    case "pending":
      return "排队中";
    case "running":
      return "分析中";
    case "completed":
      return "已完成";
    case "degraded":
      return "诚实降级";
    case "failed":
      return "失败";
    default:
      return status;
  }
}

function getModeLabel(mode: "rag" | "research_tool_assisted" | "research_external_context") {
  switch (mode) {
    case "rag":
      return "标准分析";
    case "research_tool_assisted":
      return "工具辅助";
    case "research_external_context":
      return "MCP 资源试点";
    default:
      return mode;
  }
}

function normalizeModeMeta(candidate: {
  value: "rag" | "research_tool_assisted" | "research_external_context";
  label: string;
  description: string;
}) {
  if (candidate.value !== "research_external_context") {
    return candidate;
  }

  return {
    ...candidate,
    label: "MCP 资源试点",
    description: "在授权后读取一个有边界的 MCP 资源摘要，并继续清楚地区分工作区资料和外部上下文。",
  };
}
function getConnectorStatusCopy(status: WorkspaceConnectorStatusRecord | null) {
  if (!status || status.consent_state === "not_granted") {
    return {
      tone: "#fff7ed",
      border: "#fed7aa",
      accent: "#9a3412",
      title: "尚未授权 MCP 资源试点",
      body: "当前工作区还没有授权使用 MCP 资源。授权后，研究分析可以在工作区资料之外读取有边界的外部上下文。",
    };
  }

  if (status.consent_state === "revoked") {
    return {
      tone: "#fef2f2",
      border: "#fecaca",
      accent: "#991b1b",
      title: "授权已撤销",
      body: "当前工作区已撤销 MCP 资源授权。你仍然可以查看已有快照，但新的 MCP 资源读取会诚实降级。",
    };
  }

  return {
    tone: "#ecfdf5",
    border: "#bbf7d0",
    accent: "#166534",
    title: "已授权 MCP 资源试点",
    body: "当前工作区可以在研究分析里读取 MCP 资源摘要，并且会明确区分工作区资料和外部上下文来源。",
  };
}

function SnapshotCard({
  snapshot,
  title,
  isSelected = false,
  actionLabel,
  onAction,
}: {
  snapshot: ResearchExternalResourceSnapshotRecord;
  title: string;
  isSelected?: boolean;
  actionLabel?: string;
  onAction?: (() => void) | null;
}) {
  return (
    <div
      style={{
        ...cardStyle,
        backgroundColor: isSelected ? "#f3e8ff" : "#faf5ff",
        border: `1px solid ${isSelected ? "#7c3aed" : "#ddd6fe"}`,
        gap: 8,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", gap: 12, justifyContent: "space-between" }}>
        <strong style={{ color: "#581c87", fontSize: 14 }}>{title}</strong>
        {actionLabel && onAction ? (
          <button
            onClick={onAction}
            style={{
              backgroundColor: isSelected ? "#6b21a8" : "#ffffff",
              border: `1px solid ${isSelected ? "#6b21a8" : "#c4b5fd"}`,
              borderRadius: 999,
              color: isSelected ? "#ffffff" : "#6b21a8",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 700,
              minHeight: 32,
              padding: "0 12px",
            }}
            type="button"
          >
            {actionLabel}
          </button>
        ) : null}
      </div>
      <div style={{ color: "#0f172a", fontWeight: 700 }}>{snapshot.title}</div>
      <div style={{ color: "#475569", fontSize: 13 }}>
        搜索词：{snapshot.search_query}
        {snapshot.analysis_focus ? ` | 分析焦点：${snapshot.analysis_focus}` : ""}
      </div>
      <div style={{ color: "#475569", fontSize: 13 }}>资源数：{snapshot.resource_count}</div>
      <div style={{ display: "grid", gap: 8 }}>
        {snapshot.resources.map((resource) => (
          <div
            key={`${snapshot.id}-${resource.resource_id}`}
            style={{ backgroundColor: "#ffffff", border: "1px solid #e9d5ff", borderRadius: 12, padding: 10 }}
          >
            <div style={{ color: "#0f172a", fontSize: 13, fontWeight: 700 }}>{resource.title}</div>
            <div style={{ color: "#6b21a8", fontSize: 12 }}>{resource.source_label}</div>
            <div style={{ color: "#475569", fontSize: 13, lineHeight: 1.7 }}>{resource.snippet}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
function ToolStepList({ toolSteps }: { toolSteps: ChatToolStep[] }) {
  if (toolSteps.length === 0) {
    return null;
  }

  return (
    <div style={{ ...cardStyle, backgroundColor: "#f8fafc", gap: 8, marginTop: 12 }}>
      <strong style={{ color: "#0f172a", fontSize: 14 }}>分析步骤</strong>
      {toolSteps.map((step, index) => (
        <div
          key={`${step.tool_name}-${index}`}
          style={{ backgroundColor: "#ffffff", border: "1px solid #dbe4f0", borderRadius: 12, padding: 10 }}
        >
          <div style={{ color: "#0f172a", fontSize: 13, fontWeight: 700 }}>{step.summary}</div>
          {step.detail ? <div style={{ color: "#475569", fontSize: 13 }}>{step.detail}</div> : null}
        </div>
      ))}
    </div>
  );
}

function SourceList({ sources, traceId }: { sources: ChatSource[]; traceId: string | null }) {
  if (sources.length === 0) {
    return <div style={{ color: "#64748b", fontSize: 13, marginTop: 12 }}>这次输出没有返回可见来源。</div>;
  }

  return (
    <details style={{ marginTop: 12 }}>
      <summary style={{ cursor: "pointer", fontWeight: 700 }}>查看来源</summary>
      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {sources.map((source) => (
          <div
            key={`${traceId ?? "run"}-${source.chunk_id}`}
            style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, padding: 12 }}
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
              片段 {source.chunk_index} / 文档 ID：{source.document_id}
            </div>
            <div style={{ color: "#334155", lineHeight: 1.7 }}>{source.snippet}</div>
          </div>
        ))}
      </div>
    </details>
  );
}

function ResponseCard({ entry }: { entry: ChatEntry }) {
  return (
    <section style={cardStyle}>
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
        <span
          style={{
            backgroundColor: "#e2e8f0",
            borderRadius: 999,
            color: "#0f172a",
            fontSize: 12,
            fontWeight: 700,
            padding: "4px 10px",
          }}
        >
          {getModeLabel(entry.mode)}
        </span>
        <span style={{ color: "#64748b", fontSize: 13 }}>追踪：{entry.traceId}</span>
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong style={{ color: "#0f172a" }}>你的问题</strong>
          <div style={{ color: "#334155", lineHeight: 1.7 }}>{entry.question}</div>
        </div>
        <div>
          <strong style={{ color: "#0f172a" }}>分析结论</strong>
          <div style={{ color: "#334155", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{entry.answer}</div>
        </div>
      </div>
      {entry.externalResourceSnapshot ? (
        <SnapshotCard snapshot={entry.externalResourceSnapshot} title="本次使用的外部资源快照" />
      ) : null}
      <ToolStepList toolSteps={entry.toolSteps} />
      <SourceList sources={entry.sources} traceId={entry.traceId} />
    </section>
  );
}

function RunCard({ run }: { run: ResearchAnalysisRunRecord }) {
  return (
    <section style={cardStyle}>
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
        <span
          style={{
            backgroundColor: RUN_ACTIVE_STATUSES.includes(run.status) ? "#e0f2fe" : "#e2e8f0",
            borderRadius: 999,
            color: "#0f172a",
            fontSize: 12,
            fontWeight: 700,
            padding: "4px 10px",
          }}
        >
          {getRunStatusLabel(run.status)}
        </span>
        <span style={{ color: "#64748b", fontSize: 13 }}>{getModeLabel(run.mode)}</span>
        {run.trace_id ? <span style={{ color: "#64748b", fontSize: 13 }}>追踪：{run.trace_id}</span> : null}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong style={{ color: "#0f172a" }}>研究问题</strong>
          <div style={{ color: "#334155", lineHeight: 1.7 }}>{run.question}</div>
        </div>
        {run.answer ? (
          <div>
            <strong style={{ color: "#0f172a" }}>分析结论</strong>
            <div style={{ color: "#334155", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{run.answer}</div>
          </div>
        ) : (
          <div style={{ color: "#475569", lineHeight: 1.7 }}>这条后台分析还没有产出最终回答。</div>
        )}
        {run.degraded_reason ? (
          <div style={{ color: "#9a3412", fontSize: 13 }}>降级原因：{run.degraded_reason}</div>
        ) : null}
      </div>
      {run.external_resource_snapshot ? (
        <SnapshotCard snapshot={run.external_resource_snapshot} title="本次运行使用的外部资源快照" />
      ) : null}
      <ToolStepList toolSteps={run.tool_steps} />
      <SourceList sources={run.sources} traceId={run.trace_id ?? null} />
      <div style={{ color: "#64748b", fontSize: 12 }}>
        创建于 {formatDateTime(run.created_at)}
        {run.completed_at ? ` · 完成于 ${formatDateTime(run.completed_at)}` : ""}
      </div>
    </section>
  );
}

export default function ChatPanel({
  workspaceId,
  assistantLabel = "Research Assistant",
  workflowLabel = "Research 工作流",
  introTitle = "从一个研究问题开始",
  introBody = "可以直接输入问题，也可以先点一个快捷提示词，然后开始分析。",
  placeholder = "例如：总结当前资料里最重要的发现，并告诉我还缺哪些关键证据。",
  suggestedPrompts,
  primaryActionLabel = "开始分析",
  outputTitle = "分析过程与结果",
  modes,
  supportsBackgroundRuns = false,
  onStatusChange,
}: ChatPanelProps) {
  const { session, isReady } = useAuthSession();
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [analysisRuns, setAnalysisRuns] = useState<ResearchAnalysisRunRecord[]>([]);
  const [recentSnapshots, setRecentSnapshots] = useState<ResearchExternalResourceSnapshotRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [connectorStatus, setConnectorStatus] = useState<WorkspaceConnectorStatusRecord | null>(null);
  const [isGrantingConnectorConsent, setIsGrantingConnectorConsent] = useState(false);
  const [isRevokingConnectorConsent, setIsRevokingConnectorConsent] = useState(false);
  const [selectedExternalResourceSnapshotId, setSelectedExternalResourceSnapshotId] = useState<string | null>(null);

  const availableModes = useMemo(
    () =>
      modes && modes.length > 0
        ? modes.map(normalizeModeMeta)
        : [
            {
              value: "rag" as const,
              label: "标准分析",
              description: "直接基于当前工作区资料生成有依据的回答。",
            },
          ],
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
            "指出现阶段还缺哪些关键证据。",
            "告诉我哪些结论还需要继续验证。",
          ],
    [suggestedPrompts],
  );

  const modeMeta = useMemo(
    () => availableModes.find((candidate) => candidate.value === mode) ?? availableModes[0],
    [availableModes, mode],
  );
  const activeRuns = useMemo(() => analysisRuns.filter((run) => RUN_ACTIVE_STATUSES.includes(run.status)), [analysisRuns]);
  const latestRun = analysisRuns[0] ?? null;
  const lastTraceId = latestRun?.trace_id ?? entries.at(-1)?.traceId ?? null;
  const requiresExternalContextConnector = mode === "research_external_context";
  const selectedExternalResourceSnapshot = useMemo(
    () => recentSnapshots.find((snapshot) => snapshot.id === selectedExternalResourceSnapshotId) ?? null,
    [recentSnapshots, selectedExternalResourceSnapshotId],
  );
  const connectorCopy = getConnectorStatusCopy(connectorStatus);

  useEffect(() => {
    if (!availableModes.some((candidate) => candidate.value === mode)) {
      setMode(availableModes[0]?.value ?? "rag");
    }
  }, [availableModes, mode]);

  useEffect(() => {
    if (!requiresExternalContextConnector) {
      setSelectedExternalResourceSnapshotId(null);
      return;
    }

    if (
      selectedExternalResourceSnapshotId &&
      !recentSnapshots.some((snapshot) => snapshot.id === selectedExternalResourceSnapshotId)
    ) {
      setSelectedExternalResourceSnapshotId(null);
    }
  }, [recentSnapshots, requiresExternalContextConnector, selectedExternalResourceSnapshotId]);

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
      setRecentSnapshots([]);
      return;
    }

    let cancelled = false;

    const loadSurfaceData = async () => {
      setIsLoadingRuns(true);
      try {
        const [runs, snapshots] = await Promise.all([
          listWorkspaceResearchAnalysisRuns(session.accessToken, workspaceId, 8),
          listWorkspaceResearchExternalResourceSnapshots(session.accessToken, workspaceId, 8),
        ]);
        if (!cancelled) {
          setAnalysisRuns(runs);
          setRecentSnapshots(
            mergeSnapshots(
              snapshots,
              runs.flatMap((run) => (run.external_resource_snapshot ? [run.external_resource_snapshot] : [])),
            ),
          );
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "无法加载最近的分析运行和外部资源快照。");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingRuns(false);
        }
      }
    };

    void loadSurfaceData();
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
          setRecentSnapshots((currentSnapshots) =>
            mergeSnapshots(
              currentSnapshots,
              refreshedRuns.flatMap((run) => (run.external_resource_snapshot ? [run.external_resource_snapshot] : [])),
            ),
          );
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "刷新后台分析状态时失败。");
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
          setErrorMessage(isApiClientError(error) ? error.message : "无法读取 MCP 资源试点的授权状态。");
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
        { consent_note: "允许当前 Research 工作区使用外部信息试点。" },
      );
      setConnectorStatus(status);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "授权外部信息试点时失败。");
    } finally {
      setIsGrantingConnectorConsent(false);
    }
  };

  const handleRevokeConnectorConsent = async () => {
    if (!session) {
      return;
    }

    setIsRevokingConnectorConsent(true);
    setErrorMessage(null);
    try {
      const status = await revokeWorkspaceConnectorConsent(
        session.accessToken,
        workspaceId,
        RESEARCH_EXTERNAL_CONTEXT_CONNECTOR_ID,
        { consent_note: "撤销当前 Research 工作区对外部信息试点的授权。" },
      );
      setConnectorStatus(status);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "撤销外部信息试点授权时失败。");
    } finally {
      setIsRevokingConnectorConsent(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
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
          external_resource_snapshot_id:
            mode === "research_external_context" ? selectedExternalResourceSnapshotId ?? undefined : undefined,
        });
        setAnalysisRuns((currentRuns) => mergeRuns(currentRuns, [run]));
        if (run.external_resource_snapshot) {
          const snapshot = run.external_resource_snapshot;
          setRecentSnapshots((currentSnapshots) => mergeSnapshots(currentSnapshots, [snapshot]));
        }
      } else {
        const response = await sendWorkspaceChat(session.accessToken, workspaceId, {
          question: trimmedQuestion,
          mode,
          external_resource_snapshot_id:
            mode === "research_external_context" ? selectedExternalResourceSnapshotId ?? undefined : undefined,
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
            externalResourceSnapshot: response.external_resource_snapshot ?? null,
          },
        ]);
        if (response.external_resource_snapshot) {
          const snapshot = response.external_resource_snapshot;
          setRecentSnapshots((currentSnapshots) => mergeSnapshots(currentSnapshots, [snapshot]));
        }
      }
      setQuestion("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "提交分析请求时失败。");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Research 工作流">正在加载工作流...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="请先登录，再进入 Research 工作流。" />;
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
          <span style={{ color: "#64748b", fontSize: 13 }}>{assistantLabel}</span>
          {isLoadingRuns ? <span style={{ color: "#64748b", fontSize: 13 }}>正在刷新后台分析状态...</span> : null}
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
            <button
              key={prompt}
              onClick={() => setQuestion(prompt)}
              style={{
                backgroundColor: question === prompt ? "#0f172a" : "#ffffff",
                border: `1px solid ${question === prompt ? "#0f172a" : "#cbd5e1"}`,
                borderRadius: 16,
                color: question === prompt ? "#f8fafc" : "#0f172a",
                cursor: "pointer",
                fontWeight: 700,
                minHeight: 60,
                padding: 12,
                textAlign: "left",
              }}
              type="button"
            >
              {prompt}
            </button>
          ))}
        </div>
      </section>

      {requiresExternalContextConnector ? (
        <section
          style={{
            backgroundColor: connectorCopy.tone,
            border: `1px solid ${connectorCopy.border}`,
            borderRadius: 18,
            display: "grid",
            gap: 10,
            padding: 16,
          }}
        >
          <strong style={{ color: connectorCopy.accent }}>{connectorCopy.title}</strong>
          <div style={{ color: "#475569", lineHeight: 1.7 }}>{connectorCopy.body}</div>
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
                  : connectorStatus?.consent_state === "revoked"
                    ? "重新授权"
                    : "授权 MCP 资源试点"}
            </button>
            <button
              disabled={connectorStatus?.consent_state !== "granted" || isRevokingConnectorConsent}
              onClick={() => {
                void handleRevokeConnectorConsent();
              }}
              style={{
                backgroundColor: "#ffffff",
                border: "1px solid #cbd5e1",
                borderRadius: 999,
                color: "#0f172a",
                fontSize: 13,
                fontWeight: 700,
                minHeight: 40,
                padding: "0 14px",
              }}
              type="button"
            >
              {isRevokingConnectorConsent ? "撤销中..." : "撤销授权"}
            </button>
            {connectorStatus?.consent_state === "granted" && connectorStatus.granted_at ? (
              <span style={{ color: "#166534", fontSize: 13 }}>授权时间：{formatDateTime(connectorStatus.granted_at)}</span>
            ) : null}
            {connectorStatus?.consent_state === "revoked" && connectorStatus.revoked_at ? (
              <span style={{ color: "#b91c1c", fontSize: 13 }}>撤销时间：{formatDateTime(connectorStatus.revoked_at)}</span>
            ) : null}
          </div>
        </section>
      ) : null}

      {requiresExternalContextConnector && recentSnapshots.length > 0 ? (
        <section style={{ ...cardStyle, gap: 10 }}>
          <div style={{ alignItems: "center", display: "flex", gap: 12, justifyContent: "space-between" }}>
            <strong style={{ color: "#0f172a", fontSize: 16 }}>最近外部资源快照</strong>
            <button
              onClick={() => setSelectedExternalResourceSnapshotId(null)}
              style={{
                backgroundColor: selectedExternalResourceSnapshotId ? "#ffffff" : "#0f172a",
                border: `1px solid ${selectedExternalResourceSnapshotId ? "#cbd5e1" : "#0f172a"}`,
                borderRadius: 999,
                color: selectedExternalResourceSnapshotId ? "#0f172a" : "#ffffff",
                cursor: "pointer",
                fontSize: 12,
                fontWeight: 700,
                minHeight: 32,
                padding: "0 12px",
              }}
              type="button"
            >
              {selectedExternalResourceSnapshotId ? "改为自动选择" : "当前为自动选择"}
            </button>
          </div>
          <span style={{ color: "#475569", fontSize: 13 }}>
            这些快照来自最近真实使用过的 MCP 资源结果。你可以明确选择其中一个快照继续分析，也可以保持自动选择。
          </span>
          {selectedExternalResourceSnapshot ? (
            <div style={{ color: "#6b21a8", fontSize: 13, fontWeight: 700 }}>
              当前已选快照：{selectedExternalResourceSnapshot.title}
            </div>
          ) : null}
          <div style={{ display: "grid", gap: 12 }}>
            {recentSnapshots.map((snapshot, index) => (
              <SnapshotCard
                key={snapshot.id}
                snapshot={snapshot}
                title={`快照 ${index + 1}`}
                isSelected={snapshot.id === selectedExternalResourceSnapshotId}
                actionLabel={snapshot.id === selectedExternalResourceSnapshotId ? "已选中" : "使用这个快照"}
                onAction={() => setSelectedExternalResourceSnapshotId(snapshot.id)}
              />
            ))}
          </div>
        </section>
      ) : null}

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 8 }}>
          <span style={{ color: "#0f172a", fontSize: 14, fontWeight: 800 }}>输入当前问题</span>
          <textarea
            onChange={(event) => setQuestion(event.target.value)}
            placeholder={placeholder}
            required
            rows={5}
            style={{ borderRadius: 22, border: "1px solid #cbd5e1", minHeight: 138, padding: "18px 20px", resize: "vertical" }}
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
            {isSubmitting ? "提交中..." : primaryActionLabel}
          </button>
        </div>
      </form>

      <section style={{ display: "grid", gap: 14 }}>
        <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "space-between" }}>
          <strong style={{ color: "#0f172a", fontSize: 18 }}>{outputTitle}</strong>
          {activeRuns.length > 0 ? <span style={{ color: "#0f766e", fontSize: 13 }}>当前有 {activeRuns.length} 条后台分析正在运行</span> : null}
        </div>

        {entries.length === 0 && analysisRuns.length === 0 ? (
          <div style={{ ...cardStyle, color: "#475569", lineHeight: 1.8 }}>
            先输入一个研究问题并开始分析。标准分析会直接回答，工具辅助和 MCP 资源试点会创建可回看的后台分析运行。
          </div>
        ) : null}

        {entries.map((entry, index) => (
          <ResponseCard key={`${entry.traceId}-${index}`} entry={entry} />
        ))}

        {analysisRuns.map((run) => (
          <RunCard key={run.id} run={run} />
        ))}
      </section>
    </section>
  );
}
