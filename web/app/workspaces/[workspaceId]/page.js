import SectionCard from "../../../components/ui/section-card";
import WorkspaceNav from "../../../components/workspace/workspace-nav";

export default function WorkspaceOverviewPage({ params }) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>Workspace: {workspaceId}</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <SectionCard
        title="Workspace Overview"
        description="A workspace will host scenario-specific flows on top of one shared platform core."
      >
        <ul>
          <li>Documents and retrieval state</li>
          <li>Conversations and citations</li>
          <li>Tasks, agent runs, and tool traces</li>
          <li>Quality metrics and cost tracking</li>
        </ul>
      </SectionCard>
    </main>
  );
}
