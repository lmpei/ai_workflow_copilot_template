import EvalManager from "../../../../components/evals/eval-manager";
import MetricsPanel from "../../../../components/workspace/metrics-panel";
import ObservabilityPanel from "../../../../components/workspace/observability-panel";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceAnalyticsPage({ params }: WorkspacePageProps) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>Analytics</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>
        Phase 4 adds evaluation datasets, eval runs, richer workspace analytics, and recent trace
        inspection from the product surface.
      </p>
      <MetricsPanel workspaceId={workspaceId} />
      <EvalManager workspaceId={workspaceId} />
      <ObservabilityPanel workspaceId={workspaceId} />
    </main>
  );
}
