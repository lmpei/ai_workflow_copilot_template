export const moduleTypes = ["job", "support", "research"] as const;
export const workspaceTypes = moduleTypes;
export const scenarioTaskTypes = [
  "research_summary",
  "workspace_report",
  "ticket_summary",
  "reply_draft",
  "jd_summary",
  "resume_match",
] as const;
export const taskTypes = scenarioTaskTypes;

export type ModuleType = (typeof moduleTypes)[number];
export type TaskType = (typeof scenarioTaskTypes)[number];
export type JsonObject = Record<string, unknown>;
export type TaskStatus = "pending" | "running" | "completed" | "failed";

export type PublicDemoSettingsRecord = {
  public_demo_mode: boolean;
  registration_enabled: boolean;
  max_workspaces_per_user: number;
  max_documents_per_workspace: number;
  max_tasks_per_workspace: number;
  max_upload_bytes: number;
};

export type PublicDemoSeedDocumentRecord = {
  title: string;
  summary: string;
};

export type PublicDemoShowcaseStepRecord = {
  title: string;
  description: string;
  route_suffix: string;
  cta_label: string;
  sample_prompt?: string | null;
  sample_task_type?: TaskType | null;
  sample_task_input: JsonObject;
};

export type PublicDemoTemplateRecord = {
  template_id: string;
  module_type: ModuleType;
  title: string;
  summary: string;
  workspace_name: string;
  workspace_description: string;
  seeded_documents: PublicDemoSeedDocumentRecord[];
  showcase_steps: PublicDemoShowcaseStepRecord[];
};

export type PublicDemoWorkspaceSeedRecord = {
  workspace: Workspace;
  documents: DocumentRecord[];
  template: PublicDemoTemplateRecord;
};

export type RecoveryHistoryEntryRecord = {
  event: string;
  at: string;
  state?: string;
  by?: string;
  reason?: string;
  metadata?: JsonObject;
};

export type RecoveryDetailRecord = {
  state: string;
  history: RecoveryHistoryEntryRecord[];
  metadata: JsonObject;
  last_action?: string;
  reason?: string;
  requested_by?: string;
  requested_at?: string;
  applied_by?: string;
  applied_at?: string;
  source_task_id?: string;
  target_task_id?: string;
  source_eval_run_id?: string;
  target_eval_run_id?: string;
};

export type ScenarioEvidenceItem = {
  kind: string;
  ref_id: string;
  title?: string | null;
  snippet?: string | null;
  metadata: JsonObject;
};

export type ScenarioTaskResult = {
  module_type: ModuleType;
  task_type: TaskType;
  title: string;
  summary: string;
  highlights: string[];
  evidence: ScenarioEvidenceItem[];
  artifacts: JsonObject;
  metadata: JsonObject;
};

export type ScenarioTaskDefinitionRecord = {
  task_type: TaskType;
  label: string;
  input_field: string;
  eval_prompt_placeholder: string;
};

export type ScenarioModuleRecord = {
  module_type: ModuleType;
  title: string;
  short_label: string;
  description: string;
  work_object: string;
  primary_output: string;
  core_capabilities: string[];
  not_responsible_for: string[];
  entry_task_types: TaskType[];
  task_labels: Partial<Record<TaskType, string>>;
  eval_input_label: string;
  eval_prompt_field: string;
  default_eval_task_type: TaskType;
  quality_baseline: string;
  pass_threshold: number;
  tasks: ScenarioTaskDefinitionRecord[];
};

export type ResearchTaskType = Extract<TaskType, "research_summary" | "workspace_report">;
export type ResearchDeliverable = "brief" | "report";
export type ResearchRequestedSection =
  | "summary"
  | "findings"
  | "evidence"
  | "open_questions"
  | "next_steps";
export type ResearchTaskInput = {
  goal?: string;
  focus_areas: string[];
  key_questions: string[];
  constraints: string[];
  deliverable?: ResearchDeliverable;
  requested_sections: ResearchRequestedSection[];
  research_asset_id?: string;
  parent_task_id?: string;
  continuation_notes?: string;
};
export type ResearchAssetLink = {
  asset_id: string;
  revision_id: string;
  revision_number: number;
};
export type ResearchLineage = {
  parent_task_id: string;
  parent_task_type: ResearchTaskType;
  parent_title: string;
  parent_goal?: string;
  parent_summary: string;
  parent_report_headline?: string;
  continuation_notes?: string;
};
export type SupportTaskType = Extract<TaskType, "ticket_summary" | "reply_draft">;
export type SupportSeverity = "low" | "medium" | "high" | "critical";
export type SupportEvidenceStatus = "grounded_matches" | "documents_only" | "no_documents";
export type SupportTaskInput = {
  customer_issue?: string;
  product_area?: string;
  severity?: SupportSeverity;
  desired_outcome?: string;
  reproduction_steps: string[];
  parent_task_id?: string;
  follow_up_notes?: string;
};

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

