import { redirect } from "next/navigation";

type WorkspaceModulesPageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceModulesPage({ params }: WorkspaceModulesPageProps) {
  redirect(`/workspaces/${params.workspaceId}`);
}
