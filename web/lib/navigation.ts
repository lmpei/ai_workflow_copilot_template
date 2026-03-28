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
  title: "平台核心",
  description: "共享的认证、工作区、文档、对话、任务与指标基础能力。",
};

export const workspaceTabs: ReadonlyArray<WorkspaceTab> = [
  { label: "概览", suffix: "" },
  { label: "模块", suffix: "/modules" },
  { label: "文档", suffix: "/documents" },
  { label: "对话", suffix: "/chat" },
  { label: "任务", suffix: "/tasks" },
  { label: "分析", suffix: "/analytics" },
];

export function isModuleType(value: string): value is ModuleType {
  return moduleTypes.includes(value as ModuleType);
}
