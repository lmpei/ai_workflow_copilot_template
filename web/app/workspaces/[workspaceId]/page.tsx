import GuidedWorkspaceShowcase from "../../../components/public-demo/guided-workspace-showcase";
import ModuleHubPanel from "../../../components/workspace/module-hub-panel";
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
      <h1>Workspace Overview</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <GuidedWorkspaceShowcase workspaceId={workspaceId} />
      <SectionCard
        title="Shared workspace surfaces"
        description="Every module keeps its documents, chat traces, tasks, and analytics inside one shared workspace scope."
      >
        <ul>
          <li>Documents and retrieval state</li>
          <li>Conversations and citations</li>
          <li>Tasks, agent runs, and tool traces</li>
          <li>Quality metrics and cost tracking</li>
        </ul>
      </SectionCard>
      <ModuleHubPanel workspaceId={workspaceId} />
    </main>
  );
}