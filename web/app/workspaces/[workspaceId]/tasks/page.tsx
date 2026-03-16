import ResearchAssistantPanel from "../../../../components/research/research-assistant-panel";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceTasksPage({ params }: WorkspacePageProps) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>Research Assistant</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>Phase 5 turns the shared task runtime into a research module surface so you can launch structured summaries, inspect findings, and review linked evidence.</p>
      <ResearchAssistantPanel workspaceId={workspaceId} />
    </main>
  );
}
