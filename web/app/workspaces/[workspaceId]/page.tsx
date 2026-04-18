import { isWorkbenchPanelId } from "../../../lib/navigation";
import WorkspaceWorkbenchRoute from "../../../components/workspace/workspace-workbench-route";

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

  return <WorkspaceWorkbenchRoute initialPanel={initialPanel} workspaceId={workspaceId} />;
}
