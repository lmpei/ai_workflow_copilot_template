"use client";

import { useEffect, useMemo, useState } from "react";

import {
  createWorkspaceResearchAnalysisRun,
  getResearchAnalysisRun,
  getWorkspaceConnectorStatus,
  grantWorkspaceConnectorConsent,
  isApiClientError,
  listWorkspaceResearchAnalysisRuns,
  listWorkspaceResearchExternalResourceSnapshots,
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

const panelStyle = {
  backgroundColor: "#ffffff",
  border: "1px solid #dbe4f0",
  borderRadius: 18,
  display: "grid",
  gap: 12,
  padding: 16,
} as const;

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

function SnapshotCard({ snapshot, title }: { snapshot: ResearchExternalResourceSnapshotRecord; title: string }) {
  return (
    <div style={{ ...panelStyle, backgroundColor: "#faf5ff", border: "1px solid #ddd6fe", gap: 8, marginTop: 12 }}>
      <strong style={{ color: "#581c87", fontSize: 14 }}>{title}</strong>
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
    <div style={{ ...panelStyle, backgroundColor: "#f8fafc", gap: 8, marginTop: 12 }}>
      <strong style={{ color: "#0f172a", fontSize: 14 }}>本次分析步骤</strong>
      {toolSteps.map((step, index) => (
        <div key={`${step.tool_name}-${index}`} style={{ backgroundColor: "#ffffff", border: "1px solid #dbe4f0", borderRadius: 12, padding: 10 }}>
          <div style={{ color: "#0f172a", fontSize: 13, fontWeight: 700 }}>{step.summary}</div>
          {step.detail ? <div style={{ color: "#475569", fontSize: 13 }}>{step.detail}</div> : null}
        </div>
      ))}
    </div>
  );
}

function SourceList({ sources, traceId }: { sources: ChatSource[]; traceId: string | null }) {
  return (
    <details style={{ marginTop: 12 }}>
      <summary>查看分析依据</summary>
      {sources.length === 0 ? (
        <p style={{ color: "#64748b", marginBottom: 0 }}>这一轮没有返回可见的依据。</p>
      ) : (
        <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
          {sources.map((source) => (
            <div
              key={`${traceId ?? "run"}-${source.chunk_id}`}
              style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, padding: 12 }}
            >
              <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between", gap: 8 }}>
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
              <div style={{ color: "#475569", fontSize: 13 }}>分片 {source.chunk_index} / 文档 {source.document_id}</div>
              <div style={{ color: "#334155", lineHeight: 1.7 }}>{source.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </details>
  );
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
  const [recentSnapshots, setRecentSnapshots] = useState<ResearchExternalResourceSnapshotRecord[]>([]);
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

  const activeRuns = useMemo(() => analysisRuns.filter((run) => RUN_ACTIVE_STATUSES.includes(run.status)), [analysisRuns]);
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
          setErrorMessage(isApiClientError(error) ? error.message : "无法加载研究运行和外部资源快照。");
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
        { consent_note: "允许这个工作区使用一次有边界的 Research 外部信息试点。" },
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
        if (run.external_resource_snapshot) {
          const snapshot = run.external_resource_snapshot;
          setRecentSnapshots((currentSnapshots) => mergeSnapshots(currentSnapshots, [snapshot]));
        }
      } else {
        const response = await sendWorkspaceChat(session.accessToken, workspaceId, { question: trimmedQuestion, mode });
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
              : "这个工作区还没有授权连接器。在授权前，系统会诚实降级，只使用工作区资料。"}
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
              {connectorStatus?.consent_state === "granted" ? "已授权" : isGrantingConnectorConsent ? "授权中..." : "授权连接器"}
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
            style={{ borderRadius: 22, border: "1px solid #cbd5e1", minHeight: 138, padding: "18px 20px", resize: "vertical" }}
            value={question}
          />
        </label>
        {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
        <div style={{ display: "flex", justifyContent: "flex-start" }}>
          <button
            disabled={isSubmitting}
            style={{ backgroundColor: "#0f172a", border: "none", borderRadius: 999, color: "#ffffff", fontSize: 16, fontWeight: 800, minHeight: 48, minWidth: 148, padding: "0 22px" }}
            type="submit"
          >
            {isSubmitting ? "启动中..." : primaryActionLabel}
          </button>
        </div>
      </form>

      {recentSnapshots.length > 0 ? (
        <div style={{ ...panelStyle, gap: 10 }}>
          <strong style={{ color: "#0f172a", fontSize: 16 }}>最近外部资源快照</strong>
          <span style={{ color: "#475569", fontSize: 13 }}>这些快照会保存最近真正使用过的外部信息，不再只存在于一次回答里。</span>
          {recentSnapshots.map((snapshot) => (
            <SnapshotCard key={snapshot.id} snapshot={snapshot} title="外部资源快照" />
          ))}
        </div>
      ) : null}

      <section style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 24, display: "grid", gap: 14, minHeight: 320, padding: 18 }}>
        <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
          <strong style={{ color: "#0f172a", fontSize: 18 }}>{outputTitle}</strong>
          <span style={{ color: "#64748b", fontSize: 13 }}>
            {entries.length + analysisRuns.length > 0 ? `${entries.length + analysisRuns.length} 次分析记录` : "还没有分析记录"}
          </span>
        </div>

        {entries.length === 0 && analysisRuns.length === 0 && !isSubmitting && !isLoadingRuns ? (
          <div style={{ color: "#64748b", lineHeight: 1.8, minHeight: 180, padding: 8 }}>
            先开始一轮分析。这里会显示后台运行状态、系统结论、追踪链接和有依据的资料来源。
          </div>
        ) : null}

        {analysisRuns.map((run) => (
          <section key={run.id} style={{ ...panelStyle, gap: 10 }}>
            <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between", gap: 10 }}>
              <strong style={{ color: "#0f172a" }}>{run.question}</strong>
              <span style={{ color: "#475569", fontSize: 13 }}>{run.status}</span>
            </div>
            <div style={{ color: "#475569", fontSize: 13 }}>
              分析焦点：{run.analysis_focus ?? "等待系统确定"}
              {run.search_query ? ` | 搜索词：${run.search_query}` : ""}
            </div>
            {run.answer ? <div style={{ color: "#1e293b", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>{run.answer}</div> : null}
            {run.run_memory ? <div style={{ color: "#475569", fontSize: 13 }}>压缩后的运行记忆：{run.run_memory.summary}</div> : null}
            {run.degraded_reason ? <div style={{ color: "#9a3412", fontSize: 13 }}>降级原因：{run.degraded_reason}</div> : null}
            <ToolStepList toolSteps={run.tool_steps} />
            {run.external_resource_snapshot ? <SnapshotCard snapshot={run.external_resource_snapshot} title="本次运行使用的外部资源快照" /> : null}
            <SourceList sources={run.sources} traceId={run.trace_id ?? null} />
          </section>
        ))}

        {entries.map((entry) => (
          <section key={entry.traceId} style={{ ...panelStyle, gap: 10 }}>
            <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700 }}>你的问题</div>
            <div style={{ color: "#0f172a", lineHeight: 1.7 }}>{entry.question}</div>
            <div style={{ alignItems: "center", display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span style={{ backgroundColor: "#e0f2fe", borderRadius: 999, color: "#0c4a6e", fontSize: 12, fontWeight: 700, padding: "4px 10px" }}>{assistantLabel}</span>
              {entry.mode === "research_tool_assisted" ? <span style={{ backgroundColor: "#ecfccb", borderRadius: 999, color: "#3f6212", fontSize: 12, fontWeight: 700, padding: "4px 10px" }}>工具辅助试点</span> : null}
              {entry.mode === "research_external_context" ? <span style={{ backgroundColor: "#ede9fe", borderRadius: 999, color: "#5b21b6", fontSize: 12, fontWeight: 700, padding: "4px 10px" }}>外部信息试点</span> : null}
              <span style={{ color: "#64748b", fontSize: 12 }}>追踪 ID：{entry.traceId}</span>
            </div>
            <div style={{ color: "#1e293b", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>{entry.answer}</div>
            <ToolStepList toolSteps={entry.toolSteps} />
            {entry.externalResourceSnapshot ? <SnapshotCard snapshot={entry.externalResourceSnapshot} title="本次使用的外部资源快照" /> : null}
            <SourceList sources={entry.sources} traceId={entry.traceId} />
          </section>
        ))}
      </section>
    </section>
  );
}
