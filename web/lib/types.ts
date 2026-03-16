export const workspaceTypes = ["job", "support", "research"] as const;
export const scenarioTaskTypes = [
  "research_summary",
  "workspace_report",
  "ticket_summary",
  "reply_draft",
  "jd_summary",
  "resume_match",
] as const;
export const taskTypes = scenarioTaskTypes;

export type WorkspaceType = (typeof workspaceTypes)[number];
export type TaskType = (typeof scenarioTaskTypes)[number];
export type ModuleType = WorkspaceType;
export type ScenarioTaskType = (typeof scenarioTaskTypes)[number];
export type JsonObject = Record<string, unknown>;

export type ScenarioEvidenceItem = {
  kind: string;
  ref_id: string;
  title?: string | null;
  snippet?: string | null;
  metadata: JsonObject;
};

export type ScenarioTaskResult = {
  module_type: ModuleType;
  task_type: ScenarioTaskType;
  title: string;
  summary: string;
  highlights: string[];
  evidence: ScenarioEvidenceItem[];
  artifacts: JsonObject;
  metadata: JsonObject;
};

export type ResearchTaskType = Extract<TaskType, "research_summary" | "workspace_report">;
export type SupportTaskType = Extract<TaskType, "ticket_summary" | "reply_draft">;

export type ResearchDocumentSummary = {
  id: string;
  title: string;
  status: DocumentRecord["status"];
  source_type: string;
  mime_type?: string | null;
};

export type ResearchMatch = {
  document_id: string;
  chunk_id: string;
  document_title: string;
  chunk_index: number;
  snippet: string;
};

export type ResearchArtifacts = {
  document_count: number;
  match_count: number;
  documents: ResearchDocumentSummary[];
  matches: ResearchMatch[];
  tool_call_ids: string[];
};

export type ResearchTaskResult = ScenarioTaskResult & {
  module_type: "research";
  task_type: ResearchTaskType;
  artifacts: ResearchArtifacts;
};

export type SupportDocumentSummary = ResearchDocumentSummary;
export type SupportMatch = ResearchMatch;

export type SupportArtifacts = {
  document_count: number;
  match_count: number;
  documents: SupportDocumentSummary[];
  matches: SupportMatch[];
  tool_call_ids: string[];
  draft_reply?: string | null;
};

export type SupportTaskResult = ScenarioTaskResult & {
  module_type: "support";
  task_type: SupportTaskType;
  artifacts: SupportArtifacts;
};

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
  type: WorkspaceType;
  module_type: ModuleType;
  description: string | null;
  module_config_json: JsonObject;
  created_at: string;
  updated_at: string;
};

export type WorkspaceCreatePayload = {
  name: string;
  type?: WorkspaceType;
  module_type?: ModuleType;
  module_config_json?: JsonObject;
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
  retrieval_hit_rate: number;
  token_usage: number;
  total_estimated_cost: number;
  task_success_rate: number;
  eval_run_count: number;
  eval_case_count: number;
  eval_pass_rate: number;
  avg_eval_score: number;
};

export type EvalType = "retrieval_chat";

export type EvalCaseCreatePayload = {
  input_json: JsonObject;
  expected_json?: JsonObject;
  metadata_json?: JsonObject;
};

export type EvalDatasetCreatePayload = {
  name: string;
  eval_type: EvalType;
  description?: string;
  config_json?: JsonObject;
  cases: EvalCaseCreatePayload[];
};

export type EvalCaseRecord = {
  id: string;
  case_index: number;
  input_json: JsonObject;
  expected_json: JsonObject;
  metadata_json: JsonObject;
  created_at: string;
  updated_at: string;
};

export type EvalDatasetRecord = {
  id: string;
  workspace_id: string;
  name: string;
  eval_type: EvalType;
  description: string | null;
  created_by: string;
  config_json: JsonObject;
  cases: EvalCaseRecord[];
  created_at: string;
  updated_at: string;
};

export type EvalRunCreatePayload = {
  dataset_id: string;
};

export type EvalRunRecord = {
  id: string;
  workspace_id: string;
  dataset_id: string;
  eval_type: EvalType;
  status: "pending" | "running" | "completed" | "failed";
  created_by: string;
  summary_json: JsonObject;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
};

export type EvalResultRecord = {
  id: string;
  eval_run_id: string;
  eval_case_id: string;
  status: "pending" | "completed" | "failed";
  output_json: JsonObject;
  metrics_json: JsonObject;
  score: number | null;
  passed: boolean | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type TraceRecord = {
  id: string;
  workspace_id: string;
  parent_trace_id: string | null;
  task_id: string | null;
  agent_run_id: string | null;
  tool_call_id: string | null;
  eval_run_id: string | null;
  trace_type: string;
  request_json: JsonObject;
  response_json: JsonObject;
  metadata_json: JsonObject;
  error_message: string | null;
  latency_ms: number;
  token_input: number;
  token_output: number;
  estimated_cost: number;
  created_at: string;
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
