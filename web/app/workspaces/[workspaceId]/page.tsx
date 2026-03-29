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
      description="这是当前工作区的主工作台。文档、对话和任务都在这里按需切换完成，不再要求你在多个平级页面之间来回跳。"
      page="workbench"
      title="工作台"
      workspaceId={workspaceId}
    >
      <WorkspaceWorkbenchPanel initialPanel={initialPanel} workspaceId={workspaceId} />
    </WorkspacePageShell>
  );
}
