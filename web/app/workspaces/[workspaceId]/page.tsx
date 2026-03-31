import { isWorkbenchPanelId } from "../../../lib/navigation";
import WorkspaceWorkbenchPanel from "../../../components/workspace/workspace-workbench-panel";
import WorkspacePageShell from "../../../components/workspace/workspace-page-shell";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
  searchParams?: {
    panel?: string;
  };
};

export default function WorkspaceWorkbenchPage({ params, searchParams }: WorkspacePageProps) {
  const { workspaceId } = params;
  const requestedPanel = searchParams?.panel;
  const initialPanel = requestedPanel && isWorkbenchPanelId(requestedPanel) ? requestedPanel : undefined;

  return (
    <WorkspacePageShell
      description="这是当前工作区的主工作台。对话是主中心，资料、动作和分析只在需要时以辅助视图方式唤出。"
      page="workbench"
      title="工作台"
      workspaceId={workspaceId}
    >
      <WorkspaceWorkbenchPanel initialPanel={initialPanel} workspaceId={workspaceId} />
    </WorkspacePageShell>
  );
}