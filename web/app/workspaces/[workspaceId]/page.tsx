import ModuleHub from "../../../components/workspace/module-hub";
import SectionCard from "../../../components/ui/section-card";
import WorkspaceNav from "../../../components/workspace/workspace-nav";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceOverviewPage({ params }: WorkspacePageProps) {
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
      <ModuleHub workspaceId={workspaceId} />
    </main>
  );
}
