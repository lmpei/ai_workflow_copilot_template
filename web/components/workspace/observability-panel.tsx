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
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
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

function getTraceString(trace: TraceRecord, key: string): string | null {
  return readString(trace.response_json[key]) ?? readString(trace.metadata_json[key]);
}

function getTraceBoolean(trace: TraceRecord, key: string): boolean | null {
  return readBoolean(trace.response_json[key]) ?? readBoolean(trace.metadata_json[key]);
}

function getTraceNumber(trace: TraceRecord, key: string): number | null {
  return readNumber(trace.response_json[key]) ?? readNumber(trace.metadata_json[key]);
}

function getPilotDegradedReason(trace: TraceRecord): string | null {
  return getTraceString(trace, "degraded_reason");
}

function getConnectorId(trace: TraceRecord): string | null {
  return getTraceString(trace, "connector_id");
}

function getConnectorConsentState(trace: TraceRecord): string | null {
  return getTraceString(trace, "connector_consent_state");
}

function getExternalContextUsed(trace: TraceRecord): boolean | null {
  return getTraceBoolean(trace, "external_context_used");
}

function getExternalMatchCount(trace: TraceRecord): number | null {
  return getTraceNumber(trace, "external_match_count");
}

function getContextSelectionMode(trace: TraceRecord): string | null {
  return getTraceString(trace, "context_selection_mode");
}

function getMcpServerId(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_server_id");
}

function getMcpEndpointSource(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_endpoint_source");
}

function getMcpEndpointDisplayName(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_endpoint_display_name");
}

function getMcpEndpointAuthState(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_endpoint_auth_state");
}

function getMcpEndpointAuthDetail(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_endpoint_auth_detail");
}

function getMcpResourceId(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_resource_id");
}

function getMcpResourceUri(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_resource_uri");
}

function getMcpResourceDisplayName(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_resource_display_name");
}

function getMcpTransport(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_transport");
}

function getMcpReadStatus(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_read_status");
}

function getMcpTransportError(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_transport_error");
}

function getMcpToolName(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_tool_name");
}

