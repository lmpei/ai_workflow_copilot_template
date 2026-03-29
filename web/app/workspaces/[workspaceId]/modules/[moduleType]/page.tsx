import { redirect } from "next/navigation";

type WorkspaceModulePageProps = {
  params: {
    workspaceId: string;
    moduleType: string;
  };
};

export default function WorkspaceModulePage({ params }: WorkspaceModulePageProps) {
  redirect(`/workspaces/${params.workspaceId}`);
}
