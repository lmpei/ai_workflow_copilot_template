"use client";

import type { CSSProperties, FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  createWorkspaceResearchAnalysisRun,
  getResearchAnalysisRun,
  getWorkspaceConnectorStatus,
  isApiClientError,
  listWorkspaceAiFrontierResearchRecords,
  listWorkspaceResearchAnalysisRuns,
  listWorkspaceResearchExternalResourceSnapshots,
  sendWorkspaceChat,
} from "../../lib/api";
import type {
  AiFrontierResearchOutputRecord,
  AiFrontierResearchRecord,
  ChatSource,
  ChatToolStep,
  ResearchAnalysisRunRecord,
  ResearchAnalysisRunStatus,
  ResearchExternalResourceSnapshotRecord,
  WorkspaceConnectorStatusRecord,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import AiFrontierOutputCard from "../research/ai-frontier-output-card";
import SectionCard from "../ui/section-card";

type Mode = "rag" | "research_tool_assisted" | "research_external_context";

type ChatEntry = {
  question: string;
  answer: string;
  traceId: string;
  mode: Mode;
  toolSteps: ChatToolStep[];
  sources: ChatSource[];
  externalResourceSnapshot?: ResearchExternalResourceSnapshotRecord | null;
  frontierOutput?: AiFrontierResearchOutputRecord | null;
  researchRecord?: AiFrontierResearchRecord | null;
};

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
  modes?: Array<{ value: Mode; label: string; description: string }>;
  defaultMode?: Mode;
  supportsBackgroundRuns?: boolean;
  showModePicker?: boolean;
  showConnectorControls?: boolean;
  showSnapshotPicker?: boolean;
  showToolSteps?: boolean;
  showRecentRecords?: boolean;
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

const RUN_ACTIVE: ResearchAnalysisRunStatus[] = ["pending", "running"];
const CONNECTOR_ID = "research_external_context";

const panelStyle: CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #dbe4f0",
  borderRadius: 24,
  display: "grid",
  gap: 18,
  padding: 20,
};

const mergeById = <T extends { id: string; created_at: string }>(current: T[], incoming: T[]) => {
  const byId = new Map<string, T>();
  [...current, ...incoming].forEach((item) => byId.set(item.id, item));
  return [...byId.values()].sort((a, b) => b.created_at.localeCompare(a.created_at));
};

const mergeRuns = (current: ResearchAnalysisRunRecord[], incoming: ResearchAnalysisRunRecord[]) => mergeById(current, incoming);
const mergeSnapshots = (current: ResearchExternalResourceSnapshotRecord[], incoming: ResearchExternalResourceSnapshotRecord[]) =>
  mergeById(current, incoming);
const mergeRecords = (current: AiFrontierResearchRecord[], incoming: AiFrontierResearchRecord[]) => mergeById(current, incoming);

function formatDateTime(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "";
}

function SourceList({ sources }: { sources: ChatSource[] }) {
  if (!sources.length) {
    return null;
  }

  return (
    <details>
      <summary style={{ cursor: "pointer", fontWeight: 700 }}>查看来源</summary>
      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {sources.map((source) => (
          <div
            key={`${source.document_id}-${source.chunk_id}`}
            style={{
              backgroundColor: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: 16,
              display: "grid",
              gap: 6,
              padding: 12,
            }}
          >
            <div style={{ alignItems: "baseline", display: "flex", justifyContent: "space-between", gap: 10 }}>
              <strong style={{ color: "#0f172a" }}>{source.document_title}</strong>
              <span style={{ color: "#64748b", fontSize: 12, fontWeight: 700 }}>
                {source.source_kind === "external_context" ? "外部来源" : "工作区资料"}
              </span>
            </div>
            <div style={{ color: "#64748b", fontSize: 13 }}>
              片段 {source.chunk_index} · 文档 ID：{source.document_id}
            </div>
            <div style={{ color: "#334155", lineHeight: 1.7 }}>{source.snippet}</div>
          </div>
        ))}
      </div>
    </details>
  );
}

