import SectionCard from "../../../../components/ui/section-card";
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
      <SectionCard
        title="Evaluation and Observability"
        description="This page is reserved for latency, token, cost, retrieval-hit, and quality dashboards."
      >
        <ul>
          <li>Trace volume and latency</li>
          <li>Token usage and estimated cost</li>
          <li>Retrieval hit rate and task success rate</li>
        </ul>
      </SectionCard>
    </main>
  );
}
