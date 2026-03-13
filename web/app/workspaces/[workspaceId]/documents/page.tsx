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
      <h1>Documents</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <p>Phase 2 shows ingest status directly and supports manual reindex for indexed content.</p>
      <DocumentManager workspaceId={workspaceId} />
    </main>
  );
}