export type ResearchFinding = {
  title: string;
  summary: string;
  evidence_ref_ids: string[];
};

export type ResearchReportSection = {
  slug: string;
  title: string;
  summary: string;
  bullets: string[];
  evidence_ref_ids: string[];
};

export type ResearchFormalReport = {
  headline: string;
  executive_summary: string;
  sections: ResearchReportSection[];
  open_questions: string[];
  recommended_next_steps: string[];
  evidence_ref_ids: string[];
};

export type ResearchResultSections = {
  summary: string;
  findings: ResearchFinding[];
  evidence_overview: string[];
  open_questions: string[];
  next_steps: string[];
};

export type ResearchTaskResult = ScenarioTaskResult & {
  module_type: "research";
  task_type: ResearchTaskType;
  input: ResearchTaskInput;
  lineage?: ResearchLineage;
  sections: ResearchResultSections;
  report?: ResearchFormalReport;
  artifacts: ResearchArtifacts;
};

export type ResearchBriefRecord = {
  goal?: string;
  focus_areas: string[];
  key_questions: string[];
  constraints: string[];
  deliverable?: ResearchDeliverable | null;
  requested_sections: ResearchRequestedSection[];
  continuation_notes?: string | null;
};

export type ResearchAssetRevisionRecord = {
  id: string;
  research_asset_id: string;
  task_id: string;
  task_type: ResearchTaskType;
  revision_number: number;
  title: string;
  brief: ResearchBriefRecord;
  input_json: JsonObject;
  result_json: JsonObject;
  summary: string;
  report_headline?: string | null;
  created_at: string;
};
export type ResearchAssetSummaryRecord = {
  id: string;
  workspace_id: string;
  created_by: string;
  title: string;
  latest_task_id?: string | null;
  latest_task_type: ResearchTaskType;
  latest_revision_number: number;
  latest_brief: ResearchBriefRecord;
  latest_input_json: JsonObject;
  latest_result_json: JsonObject;
  latest_summary: string;
  latest_report_headline?: string | null;
  created_at: string;
  updated_at: string;
};
export type ResearchAssetRecord = ResearchAssetSummaryRecord & {
  revisions: ResearchAssetRevisionRecord[];
};

export type ResearchAssetComparisonSideRecord = {
  asset_id: string;
  asset_title: string;
  revision_id?: string | null;
  revision_number: number;
  task_id?: string | null;
  task_type: ResearchTaskType;
  brief: ResearchBriefRecord;
  summary: string;
  report_headline?: string | null;
  open_questions: string[];
  findings_count: number;
  evidence_count: number;
  document_count: number;
  match_count: number;
};

export type ResearchAssetComparisonDiffRecord = {
  shared_focus_areas: string[];
  left_only_focus_areas: string[];
  right_only_focus_areas: string[];
  shared_key_questions: string[];
  left_only_key_questions: string[];
  right_only_key_questions: string[];
  shared_constraints: string[];
  left_only_constraints: string[];
  right_only_constraints: string[];
  left_only_open_questions: string[];
  right_only_open_questions: string[];
  summary_changed: boolean;
  report_headline_changed: boolean;
  finding_count_delta: number;
  evidence_count_delta: number;
  document_count_delta: number;
  match_count_delta: number;
};

export type ResearchAssetComparisonRecord = {
  left: ResearchAssetComparisonSideRecord;
  right: ResearchAssetComparisonSideRecord;
  diff: ResearchAssetComparisonDiffRecord;
};

export type SupportDocumentSummary = ResearchDocumentSummary;
export type SupportMatch = ResearchMatch;

export type SupportArtifacts = {
  document_count: number;
  match_count: number;
  documents: SupportDocumentSummary[];
  matches: SupportMatch[];
  tool_call_ids: string[];
  evidence_status: SupportEvidenceStatus;
};

export type SupportCaseBrief = {
  issue_summary: string;
  product_area?: string | null;
  severity?: SupportSeverity | null;
  desired_outcome?: string | null;
  reproduction_steps: string[];
  evidence_status: SupportEvidenceStatus;
};

export type SupportFinding = {
  title: string;
  summary: string;
  evidence_ref_ids: string[];
};

