import ModuleHubPanel from "../../../../components/workspace/module-hub-panel";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

type WorkspaceModulesPageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceModulesPage({ params }: WorkspaceModulesPageProps) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>工作区模块</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <ModuleHubPanel workspaceId={workspaceId} />
    </main>
  );
}
