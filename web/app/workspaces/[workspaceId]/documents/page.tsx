import DocumentManager from "../../../../components/documents/document-manager";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

type WorkspacePageProps = {
  params: {
    workspaceId: string;
  };
};

export default function WorkspaceDocumentsPage({ params }: WorkspacePageProps) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>文档</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>你可以在这里查看 ingest 状态，并对已索引内容手动触发重建索引。</p>
      <DocumentManager workspaceId={workspaceId} />
    </main>
  );
}
