import TaskManager from "../../../../components/tasks/task-manager";
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
      <h1>Tasks</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>Phase 3 lets you create platform tasks, watch status transitions, and inspect final agent results.</p>
      <TaskManager workspaceId={workspaceId} />
    </main>
  );
}