export type SupportTriageDecision = {
  evidence_status: SupportEvidenceStatus;
  needs_manual_review: boolean;
  should_escalate: boolean;
  recommended_owner: string;
  rationale: string;
};

export type SupportCaseLineage = {
  parent_task_id: string;
  parent_task_type: SupportTaskType;
  parent_title: string;
  parent_summary: string;
  parent_customer_issue?: string | null;
  parent_product_area?: string | null;
  parent_severity?: SupportSeverity | null;
  parent_desired_outcome?: string | null;
  parent_reproduction_steps: string[];
  parent_recommended_owner?: string | null;
  parent_evidence_status?: SupportEvidenceStatus | null;
  follow_up_notes?: string | null;
};

export type SupportReplyDraft = {
  subject_line: string;
  body: string;
  confidence_note: string;
};

export type SupportEscalationPacket = {
  recommended_owner: string;
  needs_manual_review: boolean;
  should_escalate: boolean;
  evidence_status: SupportEvidenceStatus;
  escalation_reason: string;
  case_summary: string;
  findings: SupportFinding[];
  unresolved_questions: string[];
  recommended_next_steps: string[];
  evidence_ref_ids: string[];
  follow_up_notes?: string | null;
  handoff_note: string;
};

export type SupportTaskResult = ScenarioTaskResult & {
  module_type: "support";
  task_type: SupportTaskType;
  input: SupportTaskInput;
  lineage?: SupportCaseLineage;
  case_brief: SupportCaseBrief;
  findings: SupportFinding[];
  triage: SupportTriageDecision;
  open_questions: string[];
  next_steps: string[];
  reply_draft?: SupportReplyDraft;
  escalation_packet?: SupportEscalationPacket;
  artifacts: SupportArtifacts;
};

export type SupportCaseStatus = "open" | "needs_customer_input" | "ready_for_reply" | "escalated";

export type SupportCaseLink = {
  case_id: string;
  event_id: string;
  case_status: SupportCaseStatus;
};

export type SupportCaseActionLoopRecord = {
  can_continue: boolean;
  continue_from_task_id?: string | null;
  suggested_task_type: SupportTaskType;
  status_guidance: string;
  suggested_follow_up_prompt?: string | null;
};

export type SupportCaseEventRecord = {
  id: string;
  support_case_id: string;
  task_id: string;
  task_type: SupportTaskType;
  event_kind: string;
  title: string;
  summary: string;
  case_status: SupportCaseStatus;
  recommended_owner?: string | null;
  evidence_status?: SupportEvidenceStatus | null;
  should_escalate: boolean;
  needs_manual_review: boolean;
  follow_up_notes?: string | null;
  created_at: string;
};

export type SupportCaseSummaryRecord = {
  id: string;
  workspace_id: string;
  created_by: string;
  title: string;
  status: SupportCaseStatus;
  action_loop: SupportCaseActionLoopRecord;
  latest_task_id?: string | null;
  latest_task_type: SupportTaskType;
  latest_summary: string;
  latest_case_brief: SupportCaseBrief;
  latest_triage: SupportTriageDecision;
  latest_escalation_packet: SupportEscalationPacket;
  latest_open_questions: string[];
  latest_next_steps: string[];
  latest_recommended_owner?: string | null;
  latest_evidence_status?: SupportEvidenceStatus | null;
  event_count: number;
  created_at: string;
  updated_at: string;
};

export type SupportCaseRecord = SupportCaseSummaryRecord & {
  events: SupportCaseEventRecord[];
};

export type SupportCaseContinuationDraft = {
  request_id: number;
  case_id: string;
  case_title: string;
  case_status: SupportCaseStatus;
  continue_from_task_id: string;
  suggested_task_type: SupportTaskType;
  status_guidance: string;
  suggested_follow_up_prompt?: string | null;
  customer_issue: string;
  product_area?: string | null;
  severity?: SupportSeverity | null;
  desired_outcome?: string | null;
  reproduction_steps: string[];
};
export type JobTaskType = Extract<TaskType, "jd_summary" | "resume_match">;
export type JobEvidenceStatus = "grounded_matches" | "documents_only" | "no_documents";
export type JobFitSignal =
  | "grounded_match_found"
  | "role_requirements_grounded"
  | "insufficient_grounding"
  | "no_documents_available";
export type JobTaskInput = {
  target_role?: string;
  candidate_label?: string;
  seniority?: string;
  must_have_skills: string[];
  preferred_skills: string[];
  hiring_context?: string;
  comparison_task_ids: string[];
  comparison_notes?: string;
};

