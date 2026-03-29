import { redirect } from "next/navigation";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceChatPage({ params }: WorkspacePageProps) {
  redirect(`/workspaces/${params.workspaceId}?panel=chat`);
}
