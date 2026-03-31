import { redirect } from "next/navigation";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceAnalyticsPage({ params }: WorkspacePageProps) {
  redirect(`/workspaces/${params.workspaceId}?panel=analytics`);
}
