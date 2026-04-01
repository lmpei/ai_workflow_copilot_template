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
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载调用轨迹");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadTraces();
  }, [loadTraces]);

  if (!isReady) {
    return <SectionCard title="可观测性">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能查看工作区调用轨迹和评测执行信号。" />;
  }

  const pilotTraces = traces.filter((trace) => trace.trace_type === "research_tool_assisted");
  const degradedPilotCount = pilotTraces.filter((trace) => getPilotDegradedReason(trace) !== null).length;

  return (
    <SectionCard title="近期调用轨迹" description="查看最近持久化的对话、任务、Agent、工具和评测执行记录。">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
        <p style={{ margin: 0, color: "#475569" }}>这里最多显示当前工作区最近的 20 条调用轨迹记录。</p>
        <button onClick={() => void loadTraces()} type="button">
          {isLoading ? "正在刷新..." : "刷新调用轨迹"}
        </button>
      </div>
      {pilotTraces.length > 0 ? (
        <section
          style={{
            backgroundColor: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: 14,
            display: "grid",
            gap: 6,
            marginBottom: 14,
            padding: 12,
          }}
        >
          <strong style={{ color: "#0f172a" }}>Research tool-assisted pilot review</strong>
          <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
            最近 {pilotTraces.length} 条试点 trace 中，有 {degradedPilotCount} 条走了诚实降级路径。这里应该能直接看见分析焦点、搜索词、工具步骤和降级原因，而不是只看原始 JSON。
          </p>
        </section>
      ) : null}
      {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      {!isLoading && traces.length === 0 ? <p>目前还没有记录任何调用轨迹。</p> : null}
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {traces.map((trace) => {
          const analysisFocus = readString(trace.response_json["analysis_focus"]) ?? readString(trace.metadata_json["analysis_focus"]);
          const searchQuery = readString(trace.response_json["search_query"]) ?? readString(trace.metadata_json["search_query"]);
          const toolSteps = readToolSteps(trace);
          const degradedReason = getPilotDegradedReason(trace);

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
              <div style={{ alignItems: "center", display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 8 }}>
                <strong>{trace.trace_type}</strong>
                <span>{new Date(trace.created_at).toLocaleString()}</span>
              </div>
              <div>调用轨迹 ID：{trace.id}</div>
              <div>延迟：{trace.latency_ms} ms</div>
              <div>Token：输入 {trace.token_input} / 输出 {trace.token_output}</div>
              <div>预估成本：{formatCost(trace.estimated_cost)}</div>
              {trace.task_id ? <div>任务 ID：{trace.task_id}</div> : null}
              {trace.agent_run_id ? <div>Agent 运行 ID：{trace.agent_run_id}</div> : null}
              {trace.tool_call_id ? <div>工具调用 ID：{trace.tool_call_id}</div> : null}
              {trace.eval_run_id ? <div>评测运行 ID：{trace.eval_run_id}</div> : null}
              {trace.parent_trace_id ? <div>父级调用轨迹 ID：{trace.parent_trace_id}</div> : null}
              {trace.error_message ? (
                <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 8 }}>
                  <strong>错误：</strong> {trace.error_message}
                </p>
              ) : null}
              {trace.trace_type === "research_tool_assisted" ? (
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
                      <strong>分析焦点：</strong> {analysisFocus}
                    </div>
                  ) : null}
                  {searchQuery ? (
                    <div>
                      <strong>搜索词：</strong> {searchQuery}
                    </div>
                  ) : null}
                  {degradedReason ? (
                    <div>
                      <strong>降级原因：</strong> {degradedReason}
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
                    <div style={{ color: "#64748b" }}>这条试点 trace 没有记录任何可见工具步骤。</div>
                  )}
                </section>
              ) : null}
              <details style={{ marginTop: 10 }}>
                <summary>调用轨迹载荷</summary>
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
          );
        })}
      </ul>
    </SectionCard>
  );
}
