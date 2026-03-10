import MetricsPanel from "../../../../components/workspace/metrics-panel";
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
      <p>Phase 1 exposes persisted request, latency, token, and retrieval metrics per workspace.</p>
      <MetricsPanel workspaceId={workspaceId} />
    </main>
  );
}
