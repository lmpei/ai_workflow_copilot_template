import type { ModuleType, ScenarioTaskType } from "./types";

type PlatformModule = {
  title: string;
  description: string;
};

type WorkspaceTab = {
  label: string;
  suffix: string;
};

export type ScenarioModuleNavigation = {
  moduleType: ModuleType;
  title: string;
  shortLabel: string;
  description: string;
  entryTaskTypes: ScenarioTaskType[];
};

export const scenarioTaskLabels: Record<ScenarioTaskType, string> = {
  research_summary: "Research Summary",
  workspace_report: "Workspace Report",
  ticket_summary: "Ticket Summary",
  reply_draft: "Reply Draft",
  jd_summary: "JD Summary",
  resume_match: "Resume Match",
};

export const scenarioModules: ReadonlyArray<ScenarioModuleNavigation> = [
  {
    moduleType: "research",
    title: "Research Assistant",
    shortLabel: "Research",
    description: "Grounded retrieval, comparison, summarization, and report generation.",
    entryTaskTypes: ["research_summary", "workspace_report"],
  },
  {
    moduleType: "support",
    title: "Support Copilot",
    shortLabel: "Support",
    description: "Knowledge Q&A, ticket classification, drafting, and escalation guidance.",
    entryTaskTypes: ["ticket_summary", "reply_draft"],
  },
  {
    moduleType: "job",
    title: "Job Assistant",
    shortLabel: "Job",
    description: "JD parsing, resume matching, gap analysis, and application workflows.",
    entryTaskTypes: ["jd_summary", "resume_match"],
  },
];

export const platformModules: ReadonlyArray<PlatformModule> = [
  {
    title: "Platform Core",
    description: "Shared auth, workspaces, documents, chat, tasks, and metrics foundations.",
  },
  ...scenarioModules.map(({ title, description }) => ({ title, description })),
];

export const workspaceTabs: ReadonlyArray<WorkspaceTab> = [
  { label: "Overview", suffix: "" },
  { label: "Modules", suffix: "/modules" },
  { label: "Documents", suffix: "/documents" },
  { label: "Chat", suffix: "/chat" },
  { label: "Tasks", suffix: "/tasks" },
  { label: "Analytics", suffix: "/analytics" },
];

export function isModuleType(value: string): value is ModuleType {
  return scenarioModules.some((module) => module.moduleType === value);
}

export function getScenarioModule(moduleType: ModuleType): ScenarioModuleNavigation {
  return scenarioModules.find((module) => module.moduleType === moduleType) ?? scenarioModules[0];
}
