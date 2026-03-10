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
      <p>Phase 1 supports authenticated chat requests and trace IDs on top of the workspace contract.</p>
      <ChatPanel workspaceId={workspaceId} />
    </main>
  );
}
