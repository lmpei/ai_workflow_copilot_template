import SectionCard from "../../../../components/ui/section-card";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

export default function WorkspaceTasksPage({ params }) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>Tasks</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <SectionCard
        title="Async Task Surface"
        description="This page will list ingest jobs, report generation tasks, and agent executions."
      >
        <ul>
          <li>Pending queue status</li>
          <li>Worker progress</li>
          <li>Task outputs and errors</li>
        </ul>
      </SectionCard>
    </main>
  );
}