function getMcpPromptName(trace: TraceRecord): string | null {
  return getTraceString(trace, "mcp_prompt_name");
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

function renderJson(payload: JsonObject): string {
  return JSON.stringify(payload, null, 2);
}

function formatConsentState(state: string | null | undefined): string {
  if (state === "granted") return "已授权";
  if (state === "revoked") return "已撤销";
  if (state === "not_granted") return "未授权";
  return "未记录";
}

function formatResourceSelectionMode(mode: ResearchAnalysisReviewRecord["resource_selection_mode"]): string {
  if (mode === "explicit") return "显式选择";
  if (mode === "auto") return "自动生成";
  return "未使用快照";
}

function formatContextSelectionMode(
  mode: ResearchAnalysisReviewRecord["context_selection_mode"] | string | null | undefined,
): string {
  if (mode === "snapshot") return "资源快照";
  if (mode === "mcp_resource") return "MCP 资源";
  return "未使用";
}

function formatMcpTransport(transport: string | null | undefined): string {
  if (transport === "stdio_process") return "子进程 stdio";
  if (transport === "local_inproc") return "进程内本地";
  return "未记录";
}

function formatMcpReadStatus(status: string | null | undefined): string {
  if (status === "consent_required") return "未授权，未尝试读取";
  if (status === "consent_revoked") return "授权已撤销，未尝试读取";
  if (status === "auth_required") return "端点要求认证，但当前没有可用凭据";
  if (status === "auth_denied") return "远程端点拒绝当前凭据";
  if (status === "snapshot_reused") return "复用已选快照，未读取远程 MCP";
  if (status === "used") return "已成功读取并使用远程 MCP";
  if (status === "transport_unavailable") return "远程 MCP 暂时不可用";
  if (status === "no_useful_matches") return "已读取远程 MCP，但没有有效内容";
  return "未记录";
}

function formatMcpEndpointSource(source: string | null | undefined): string {
  if (source === "external_configured") return "外部配置端点";
  if (source === "repo_local") return "仓库内基线端点";
  return "未记录";
}

function formatMcpEndpointAuthState(state: string | null | undefined): string {
  if (state === "configured") return "已配置";
  if (state === "missing") return "缺少认证";
  if (state === "denied") return "认证被拒";
  if (state === "not_required") return "不需要认证";
  return "未记录";
}

function getPilotOutcomeLabel(trace: TraceRecord): string {
  if (trace.error_message) return "试点失败";

  const degradedReason = getPilotDegradedReason(trace);
  if (degradedReason === "no_documents") return "诚实降级：没有资料";
  if (degradedReason === "no_grounded_matches") return "诚实降级：没有命中有依据的内容";
  if (degradedReason === "connector_consent_required") return "诚实降级：工作区尚未授权外部信息";
  if (degradedReason === "connector_consent_revoked") return "诚实降级：外部信息授权已撤销";
  if (degradedReason === "external_context_unavailable") return "诚实降级：远程 MCP 暂时不可用";
  if (degradedReason === "external_context_no_useful_matches") return "诚实降级：远程 MCP 没有有效内容";
  if (degradedReason === "selected_external_resource_snapshot_empty") return "诚实降级：选中的资源快照为空";

  if (getExternalContextUsed(trace) === true) return "已使用外部信息";

  const sources = trace.response_json["sources"];
  if (Array.isArray(sources) && sources.length > 0) return "已有有依据的结果";

  return "试点已完成";
}

function formatReviewIssue(issue: string): string {
  switch (issue) {
    case "run_failed":
      return "运行失败，需要人工查看错误原因。";
    case "missing_trace_link":
      return "缺少 trace 关联。";
    case "invalid_trace_type":
      return "trace 类型不是预期的 AI 前沿研究运行类型。";
    case "missing_prompt":
      return "trace 里没有保留 prompt。";
    case "missing_answer":
      return "运行结束后没有留下答案。";
    case "missing_tool_steps":
      return "工具步骤不可见。";
    case "missing_run_memory":
      return "运行记忆不可见。";
    case "missing_grounding_or_honest_degraded_reason":
      return "既没有依据来源，也没有诚实降级原因。";
    case "missing_resumed_memory_visibility":
      return "续跑来源没有被正确暴露。";
    case "missing_connector_id_visibility":
      return "连接器标识不可见。";
    case "missing_connector_consent_state_visibility":
      return "连接器授权状态不可见。";
    case "missing_external_context_usage_visibility":
      return "是否使用外部信息不可见。";
    case "missing_external_match_count_visibility":
      return "外部命中数量不可见。";
    case "missing_selected_resource_snapshot_visibility":
      return "显式选择的资源快照不可见。";
    case "missing_resource_snapshot_visibility":
      return "实际使用的资源快照不可见。";
    case "inconsistent_external_context_visibility":
      return "外部信息使用状态和来源可见性不一致。";
    case "inconsistent_resource_selection_visibility":
      return "资源选择方式和实际快照使用不一致。";
    case "missing_mcp_server_visibility":
      return "MCP 服务标识不可见。";
    case "missing_mcp_endpoint_visibility":
      return "MCP 端点信息不可见。";
    case "missing_mcp_auth_state_visibility":
      return "MCP 认证状态不可见。";
    case "missing_mcp_auth_detail_visibility":
      return "MCP 认证细节不可见。";
    case "missing_mcp_resource_visibility":
      return "MCP 资源标识不可见。";
    case "missing_mcp_tool_visibility":
      return "MCP 工具标识不可见。";
    case "missing_mcp_prompt_visibility":
      return "MCP 提示标识不可见。";
    case "missing_mcp_transport_visibility":
      return "MCP 传输方式不可见。";
    case "missing_remote_mcp_read_status_visibility":
      return "远程 MCP 读取状态不可见。";
    case "missing_mcp_transport_error_visibility":
      return "远程 MCP 传输错误不可见。";
    case "inconsistent_remote_mcp_outcome_visibility":
      return "远程 MCP 读取结果与最终运行状态不一致。";
    case "inconsistent_connector_consent_lifecycle":
      return "授权生命周期和运行结果不一致。";
    default:
      return issue;
  }
}

function renderReviewCard(review: ResearchAnalysisReviewRecord) {
  const selectedSnapshotLabel =
    review.selected_external_resource_snapshot_title ?? review.selected_external_resource_snapshot_id ?? "未记录";
  const usedSnapshotLabel =
    review.external_resource_snapshot_title ?? review.external_resource_snapshot_id ?? "未记录";

  return (
    <div
      key={review.run_id}
      style={{
        backgroundColor: "#ffffff",
        border: `1px solid ${review.passed ? "#bbf7d0" : "#fecaca"}`,
        borderRadius: 12,
        display: "grid",
        gap: 8,
        padding: 12,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
        <strong style={{ color: "#0f172a" }}>{review.question}</strong>
        <span
          style={{
            backgroundColor: review.passed ? "#dcfce7" : "#fee2e2",
            borderRadius: 999,
            color: review.passed ? "#166534" : "#b91c1c",
            fontSize: 12,
            padding: "2px 8px",
          }}
        >
          {review.passed ? "通过" : "需复核"}
        </span>
      </div>
      <div style={{ color: "#475569", fontSize: 13 }}>
        状态：{review.status} | 模式：{review.mode} | 结束时间：
        {review.completed_at ? new Date(review.completed_at).toLocaleString() : "未结束"}
      </div>
      {review.trace_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>Trace：{review.trace_id}</div>
      ) : null}
      {review.connector_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          连接器：{review.connector_id} | 授权：{formatConsentState(review.connector_consent_state)}
        </div>
      ) : null}
      {review.connector_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          外部信息：
          {review.external_context_used === true ? "已使用" : review.external_context_used === false ? "未使用" : "未记录"}
          {typeof review.external_match_count === "number" ? ` | 命中数：${review.external_match_count}` : ""}
        </div>
      ) : null}
      <div style={{ color: "#475569", fontSize: 13 }}>
        上下文路径：{formatContextSelectionMode(review.context_selection_mode)} | 快照选择：
        {formatResourceSelectionMode(review.resource_selection_mode)}
      </div>
      {review.context_selection_mode === "snapshot" ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          已选快照：{selectedSnapshotLabel} | 实际使用快照：{usedSnapshotLabel}
        </div>
      ) : null}
      {review.connector_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          端点来源：{formatMcpEndpointSource(review.mcp_endpoint_source)} | 认证状态：
          {formatMcpEndpointAuthState(review.mcp_endpoint_auth_state)}
          {review.mcp_endpoint_display_name ? ` | 端点：${review.mcp_endpoint_display_name}` : ""}
        </div>
      ) : null}
      {review.mcp_endpoint_auth_detail ? (
        <div style={{ color: "#b45309", fontSize: 13 }}>认证细节：{review.mcp_endpoint_auth_detail}</div>
      ) : null}
      {review.mcp_transport_error ? (
        <div style={{ color: "#b45309", fontSize: 13 }}>MCP 传输错误：{review.mcp_transport_error}</div>
      ) : null}
      {review.context_selection_mode === "mcp_resource" ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          MCP 服务：{review.mcp_server_id ?? "未记录"}
          {review.mcp_resource_display_name ? ` | MCP 资源：${review.mcp_resource_display_name}` : ""}
          {review.mcp_tool_name ? ` | MCP 工具：${review.mcp_tool_name}` : ""}
          {review.mcp_prompt_name ? ` | MCP 提示：${review.mcp_prompt_name}` : ""}
          {review.mcp_resource_uri ? ` | URI：${review.mcp_resource_uri}` : ""}
        </div>
      ) : null}
      {review.connector_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>
          MCP 传输：{formatMcpTransport(review.mcp_transport)} | 读取状态：
          {formatMcpReadStatus(review.mcp_read_status)}
        </div>
      ) : null}
      {review.resumed_from_run_id ? (
        <div style={{ color: "#475569", fontSize: 13 }}>续跑来源：{review.resumed_from_run_id}</div>
      ) : null}
      {review.degraded_reason ? (
        <div style={{ color: "#475569", fontSize: 13 }}>降级原因：{review.degraded_reason}</div>
      ) : null}
      {review.run_memory_summary ? (
        <div style={{ color: "#334155" }}>
          <strong>运行记忆摘要：</strong> {review.run_memory_summary}
        </div>
      ) : null}
      {review.issues.length > 0 ? (
        <div style={{ display: "grid", gap: 4 }}>
          <strong style={{ color: "#0f172a" }}>复核问题</strong>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {review.issues.map((issue) => (
              <li key={`${review.run_id}-${issue}`} style={{ color: "#475569" }}>
                {formatReviewIssue(issue)}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div style={{ color: "#166534" }}>这条运行满足当前 MCP 学习闭环基线。</div>
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
      setSnapshots([]);
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
      description="查看这个工作区最近持久化的聊天、运行和 MCP 试点可见性。"
    >
      <div style={{ display: "flex", gap: 12, justifyContent: "space-between", marginBottom: 12 }}>
        <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
          这里会展示最近的 trace、AI 前沿研究运行复核，以及最近保存的外部资源快照。
        </p>
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
          <strong style={{ color: "#0f172a" }}>AI 前沿研究运行复核</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            基线版本 {review.baseline_version} 已复核最近 {review.reviewed_count} 个结束态运行，其中 {review.passing_count} 个通过，
            {review.failing_count} 个需要人工复核。
          </p>
          <div style={{ display: "grid", gap: 8 }}>{review.items.map(renderReviewCard)}</div>
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
          <strong style={{ color: "#0f172a" }}>研究试点追踪概览</strong>
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
            这些快照表示最近真正进入分析链路的外部资源结果，便于核对当前 AI 前沿研究路径到底用了哪些外部上下文。
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
          const analysisFocus = getTraceString(trace, "analysis_focus");
          const searchQuery = getTraceString(trace, "search_query");
          const toolSteps = readToolSteps(trace);
          const degradedReason = getPilotDegradedReason(trace);
          const resumedFromRunId = getTraceString(trace, "resumed_from_run_id");
          const runMemory = (trace.response_json["run_memory"] ?? trace.metadata_json["run_memory"]) as
            | JsonObject
            | undefined;
          const runMemorySummary = runMemory ? readString(runMemory["summary"]) : null;
          const runMemoryNextStep = runMemory ? readString(runMemory["recommended_next_step"]) : null;
          const connectorId = getConnectorId(trace);
          const connectorConsentState = getConnectorConsentState(trace);
          const externalContextUsed = getExternalContextUsed(trace);
          const externalMatchCount = getExternalMatchCount(trace);
          const contextSelectionMode = getContextSelectionMode(trace);
          const mcpServerId = getMcpServerId(trace);
          const mcpEndpointSource = getMcpEndpointSource(trace);
          const mcpEndpointDisplayName = getMcpEndpointDisplayName(trace);
          const mcpEndpointAuthState = getMcpEndpointAuthState(trace);
          const mcpEndpointAuthDetail = getMcpEndpointAuthDetail(trace);
          const mcpResourceId = getMcpResourceId(trace);
          const mcpResourceUri = getMcpResourceUri(trace);
          const mcpResourceDisplayName = getMcpResourceDisplayName(trace);
          const mcpToolName = getMcpToolName(trace);
          const mcpPromptName = getMcpPromptName(trace);
          const mcpTransport = getMcpTransport(trace);
          const mcpReadStatus = getMcpReadStatus(trace);
          const mcpTransportError = getMcpTransportError(trace);

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
              <div>Trace ID：{trace.id}</div>
              <div>延迟：{trace.latency_ms} 毫秒</div>
              <div>
                Token 用量：输入 {trace.token_input} / 输出 {trace.token_output}
              </div>
              <div>估算成本：{formatCost(trace.estimated_cost)}</div>
              {trace.task_id ? <div>任务 ID：{trace.task_id}</div> : null}
              {trace.agent_run_id ? <div>智能体运行 ID：{trace.agent_run_id}</div> : null}
              {trace.tool_call_id ? <div>工具调用 ID：{trace.tool_call_id}</div> : null}
              {trace.eval_run_id ? <div>评测运行 ID：{trace.eval_run_id}</div> : null}
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
                  {isExternalContextTrace(trace) ? (
                    <div>
                      <strong>上下文路径：</strong> {formatContextSelectionMode(contextSelectionMode)}
                    </div>
                  ) : null}
                  {connectorId ? (
                    <div>
                      <strong>MCP 传输：</strong> {formatMcpTransport(mcpTransport)} | <strong>读取状态：</strong>
                      {formatMcpReadStatus(mcpReadStatus)}
                    </div>
                  ) : null}
                  {connectorId ? (
                    <div>
                      <strong>端点来源：</strong> {formatMcpEndpointSource(mcpEndpointSource)} | <strong>认证状态：</strong>
                      {formatMcpEndpointAuthState(mcpEndpointAuthState)}
                      {mcpEndpointDisplayName ? ` | 端点：${mcpEndpointDisplayName}` : ""}
                    </div>
                  ) : null}
                  {mcpEndpointAuthDetail ? (
                    <div>
                      <strong>认证细节：</strong> {mcpEndpointAuthDetail}
                    </div>
                  ) : null}
                  {mcpTransportError ? (
                    <div>
                      <strong>MCP 传输错误：</strong> {mcpTransportError}
                    </div>
                  ) : null}
                  {mcpServerId || mcpResourceId || mcpResourceDisplayName || mcpResourceUri ? (
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong>MCP 资源信息</strong>
                      {mcpServerId ? <div>服务：{mcpServerId}</div> : null}
                      {mcpResourceDisplayName ? <div>资源：{mcpResourceDisplayName}</div> : null}
                      {mcpResourceId ? <div>资源 ID：{mcpResourceId}</div> : null}
                      {mcpResourceUri ? <div>URI：{mcpResourceUri}</div> : null}
                    </div>
                  ) : null}
                  {mcpToolName || mcpPromptName ? (
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong>MCP 工具与提示</strong>
                      {mcpToolName ? <div>工具：{mcpToolName}</div> : null}
                      {mcpPromptName ? <div>提示：{mcpPromptName}</div> : null}
                    </div>
                  ) : null}
                  {degradedReason ? (
                    <div>
                      <strong>降级原因：</strong> {degradedReason}
                    </div>
                  ) : null}
                  {resumedFromRunId ? (
                    <div>
                      <strong>续跑来源：</strong> {resumedFromRunId}
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
                <summary>查看追踪载荷</summary>
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
