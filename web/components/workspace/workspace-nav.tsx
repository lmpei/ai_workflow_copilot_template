import Link from "next/link";

import { getWorkspacePageHref, type WorkspacePageId } from "../../lib/navigation";

type WorkspaceNavProps = {
  workspaceId: string;
  currentPage: WorkspacePageId;
};

function renderNavLink(href: string, label: string, description: string, isActive: boolean) {
  return (
    <Link
      href={href}
      style={{
        backgroundColor: isActive ? "#0f172a" : "#ffffff",
        border: `1px solid ${isActive ? "#0f172a" : "#cbd5e1"}`,
        borderRadius: 14,
        color: isActive ? "#ffffff" : "#0f172a",
        display: "grid",
        gap: 4,
        minWidth: 220,
        padding: "14px 16px",
        textDecoration: "none",
      }}
    >
      <strong>{label}</strong>
      <span style={{ color: isActive ? "#e2e8f0" : "#475569", fontSize: 13 }}>{description}</span>
    </Link>
  );
}

export default function WorkspaceNav({ workspaceId, currentPage }: WorkspaceNavProps) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 24 }}>
      {renderNavLink(
        getWorkspacePageHref(workspaceId, "workbench"),
        "工作台",
        "把文档、对话和任务收在一个主工作区里完成。",
        currentPage === "workbench",
      )}
      {renderNavLink(
        getWorkspacePageHref(workspaceId, "analytics"),
        "分析",
        "在需要时复盘评测、trace 和 readiness，而不是把它当成第一站。",
        currentPage === "analytics",
      )}
    </div>
  );
}
