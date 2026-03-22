// Navigation-only helpers. Scenario registry truth now comes from /api/v1/scenario-modules, not from this file.
import { moduleTypes, type ModuleType } from "./types";

type PlatformModule = {
  title: string;
  description: string;
};

type WorkspaceTab = {
  label: string;
  suffix: string;
};

export const platformCoreModule: PlatformModule = {
  title: "Platform Core",
  description: "Shared auth, workspaces, documents, chat, tasks, and metrics foundations.",
};

export const workspaceTabs: ReadonlyArray<WorkspaceTab> = [
  { label: "Overview", suffix: "" },
  { label: "Modules", suffix: "/modules" },
  { label: "Documents", suffix: "/documents" },
  { label: "Chat", suffix: "/chat" },
  { label: "Tasks", suffix: "/tasks" },
  { label: "Analytics", suffix: "/analytics" },
];

export function isModuleType(value: string): value is ModuleType {
  return moduleTypes.includes(value as ModuleType);
}