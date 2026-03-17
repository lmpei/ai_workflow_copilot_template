import TaskModulePanel from "../../../../components/tasks/task-module-panel";
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
      <h1>Scenario Tasks</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>
        Phase 5 turns the shared task runtime into module-specific copilots, while keeping tasks,
        agents, evals, and traces on the same platform primitives.
      </p>
      <TaskModulePanel workspaceId={workspaceId} />
    </main>
  );
}

