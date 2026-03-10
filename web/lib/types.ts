export const workspaceTypes = ["job", "support", "research"] as const;
export const taskTypes = ["ingest", "qa", "report", "classify", "match"] as const;

export type WorkspaceType = (typeof workspaceTypes)[number];
export type TaskType = (typeof taskTypes)[number];