function ToolSteps({ toolSteps }: { toolSteps: ChatToolStep[] }) {
  if (!toolSteps.length) {
    return null;
  }

  return (
    <details>
      <summary style={{ cursor: "pointer", fontWeight: 700 }}>查看过程步骤</summary>
      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {toolSteps.map((step, index) => (
          <div
            key={`${step.tool_name}-${index}`}
            style={{
              backgroundColor: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: 16,
              display: "grid",
              gap: 4,
              padding: 12,
            }}
          >
            <strong style={{ color: "#0f172a" }}>{step.summary}</strong>
            {step.detail ? <div style={{ color: "#475569", fontSize: 13 }}>{step.detail}</div> : null}
          </div>
        ))}
      </div>
    </details>
  );
}

function ResultCard({
  question,
  answer,
  output,
  sources,
  toolSteps,
  showToolSteps,
  footer,
}: {
  question: string;
  answer?: string | null;
  output?: AiFrontierResearchOutputRecord | null;
  sources: ChatSource[];
  toolSteps: ChatToolStep[];
  showToolSteps: boolean;
  footer?: string;
}) {
  return (
    <section style={panelStyle}>
      <div style={{ display: "grid", gap: 6 }}>
        <span
          style={{
            color: "#64748b",
            fontSize: 12,
            fontWeight: 800,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          Current Result
        </span>
        <strong style={{ color: "#0f172a", fontSize: 20 }}>本次追踪结果</strong>
        <p style={{ color: "#475569", lineHeight: 1.8, margin: 0 }}>{question}</p>
      </div>

      <div style={{ color: "#334155", lineHeight: 1.85, whiteSpace: "pre-wrap" }}>
        {answer || "当前还没有生成最终结果。"}
      </div>

      <AiFrontierOutputCard output={output} title="热点追踪输出" />
      {showToolSteps ? <ToolSteps toolSteps={toolSteps} /> : null}
      <SourceList sources={sources} />
      {footer ? <div style={{ color: "#64748b", fontSize: 12 }}>{footer}</div> : null}
    </section>
  );
}

export default function ChatPanel({
  workspaceId,
  assistantLabel = "AI 热点追踪",
  workflowLabel = "AI 热点追踪",
  introTitle = "开始一次热点追踪",
  introBody = "围绕最新高可信来源提炼 AI 行业变化、关键事件和值得跟进的项目与框架。",
  placeholder = "例如：总结最近值得持续关注的 Agent、MCP 和开源框架变化，并指出哪些项目值得继续跟进。",
  suggestedPrompts,
  primaryActionLabel = "开始追踪",
  outputTitle = "本次追踪结果",
  modes,
  defaultMode = "rag",
  supportsBackgroundRuns = false,
  showModePicker = true,
  showConnectorControls = true,
  showSnapshotPicker = true,
  showToolSteps = true,
  showRecentRecords = true,
  onStatusChange,
}: ChatPanelProps) {
  const { session, isReady } = useAuthSession();
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [analysisRuns, setAnalysisRuns] = useState<ResearchAnalysisRunRecord[]>([]);
  const [recentSnapshots, setRecentSnapshots] = useState<ResearchExternalResourceSnapshotRecord[]>([]);
  const [recentRecords, setRecentRecords] = useState<AiFrontierResearchRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [connectorStatus, setConnectorStatus] = useState<WorkspaceConnectorStatusRecord | null>(null);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null);

  const availableModes = useMemo(
    () =>
      modes?.length
        ? modes
        : [
            {
              value: "rag" as const,
              label: "标准分析",
              description: "直接基于当前资料形成一次有依据的结果。",
            },
          ],
    [modes],
  );

  const [mode, setMode] = useState<Mode>(defaultMode);
  const prompts = useMemo(
    () =>
      suggestedPrompts?.length
        ? suggestedPrompts
        : [
            "总结最近最值得关注的 AI 热点变化。",
            "指出当前最值得持续跟进的主题、事件和项目。",
            "告诉我哪些判断还需要更多原始来源来验证。",
          ],
    [suggestedPrompts],
  );

  const activeRuns = useMemo(() => analysisRuns.filter((run) => RUN_ACTIVE.includes(run.status)), [analysisRuns]);
  const latestRun = analysisRuns[0] ?? null;
  const latestEntry = entries.at(-1) ?? null;
  const latestRecord = recentRecords[0] ?? latestEntry?.researchRecord ?? latestRun?.research_record ?? null;
  const latestResult = latestEntry
    ? {
        question: latestEntry.question,
        answer: latestEntry.answer,
        output: latestEntry.frontierOutput,
        sources: latestEntry.sources,
        toolSteps: latestEntry.toolSteps,
        footer: latestRecord ? `已沉淀为记录：${latestRecord.title}` : undefined,
      }
    : latestRun
      ? {
          question: latestRun.question,
          answer: latestRun.answer,
          output: latestRun.frontier_output,
          sources: latestRun.sources,
          toolSteps: latestRun.tool_steps,
          footer: latestRun.completed_at ? `完成于 ${formatDateTime(latestRun.completed_at)}` : undefined,
        }
      : null;

  useEffect(() => {
    setMode(defaultMode);
  }, [defaultMode]);

  useEffect(() => {
    onStatusChange?.({
      entryCount: entries.length + analysisRuns.length,
      isSubmitting: isSubmitting || activeRuns.length > 0,
      currentDraft: question,
      lastTraceId: latestRun?.trace_id ?? latestEntry?.traceId ?? null,
      latestAnalysisRunId: latestRun?.id ?? null,
      latestAnalysisRunStatus: latestRun?.status ?? null,
      latestAnalysisRunQuestion: latestRun?.question ?? null,
    });
  }, [activeRuns.length, analysisRuns.length, entries.length, isSubmitting, latestEntry, latestRun, onStatusChange, question]);

  useEffect(() => {
    if (!session) {
      setAnalysisRuns([]);
      setRecentSnapshots([]);
      setRecentRecords([]);
      return;
    }

    let cancelled = false;
    const loadData = async () => {
      setIsLoading(true);
      try {
        const requests: Array<Promise<unknown>> = [];
        if (supportsBackgroundRuns) {
          requests.push(listWorkspaceResearchAnalysisRuns(session.accessToken, workspaceId, 8));
        } else {
          requests.push(Promise.resolve([]));
        }
        if (showSnapshotPicker) {
          requests.push(listWorkspaceResearchExternalResourceSnapshots(session.accessToken, workspaceId, 8));
        } else {
          requests.push(Promise.resolve([]));
        }
        if (showRecentRecords) {
          requests.push(listWorkspaceAiFrontierResearchRecords(session.accessToken, workspaceId, 8));
        } else {
          requests.push(Promise.resolve([]));
        }

        const [runs, snapshots, records] = await Promise.all(requests);
        if (!cancelled) {
          setAnalysisRuns(runs as ResearchAnalysisRunRecord[]);
          setRecentSnapshots(snapshots as ResearchExternalResourceSnapshotRecord[]);
          setRecentRecords(records as AiFrontierResearchRecord[]);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "无法加载追踪数据。");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadData();
    return () => {
      cancelled = true;
    };
  }, [session, showRecentRecords, showSnapshotPicker, supportsBackgroundRuns, workspaceId]);

  useEffect(() => {
    if (!session || !activeRuns.length) {
      return;
    }

    let cancelled = false;
    const refresh = async () => {
      try {
        const refreshed = await Promise.all(activeRuns.map((run) => getResearchAnalysisRun(session.accessToken, run.id)));
        if (!cancelled) {
          setAnalysisRuns((current) => mergeRuns(current, refreshed));
          setRecentRecords((current) =>
            mergeRecords(
              current,
              refreshed.flatMap((run) => (run.research_record ? [run.research_record] : [])),
            ),
          );
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "刷新后台运行状态失败。");
        }
      }
    };

    void refresh();
    const timer = window.setInterval(() => {
      void refresh();
    }, 2500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeRuns, session]);

  useEffect(() => {
    if (!session || !showConnectorControls || mode !== "research_external_context") {
      setConnectorStatus(null);
      return;
    }

    let cancelled = false;
    const loadStatus = async () => {
      try {
        const status = await getWorkspaceConnectorStatus(session.accessToken, workspaceId, CONNECTOR_ID);
        if (!cancelled) {
          setConnectorStatus(status);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "无法读取外部来源状态。");
        }
      }
    };

    void loadStatus();
    return () => {
      cancelled = true;
    };
  }, [mode, session, showConnectorControls, workspaceId]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
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
          external_resource_snapshot_id: mode === "research_external_context" ? selectedSnapshotId ?? undefined : undefined,
        });
        setAnalysisRuns((current) => mergeRuns(current, [run]));
        const researchRecord = run.research_record;
        if (researchRecord) {
          setRecentRecords((current) => mergeRecords(current, [researchRecord]));
        }
      } else {
        const response = await sendWorkspaceChat(session.accessToken, workspaceId, {
          question: trimmedQuestion,
          mode,
          external_resource_snapshot_id: mode === "research_external_context" ? selectedSnapshotId ?? undefined : undefined,
        });
        setEntries((current) => [
          ...current,
          {
            question: trimmedQuestion,
            answer: response.answer,
            traceId: response.trace_id,
            mode: response.mode,
            toolSteps: response.tool_steps,
            sources: response.sources,
            externalResourceSnapshot: response.external_resource_snapshot ?? null,
            frontierOutput: response.frontier_output ?? null,
            researchRecord: response.research_record ?? null,
          },
        ]);
        const researchRecord = response.research_record;
        if (researchRecord) {
          setRecentRecords((current) => mergeRecords(current, [researchRecord]));
        }
      }
      setQuestion("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "提交追踪请求时失败。");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="AI 热点追踪">正在加载工作流...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="请先登录，再进入 AI 热点追踪工作流。" />;
  }

  return (
    <section style={panelStyle}>
      <div style={{ display: "grid", gap: 10 }}>
        <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "space-between" }}>
          <div style={{ display: "grid", gap: 4 }}>
            <span
              style={{
                color: "#64748b",
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
              }}
            >
              {workflowLabel}
            </span>
            <strong style={{ color: "#0f172a", fontSize: 24 }}>{introTitle}</strong>
          </div>
          {activeRuns.length > 0 ? <span style={{ color: "#0f766e", fontSize: 13 }}>后台分析进行中</span> : null}
        </div>

        <p style={{ color: "#475569", lineHeight: 1.8, margin: 0 }}>{introBody}</p>

        {showModePicker && availableModes.length > 1 ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {availableModes.map((item) => (
                <button key={item.value} onClick={() => setMode(item.value)} type="button">
                  {item.label}
                </button>
              ))}
            </div>
            <div style={{ color: "#475569", fontSize: 14, lineHeight: 1.7 }}>
              {availableModes.find((item) => item.value === mode)?.description}
            </div>
          </div>
        ) : null}

        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {prompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => setQuestion(prompt)}
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #dbe4f0",
                borderRadius: 999,
                color: "#0f172a",
                fontSize: 13,
                fontWeight: 700,
                padding: "8px 12px",
              }}
              type="button"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {showConnectorControls && connectorStatus && mode === "research_external_context" ? (
        <section
          style={{
            backgroundColor: connectorStatus.consent_state === "granted" ? "#ecfdf5" : "#fff7ed",
            border: `1px solid ${connectorStatus.consent_state === "granted" ? "#bbf7d0" : "#fed7aa"}`,
            borderRadius: 18,
            color: "#475569",
            display: "grid",
            gap: 6,
            padding: 16,
          }}
        >
          <strong style={{ color: "#0f172a" }}>
            {connectorStatus.consent_state === "granted" ? "外部来源已可用" : "外部来源尚未可用"}
          </strong>
          <div>
            {connectorStatus.consent_state === "granted"
              ? "当前工作区可以结合外部最新来源。"
              : "当前工作区还没有外部来源权限，本次会先基于现有资料形成结果。"}
          </div>
        </section>
      ) : null}

      {showSnapshotPicker && mode === "research_external_context" && recentSnapshots.length > 0 ? (
        <section
          style={{
            backgroundColor: "#f8fafc",
            border: "1px solid #dbe4f0",
            borderRadius: 18,
            display: "grid",
            gap: 12,
            padding: 16,
          }}
        >
          <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between", gap: 10 }}>
            <strong style={{ color: "#0f172a" }}>最近外部快照</strong>
            <button onClick={() => setSelectedSnapshotId(null)} type="button">
              {selectedSnapshotId ? "改为自动选择" : "当前为自动选择"}
            </button>
          </div>
          <div style={{ display: "grid", gap: 10 }}>
            {recentSnapshots.map((snapshot) => (
              <button
                key={snapshot.id}
                onClick={() => setSelectedSnapshotId(snapshot.id)}
                style={{
                  backgroundColor: snapshot.id === selectedSnapshotId ? "#ecfeff" : "#ffffff",
                  border: `1px solid ${snapshot.id === selectedSnapshotId ? "#0891b2" : "#dbe4f0"}`,
                  borderRadius: 16,
                  display: "grid",
                  gap: 6,
                  padding: 12,
                  textAlign: "left",
                }}
                type="button"
              >
                <strong style={{ color: "#0f172a" }}>{snapshot.title}</strong>
                <span style={{ color: "#475569", fontSize: 13 }}>搜索词：{snapshot.search_query}</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 8 }}>
          <span style={{ color: "#0f172a", fontSize: 14, fontWeight: 800 }}>{assistantLabel}问题</span>
          <textarea
            onChange={(event) => setQuestion(event.target.value)}
            placeholder={placeholder}
            required
            rows={5}
            style={{
              backgroundColor: "#f8fafc",
              border: "1px solid #cbd5e1",
              borderRadius: 20,
              minHeight: 140,
              padding: "16px 18px",
              resize: "vertical",
            }}
            value={question}
          />
        </label>
        {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
        <div>
          <button
            disabled={isSubmitting}
            style={{
              backgroundColor: "#0f172a",
              border: "none",
              borderRadius: 999,
              color: "#ffffff",
              fontSize: 14,
              fontWeight: 800,
              minHeight: 44,
              padding: "0 18px",
            }}
            type="submit"
          >
            {isSubmitting ? "追踪中..." : primaryActionLabel}
          </button>
        </div>
      </form>

      <section style={{ display: "grid", gap: 14 }}>
        <div style={{ alignItems: "baseline", display: "flex", justifyContent: "space-between", gap: 10 }}>
          <strong style={{ color: "#0f172a", fontSize: 20 }}>{outputTitle}</strong>
          {isLoading ? <span style={{ color: "#64748b", fontSize: 13 }}>正在刷新数据...</span> : null}
        </div>
        {!latestResult ? (
          <div
            style={{
              backgroundColor: "#f8fafc",
              border: "1px solid #dbe4f0",
              borderRadius: 20,
              color: "#475569",
              lineHeight: 1.8,
              padding: 18,
            }}
          >
            先输入一个当前值得跟进的问题。这里会显示本次热点摘要、趋势判断、项目与框架观察，以及参考来源。
          </div>
        ) : (
          <ResultCard
            answer={latestResult.answer}
            footer={latestResult.footer}
            output={latestResult.output}
            question={latestResult.question}
            showToolSteps={showToolSteps}
            sources={latestResult.sources}
            toolSteps={latestResult.toolSteps}
          />
        )}
      </section>

      {showRecentRecords ? (
        <section style={{ display: "grid", gap: 12 }}>
          <div style={{ alignItems: "baseline", display: "flex", justifyContent: "space-between", gap: 10 }}>
            <strong style={{ color: "#0f172a", fontSize: 18 }}>最近记录</strong>
            {recentRecords.length ? <span style={{ color: "#64748b", fontSize: 13 }}>共 {recentRecords.length} 条</span> : null}
          </div>
          {recentRecords.length === 0 ? (
            <div
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #dbe4f0",
                borderRadius: 20,
                color: "#475569",
                lineHeight: 1.8,
                padding: 18,
              }}
            >
              当前还没有沉淀出的追踪记录。
            </div>
          ) : (
            recentRecords.map((record) => (
              <section
                key={record.id}
                style={{
                  backgroundColor: "#f8fafc",
                  border: "1px solid #dbe4f0",
                  borderRadius: 20,
                  display: "grid",
                  gap: 10,
                  padding: 16,
                }}
              >
                <div style={{ display: "grid", gap: 4 }}>
                  <strong style={{ color: "#0f172a" }}>{record.title}</strong>
                  <div style={{ color: "#475569", lineHeight: 1.7 }}>{record.question}</div>
                  <div style={{ color: "#64748b", fontSize: 12 }}>{formatDateTime(record.created_at)}</div>
                </div>
              </section>
            ))
          )}
        </section>
      ) : null}
    </section>
  );
}
