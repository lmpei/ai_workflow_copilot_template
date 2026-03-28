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
      <h1>对话</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>这里会基于已索引的工作区文档返回 grounded 回答，并展示引用来源。</p>
      <ChatPanel workspaceId={workspaceId} />
    </main>
  );
}
