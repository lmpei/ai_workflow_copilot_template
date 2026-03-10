"use client";

import { useEffect, useState } from "react";

import { getWorkspaceMetrics, isApiClientError } from "../../lib/api";
import type { WorkspaceMetrics } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type MetricsPanelProps = {
  workspaceId: string;
};

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
        setMetrics(await getWorkspaceMetrics(session.accessToken, workspaceId));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load metrics");
      } finally {
        setIsLoading(false);
      }
    };

    void loadMetrics();
  }, [session, workspaceId]);

  if (!isReady) {
    return <SectionCard title="Metrics">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to view workspace metrics." />;
  }

  return (
    <SectionCard title="Workspace metrics" description={`Workspace: ${workspaceId}`}>
      {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
      {isLoading ? <p>Loading metrics...</p> : null}
      {metrics ? (
        <ul>
          <li>Total requests: {metrics.total_requests}</li>
          <li>Average latency (ms): {metrics.avg_latency_ms}</li>
          <li>Retrieval hits: {metrics.retrieval_hit_count}</li>
          <li>Token usage: {metrics.token_usage}</li>
          <li>Task success rate: {metrics.task_success_rate}</li>
        </ul>
      ) : null}
    </SectionCard>
  );
}
