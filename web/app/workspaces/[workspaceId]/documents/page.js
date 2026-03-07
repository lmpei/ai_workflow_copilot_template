import IngestChecklist from "../../../../components/documents/ingest-checklist";
import SectionCard from "../../../../components/ui/section-card";
import WorkspaceNav from "../../../../components/workspace/workspace-nav";

export default function WorkspaceDocumentsPage({ params }) {
  const { workspaceId } = params;

  return (
    <main>
      <h1>Documents</h1>
      <WorkspaceNav workspaceId={workspaceId} />
      <SectionCard
        title="Document Ingest Pipeline"
        description="This page reserves the workflow for upload, parsing, chunking, and indexing."
      >
        <IngestChecklist />
      </SectionCard>
    </main>
  );
}