export type JobReviewBrief = {
  role_summary: string;
  candidate_label?: string | null;
  seniority?: string | null;
  must_have_skills: string[];
  preferred_skills: string[];
  hiring_context?: string | null;
  evidence_status: JobEvidenceStatus;
  comparison_task_count: number;
};

export type JobFinding = {
  title: string;
  summary: string;
  evidence_ref_ids: string[];
};

export type JobFitAssessment = {
  fit_signal: JobFitSignal;
  evidence_status: JobEvidenceStatus;
  recommended_outcome: string;
  confidence_note: string;
  rationale: string;
};

export type JobComparisonCandidate = {
  task_id: string;
  task_type: JobTaskType;
  candidate_label: string;
  title: string;
  summary: string;
  target_role?: string | null;
  seniority?: string | null;
  fit_signal: JobFitSignal;
  evidence_status: JobEvidenceStatus;
  recommended_outcome?: string | null;
  findings: JobFinding[];
  highlights: string[];
  evidence_ref_ids: string[];
};

export type JobShortlistEntry = {
  rank: number;
  task_id: string;
  candidate_label: string;
  fit_signal: JobFitSignal;
  evidence_status: JobEvidenceStatus;
  recommendation: string;
  rationale: string;
  risks: string[];
  interview_focus: string[];
  evidence_ref_ids: string[];
};

export type JobShortlistResult = {
  comparison_task_ids: string[];
  comparison_notes?: string | null;
  shortlist_summary: string;
  entries: JobShortlistEntry[];
  risks: string[];
  interview_focus: string[];
  gaps: string[];
};

export type JobArtifacts = {
  document_count: number;
  match_count: number;
  documents: ResearchDocumentSummary[];
  matches: ResearchMatch[];
  tool_call_ids: string[];
  evidence_status: JobEvidenceStatus;
  fit_signal: JobFitSignal;
  recommended_next_step: string;
};

export type JobTaskResult = ScenarioTaskResult & {
  module_type: "job";
  task_type: JobTaskType;
  input: JobTaskInput;
  review_brief: JobReviewBrief;
  findings: JobFinding[];
  gaps: string[];
  assessment: JobFitAssessment;
  comparison_candidates: JobComparisonCandidate[];
  shortlist?: JobShortlistResult;
  open_questions: string[];
  next_steps: string[];
  artifacts: JobArtifacts;
};

export type JobHiringPacketStatus = "collecting_materials" | "needs_alignment" | "review_ready" | "shortlist_ready";

export type JobHiringPacketLink = {
  packet_id: string;
  event_id: string;
  packet_status: JobHiringPacketStatus;
};

export type JobHiringPacketEventRecord = {
  id: string;
  job_hiring_packet_id: string;
  task_id: string;
  task_type: JobTaskType;
  event_kind: string;
  title: string;
  summary: string;
  packet_status: JobHiringPacketStatus;
  candidate_label?: string | null;
  target_role?: string | null;
  fit_signal?: JobFitSignal | null;
  evidence_status?: JobEvidenceStatus | null;
  recommended_outcome?: string | null;
  comparison_task_ids: string[];
  shortlist_entry_count: number;
  created_at: string;
};

export type JobHiringPacketSummaryRecord = {
  id: string;
  workspace_id: string;
  created_by: string;
  title: string;
  status: JobHiringPacketStatus;
  target_role?: string | null;
  seniority?: string | null;
  latest_task_id?: string | null;
  latest_task_type: JobTaskType;
  latest_summary: string;
  latest_review_brief: JobReviewBrief;
  latest_assessment: JobFitAssessment;
  latest_shortlist?: JobShortlistResult | null;
  latest_next_steps: string[];
  latest_candidate_labels: string[];
  latest_recommended_outcome?: string | null;
  latest_evidence_status?: JobEvidenceStatus | null;
  latest_fit_signal?: JobFitSignal | null;
  comparison_history_count: number;
  event_count: number;
  created_at: string;
  updated_at: string;
};

export type JobHiringPacketRecord = JobHiringPacketSummaryRecord & {
  events: JobHiringPacketEventRecord[];
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
  module_type: ModuleType;
  description: string | null;
  module_config_json: JsonObject;
  created_at: string;
  updated_at: string;
};

export type WorkspaceCreatePayload = {
  name: string;
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
  recovery_state: string;
  recovery_detail: RecoveryDetailRecord;
  created_by: string;
  summary_json: JsonObject;
  control_json: JsonObject;
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
  status: TaskStatus;
  recovery_state: string;
  recovery_detail: RecoveryDetailRecord;
  created_by: string;
  input_json: JsonObject;
  output_json: JsonObject;
  control_json: JsonObject;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};
