import Link from "next/link";

import { workspaceTabs } from "../../lib/navigation";

export default function WorkspaceNav({ workspaceId }) {
  return (
    <nav style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
      {workspaceTabs.map((tab) => (
        <Link
          key={tab.label}
          href={`/workspaces/${workspaceId}${tab.suffix}`}
          style={{ color: "#0f172a", textDecoration: "none" }}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
