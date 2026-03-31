// Navigation-only helpers. Scenario registry truth now comes from /api/v1/scenario-modules, not from this file.
import { moduleTypes, type ModuleType } from "./types";

type PlatformModule = {
  title: string;
  description: string;
};

export type WorkspacePageId = "workbench" | "analytics";
export type WorkbenchPanelId = "documents" | "chat" | "tasks" | "analytics";

type WorkspacePage = {
  id: WorkspacePageId;
  label: string;
  suffix: string;
};

type WorkbenchPanel = {
  id: WorkbenchPanelId;
  label: string;
  description: string;
};

export const platformCoreModule: PlatformModule = {
  title: "平台核心",
  description: "共享的认证、工作区、文档、对话、任务与指标基础能力。",
};

export const workspacePages: ReadonlyArray<WorkspacePage> = [
  { id: "workbench", label: "工作台", suffix: "" },
  { id: "analytics", label: "分析", suffix: "/analytics" },
];

export const workbenchPanels: ReadonlyArray<WorkbenchPanel> = [
  { id: "documents", label: "文档", description: "确认材料是否就绪，再决定下一步。" },
  { id: "chat", label: "对话", description: "基于当前文档验证 grounded 回答。" },
  { id: "tasks", label: "任务", description: "运行模块动作或继续已有 workbench。" },
  { id: "analytics", label: "分析", description: "按需查看指标、评测和 trace，不把它当成第一站。" },
];

export function getWorkspacePage(pageId: WorkspacePageId): WorkspacePage {
  return workspacePages.find((page) => page.id === pageId) ?? workspacePages[0];
}

export function getWorkspacePageHref(workspaceId: string, pageId: WorkspacePageId): string {
  return `/workspaces/${workspaceId}${getWorkspacePage(pageId).suffix}`;
}

export function getWorkbenchPanelHref(workspaceId: string, panelId: WorkbenchPanelId): string {
  return `/workspaces/${workspaceId}?panel=${panelId}`;
}

export function isWorkbenchPanelId(value: string): value is WorkbenchPanelId {
  return workbenchPanels.some((panel) => panel.id === value);
}

export function isModuleType(value: string): value is ModuleType {
  return moduleTypes.includes(value as ModuleType);
}
