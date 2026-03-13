import ChatPanel from "../../../../components/chat/chat-panel";
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
      <p>Phase 2 returns grounded answers with source citations from indexed workspace documents.</p>
      <ChatPanel workspaceId={workspaceId} />
    </main>
  );
}
