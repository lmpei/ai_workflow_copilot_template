import Link from "next/link";

import SectionCard from "../../components/ui/section-card";

export default function WorkspacesPage() {
  return (
    <main>
      <h1>Workspaces</h1>
      <SectionCard
        title="Workspace Hub"
        description="Workspaces are the shared container for documents, conversations, tasks, and metrics."
      >
        <p>
          Demo route: <Link href="/workspaces/demo">Open the demo workspace</Link>
        </p>
      </SectionCard>
    </main>
  );
}
