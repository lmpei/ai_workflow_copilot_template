import { redirect } from "next/navigation";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceTasksPage({ params }: WorkspacePageProps) {
  redirect(`/workspaces/${params.workspaceId}?panel=tasks`);
}
