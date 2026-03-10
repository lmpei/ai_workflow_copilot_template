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
      <p>Phase 1 supports document upload and metadata listing. Parsing and indexing remain in Phase 2.</p>
      <DocumentManager workspaceId={workspaceId} />
    </main>
  );
}
