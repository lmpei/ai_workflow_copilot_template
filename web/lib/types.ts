export const workspaceTypes = ["job", "support", "research"] as const;
export const taskTypes = ["research_summary", "workspace_report"] as const;

export type WorkspaceType = (typeof workspaceTypes)[number];
export type TaskType = (typeof taskTypes)[number];
export type JsonObject = Record<string, unknown>;

export type User = {
  id: string;
  email: string;
  name: string;
  role: string;
};

export type LoginRequestPayload = {
  email: string;
  password: string;
};

export type RegisterRequestPayload = LoginRequestPayload & {
  name: string;
};

export type LoginResponsePayload = {
  access_token: string;
  token_type: string;
  user: User;
};

export type AuthSession = {
  accessToken: string;
  user: User;
};

export type Workspace = {
  id: string;
  owner_id: string;
  name: string;
  type: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkspaceCreatePayload = {
  name: string;
  type: WorkspaceType;
  description?: string;
};

export type DocumentRecord = {
  id: string;
  workspace_id: string;
  title: string;
  source_type: string;
  file_path: string | null;
  mime_type: string | null;
  status: "uploaded" | "parsing" | "chunked" | "indexing" | "indexed" | "failed";
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ChatRequestPayload = {
  question: string;
  conversation_id?: string;
  mode?: string;
};

export type ChatSource = {
  document_id: string;
  chunk_id: string;
  document_title: string;
  chunk_index: number;
  snippet: string;
};

export type ChatResponsePayload = {
  answer: string;
  sources: ChatSource[];
  trace_id: string;
};

export type WorkspaceMetrics = {
  workspace_id: string;
  total_requests: number;
  avg_latency_ms: number;
  retrieval_hit_count: number;
  token_usage: number;
  task_success_rate: number;
};

export type TaskCreatePayload = {
  task_type: TaskType;
  input: JsonObject;
};

export type TaskRecord = {
  id: string;
  workspace_id: string;
  task_type: TaskType;
  status: "pending" | "running" | "done" | "failed";
  created_by: string;
  input_json: JsonObject;
  output_json: JsonObject;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};
