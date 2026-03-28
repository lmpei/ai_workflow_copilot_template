"use client";

import { useEffect, useState } from "react";

import { getWorkspaceAnalytics, isApiClientError } from "../../lib/api";
import type { WorkspaceMetrics } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type MetricsPanelProps = {
  workspaceId: string;
};

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatCost(value: number): string {
  return `$${value.toFixed(4)}`;
}

export default function MetricsPanel({ workspaceId }: MetricsPanelProps) {
  const { session, isReady } = useAuthSession();
  const [metrics, setMetrics] = useState<WorkspaceMetrics | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!session) {
      setMetrics(null);
      return;
    }

    const loadMetrics = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        setMetrics(await getWorkspaceAnalytics(session.accessToken, workspaceId));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载分析数据");
      } finally {
        setIsLoading(false);
      }
    };

    void loadMetrics();
  }, [session, workspaceId]);

  if (!isReady) {
    return <SectionCard title="分析">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能查看工作区分析数据。" />;
  }

  return (
    <SectionCard title="工作区分析" description={`工作区：${workspaceId}。这里汇总请求、评测和任务信号。`}>
      {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      {isLoading ? <p>正在加载分析数据...</p> : null}
      {metrics ? (
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          }}
        >
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>总请求数</strong>
            <div>{metrics.total_requests}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>平均延迟</strong>
            <div>{metrics.avg_latency_ms} ms</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>检索命中率</strong>
            <div>{formatPercent(metrics.retrieval_hit_rate)}</div>
            <small>累计命中 {metrics.retrieval_hit_count} 次</small>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Token 用量</strong>
            <div>{metrics.token_usage}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>预估成本</strong>
            <div>{formatCost(metrics.total_estimated_cost)}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>任务成功率</strong>
            <div>{formatPercent(metrics.task_success_rate)}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>评测运行数</strong>
            <div>{metrics.eval_run_count}</div>
            <small>累计处理 {metrics.eval_case_count} 个 case</small>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>评测通过率</strong>
            <div>{formatPercent(metrics.eval_pass_rate)}</div>
            <small>平均分：{metrics.avg_eval_score.toFixed(2)}</small>
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
