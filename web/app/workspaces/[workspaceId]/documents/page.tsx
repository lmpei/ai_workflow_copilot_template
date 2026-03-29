import { redirect } from "next/navigation";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceDocumentsPage({ params }: WorkspacePageProps) {
  redirect(`/workspaces/${params.workspaceId}?panel=documents`);
}
