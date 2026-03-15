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
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load analytics");
      } finally {
        setIsLoading(false);
      }
    };

    void loadMetrics();
  }, [session, workspaceId]);

  if (!isReady) {
    return <SectionCard title="Analytics">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to view workspace analytics." />;
  }

  return (
    <SectionCard
      title="Workspace analytics"
      description={`Workspace: ${workspaceId}. Phase 4 combines request, evaluation, and task signals.`}
    >
      {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      {isLoading ? <p>Loading analytics...</p> : null}
      {metrics ? (
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          }}
        >
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Total requests</strong>
            <div>{metrics.total_requests}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Avg latency</strong>
            <div>{metrics.avg_latency_ms} ms</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Retrieval hit rate</strong>
            <div>{formatPercent(metrics.retrieval_hit_rate)}</div>
            <small>{metrics.retrieval_hit_count} hits total</small>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Token usage</strong>
            <div>{metrics.token_usage}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Estimated cost</strong>
            <div>{formatCost(metrics.total_estimated_cost)}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Task success rate</strong>
            <div>{formatPercent(metrics.task_success_rate)}</div>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Eval runs</strong>
            <div>{metrics.eval_run_count}</div>
            <small>{metrics.eval_case_count} cases processed</small>
          </div>
          <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <strong>Eval pass rate</strong>
            <div>{formatPercent(metrics.eval_pass_rate)}</div>
            <small>Average score: {metrics.avg_eval_score.toFixed(2)}</small>
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
