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
      <h1>场景任务</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>这里把共享任务运行时包装成模块专属的 copilot 任务面板，同时保留统一的任务、评测和 trace 基础能力。</p>
      <TaskModulePanel workspaceId={workspaceId} />
    </main>
  );
}
