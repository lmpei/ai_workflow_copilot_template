import ModuleHub from "../../../../components/workspace/module-hub";
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
      <h1>Workspace Modules</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <ModuleHub workspaceId={workspaceId} />
    </main>
  );
}
