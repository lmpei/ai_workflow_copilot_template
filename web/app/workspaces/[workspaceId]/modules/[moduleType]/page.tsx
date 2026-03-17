import ModuleHubPanel from "../../../../../components/workspace/module-hub-panel";
import WorkspaceNav from "../../../../../components/workspace/workspace-nav";

type WorkspaceModulePageProps = {
  params: {
    workspaceId: string;
    moduleType: string;
  };
};

export default function WorkspaceModulePage({ params }: WorkspaceModulePageProps) {
  const { workspaceId, moduleType } = params;

  return (
    <main>
      <h1>Workspace Module</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <ModuleHubPanel workspaceId={workspaceId} selectedModuleType={moduleType} />
    </main>
  );
}


