import ChatScaffold from "../../../../components/chat/chat-scaffold";
import SectionCard from "../../../../components/ui/section-card";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceChatPage({ params }: WorkspacePageProps) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>Chat</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <SectionCard
        title="Grounded Chat"
        description="The API route exists today; this page reserves the full chat experience for citations and traces."
      >
        <ChatScaffold />
      </SectionCard>
    </main>
  );
}
