"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  isApiClientError,
  listWorkspaceResearchAnalysisRunReviews,
  listWorkspaceResearchExternalResourceSnapshots,
  listWorkspaceTraces,
} from "../../lib/api";
import type {
  JsonObject,
  ResearchAnalysisReviewRecord,
  ResearchAnalysisReviewResponse,
  ResearchExternalResourceSnapshotRecord,
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

function readBoolean(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function readNumber(value: unknown): number | null {
  return typeof value === "number" ? value : null;
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

function getConnectorId(trace: TraceRecord): string | null {
  return readString(trace.response_json["connector_id"]) ?? readString(trace.metadata_json["connector_id"]);
}

function getConnectorConsentState(trace: TraceRecord): string | null {
  return (
    readString(trace.response_json["connector_consent_state"]) ??
    readString(trace.metadata_json["connector_consent_state"])
  );
}

function getExternalContextUsed(trace: TraceRecord): boolean | null {
  return readBoolean(trace.response_json["external_context_used"]) ?? readBoolean(trace.metadata_json["external_context_used"]);
}

function getExternalMatchCount(trace: TraceRecord): number | null {
  return readNumber(trace.response_json["external_match_count"]) ?? readNumber(trace.metadata_json["external_match_count"]);
}

function getPilotOutcomeLabel(trace: TraceRecord): string {
  if (trace.error_message) {
    return "试点失败";
  }

  const degradedReason = getPilotDegradedReason(trace);
  if (degradedReason === "no_documents") {
    return "诚实降级：没有资料";
  }
  if (degradedReason === "no_grounded_matches") {
    return "诚实降级：没有命中有依据的内容";
  }
  if (degradedReason === "connector_consent_required") {
    return "诚实降级：工作区尚未授权外部信息";
  }
  if (degradedReason === "external_context_unavailable") {
    return "诚实降级：外部信息暂时不可用";
  }
  if (degradedReason === "external_context_no_useful_matches") {
    return "诚实降级：外部信息没有命中有用内容";
  }

  if (getExternalContextUsed(trace) === true) {
    return "已使用外部信息";
  }

  const sources = trace.response_json["sources"];
  if (Array.isArray(sources) && sources.length > 0) {
    return "已有有依据的证据";
  }

  return "试点已完成";
}

function isPilotTrace(trace: TraceRecord): boolean {
  return (
    trace.trace_type === "research_tool_assisted" ||
    trace.trace_type === "research_tool_assisted_run" ||
    trace.trace_type === "research_external_context" ||
    trace.trace_type === "research_external_context_run"
  );
}

function isExternalContextTrace(trace: TraceRecord): boolean {
  return trace.trace_type === "research_external_context" || trace.trace_type === "research_external_context_run";
}

function formatConsentState(state: string | null | undefined): string {
  if (state === "granted") {
    return "已授权";
  }
  if (state === "not_granted") {
    return "未授权";
  }
  return "未记录";
}

function renderJson(payload: JsonObject): string {
  return JSON.stringify(payload, null, 2);
}

function formatReviewIssue(issue: string): string {
  switch (issue) {
    case "run_failed":
      return "运行以失败状态结束";
    case "missing_trace_link":
      return "缺少追踪链接";
    case "invalid_trace_type":
      return "追踪类型不是预期的 Research 运行类型";
    case "missing_prompt":
      return "追踪元数据里缺少 prompt";
    case "missing_answer":
      return "非失败运行缺少回答";
    case "missing_tool_steps":
      return "工具步骤不可见";
    case "missing_run_memory":
      return "缺少压缩后的运行记忆";
    case "missing_grounding_or_honest_degraded_reason":
      return "既没有可见证据，也没有诚实降级原因";
    case "missing_resumed_memory_visibility":
      return "延续运行的记忆链路不可见";
    case "missing_connector_id_visibility":
      return "连接器标识不可见";
    case "missing_connector_consent_state_visibility":
      return "连接器授权状态不可见";
    case "missing_external_context_usage_visibility":
      return "是否使用外部信息不可见";
    case "missing_external_match_count_visibility":
      return "外部信息命中数量不可见";
    case "inconsistent_external_context_visibility":
      return "外部信息使用情况与来源展示不一致";
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
          {review.passed ? "通过" : "需要复核"}
        </span>
      </div>
      <div style={{ color: "#475569", fontSize: 13 }}>
        状态：{review.status}
        {review.trace_id ? ` | 追踪：${review.trace_id}` : ""}
      </div>
      <div style={{ color: "#475569", fontSize: 13 }}>
        模式：{review.mode === "research_external_context" ? "外部信息试点" : "工具辅助试点"}
      </div>
      {review.connector_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          连接器：{review.connector_id} | 授权状态：{formatConsentState(review.connector_consent_state)} | 外部信息：
          {review.external_context_used === true ? "已使用" : review.external_context_used === false ? "未使用" : "未记录"}
          {typeof review.external_match_count === "number" ? ` | 命中数：${review.external_match_count}` : ""}
        </div>
      ) : null}
      {review.resumed_from_run_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>延续自运行：{review.resumed_from_run_id}</div>
      ) : null}
      {review.degraded_reason ? (
        <div style={{ color: "#475569", fontSize: 13 }}>降级原因：{review.degraded_reason}</div>
      ) : null}
      {review.run_memory_summary ? (
        <div style={{ color: "#334155" }}>
          <strong>压缩后的运行记忆：</strong> {review.run_memory_summary}
        </div>
      ) : null}
      {review.issues.length > 0 ? (
        <div style={{ display: "grid", gap: 4 }}>
          <strong style={{ color: "#0f172a" }}>回归问题</strong>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {review.issues.map((issue) => (
              <li key={`${review.run_id}-${issue}`} style={{ color: "#475569" }}>
                {formatReviewIssue(issue)}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div style={{ color: "#166534" }}>这一轮运行已通过所有有边界的回归检查。</div>
      )}
    </div>
  );
}

export default function ObservabilityPanel({ workspaceId }: ObservabilityPanelProps) {
  const { session, isReady } = useAuthSession();
  const [traces, setTraces] = useState<TraceRecord[]>([]);
  const [review, setReview] = useState<ResearchAnalysisReviewResponse | null>(null);
  const [snapshots, setSnapshots] = useState<ResearchExternalResourceSnapshotRecord[]>([]);
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
      let snapshotItems: ResearchExternalResourceSnapshotRecord[] = [];
      try {
        snapshotItems = await listWorkspaceResearchExternalResourceSnapshots(session.accessToken, workspaceId, 8);
      } catch {
        snapshotItems = [];
      }
      setTraces(traceItems);
      setReview(reviewResponse);
      setSnapshots(snapshotItems);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载最近的可观测数据。");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadObservability();
  }, [loadObservability]);

  const pilotTraces = useMemo(() => traces.filter(isPilotTrace), [traces]);
  const externalPilotTraces = useMemo(() => pilotTraces.filter(isExternalContextTrace), [pilotTraces]);
  const degradedPilotCount = useMemo(
    () => pilotTraces.filter((trace) => getPilotDegradedReason(trace) !== null).length,
    [pilotTraces],
  );

  if (!isReady) {
    return <SectionCard title="可观测面">正在加载最近的追踪...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="请先登录，再查看工作区追踪和评测信号。" />;
  }

  return (
    <SectionCard
      title="最近追踪"
      description="查看这个工作区最近持久化的聊天、任务和有边界 Research 运行追踪。"
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
        <p style={{ color: "#475569", margin: 0 }}>这里会显示最近的追踪，以及后台 Research 运行的有边界回归复核结果。</p>
        <button onClick={() => void loadObservability()} type="button">
          {isLoading ? "刷新中..." : "刷新可观测面"}
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
          <strong style={{ color: "#0f172a" }}>Research 运行回归复核</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            基线版本 {review.baseline_version} 已复核最近 {review.reviewed_count} 个结束态运行，其中 {review.passing_count} 个通过，{review.failing_count} 个需要人工复核。
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
          <strong style={{ color: "#0f172a" }}>Research 试点追踪概览</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            最近 {pilotTraces.length} 条试点追踪里，有 {degradedPilotCount} 条走了诚实降级路径。
            {externalPilotTraces.length > 0 ? ` 其中 ${externalPilotTraces.length} 条属于外部信息试点。` : ""}
          </p>
        </section>
      ) : null}

      {snapshots.length > 0 ? (
        <section
          style={{
            backgroundColor: "#faf5ff",
            border: "1px solid #ddd6fe",
            borderRadius: 14,
            display: "grid",
            gap: 10,
            marginBottom: 14,
            padding: 12,
          }}
        >
          <strong style={{ color: "#581c87" }}>最近外部资源快照</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            这里保留最近真正使用过的外部资源快照，便于核对外部信息是否进入了 Research 分析链路。
          </p>
          <div style={{ display: "grid", gap: 10 }}>
            {snapshots.map((snapshot) => (
              <div
                key={snapshot.id}
                style={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #e9d5ff",
                  borderRadius: 12,
                  display: "grid",
                  gap: 6,
                  padding: 10,
                }}
              >
                <strong style={{ color: "#0f172a" }}>{snapshot.title}</strong>
                <div style={{ color: "#475569", fontSize: 13 }}>
                  搜索词：{snapshot.search_query}
                  {snapshot.analysis_focus ? ` | 分析焦点：${snapshot.analysis_focus}` : ""}
                </div>
                <div style={{ color: "#475569", fontSize: 13 }}>资源数：{snapshot.resource_count}</div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      {!isLoading && traces.length === 0 ? <p>这个工作区还没有记录任何追踪数据。</p> : null}

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
          const connectorId = getConnectorId(trace);
          const connectorConsentState = getConnectorConsentState(trace);
          const externalContextUsed = getExternalContextUsed(trace);
          const externalMatchCount = getExternalMatchCount(trace);

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
              <div>追踪 ID：{trace.id}</div>
              <div>延迟：{trace.latency_ms} 毫秒</div>
              <div>
                Token 用量：输入 {trace.token_input} / 输出 {trace.token_output}
              </div>
              <div>估算成本：{formatCost(trace.estimated_cost)}</div>
              {trace.task_id ? <div>任务 ID：{trace.task_id}</div> : null}
              {trace.agent_run_id ? <div>智能体运行 ID（agent run）：{trace.agent_run_id}</div> : null}
              {trace.tool_call_id ? <div>工具调用 ID（tool call）：{trace.tool_call_id}</div> : null}
              {trace.eval_run_id ? <div>评测运行 ID（eval run）：{trace.eval_run_id}</div> : null}
              {trace.parent_trace_id ? <div>父追踪 ID：{trace.parent_trace_id}</div> : null}
              {trace.error_message ? (
                <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 8 }}>
                  <strong>错误：</strong> {trace.error_message}
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
                    <strong style={{ color: "#0f172a" }}>试点可见性</strong>
                    <span style={{ color: "#475569", fontSize: 13 }}>{getPilotOutcomeLabel(trace)}</span>
                  </div>
                  {analysisFocus ? (
                    <div>
                      <strong>分析焦点：</strong> {analysisFocus}
                    </div>
                  ) : null}
                  {searchQuery ? (
                    <div>
                      <strong>搜索词：</strong> {searchQuery}
                    </div>
                  ) : null}
                  {connectorId ? (
                    <div>
                      <strong>连接器：</strong> {connectorId}
                    </div>
                  ) : null}
                  {connectorId ? (
                    <div>
                      <strong>授权状态：</strong> {formatConsentState(connectorConsentState)}
                    </div>
                  ) : null}
                  {connectorId ? (
                    <div>
                      <strong>外部信息：</strong>
                      {externalContextUsed === true ? "已使用" : externalContextUsed === false ? "未使用" : "未记录"}
                      {typeof externalMatchCount === "number" ? ` | 命中数：${externalMatchCount}` : ""}
                    </div>
                  ) : null}
                  {degradedReason ? (
                    <div>
                      <strong>降级原因：</strong> {degradedReason}
                    </div>
                  ) : null}
                  {resumedFromRunId ? (
                    <div>
                      <strong>延续自运行：</strong> {resumedFromRunId}
                    </div>
                  ) : null}
                  {runMemorySummary ? (
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong>压缩后的运行记忆</strong>
                      <div>{runMemorySummary}</div>
                      {runMemoryNextStep ? <div style={{ color: "#64748b" }}>下一步建议：{runMemoryNextStep}</div> : null}
                    </div>
                  ) : null}
                  {toolSteps.length > 0 ? (
                    <div style={{ display: "grid", gap: 8 }}>
                      <strong>工具步骤</strong>
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
                    <div style={{ color: "#64748b" }}>这条试点追踪没有记录可见的工具步骤。</div>
                  )}
                </section>
              ) : null}

              <details style={{ marginTop: 10 }}>
                <summary>追踪载荷</summary>
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
