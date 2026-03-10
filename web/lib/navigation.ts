type PlatformModule = {
  title: string;
  description: string;
};

type WorkspaceTab = {
  label: string;
  suffix: string;
};

export const platformModules: ReadonlyArray<PlatformModule> = [
  {
    title: "Platform Core",
    description: "Shared auth, workspaces, documents, chat, tasks, and metrics foundations.",
  },
  {
    title: "Job Assistant",
    description: "JD parsing, resume matching, gap analysis, and application workflows.",
  },
  {
    title: "Support Copilot",
    description: "Knowledge Q&A, ticket classification, drafting, and escalation guidance.",
  },
  {
    title: "Research Assistant",
    description: "Grounded retrieval, comparison, summarization, and report generation.",
  },
];

export const workspaceTabs: ReadonlyArray<WorkspaceTab> = [
  { label: "Overview", suffix: "" },
  { label: "Documents", suffix: "/documents" },
  { label: "Chat", suffix: "/chat" },
  { label: "Tasks", suffix: "/tasks" },
  { label: "Analytics", suffix: "/analytics" },
];
