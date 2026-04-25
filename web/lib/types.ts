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
  source_kind: "workspace_document" | "external_context";
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

export type JobHiringPacketActionLoopRecord = {
  can_continue: boolean;
  suggested_task_type: JobTaskType;
  comparison_mode: boolean;
  status_guidance: string;
  suggested_note_prompt?: string | null;
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
  action_loop: JobHiringPacketActionLoopRecord;
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
  latest_packet_note?: string | null;
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

export type JobHiringPacketContinuationDraft = {
  request_id: number;
  packet_id: string;
  packet_title: string;
  packet_status: JobHiringPacketStatus;
  suggested_task_type: JobTaskType;
  comparison_mode: boolean;
  status_guidance: string;
  suggested_note_prompt?: string | null;
  target_role?: string | null;
  seniority?: string | null;
  must_have_skills: string[];
  preferred_skills: string[];
  hiring_context?: string | null;
  comparison_task_ids: string[];
  comparison_notes?: string | null;
};

export type User = {
  id: string;
  email: string;
  name: string;
  role: string;
};

export type EnterAuthRequestPayload = {
  account: string;
  password: string;
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

export type WorkspaceUpdatePayload = {
  name?: string;
  module_type?: ModuleType;
  description?: string;
  module_config_json?: JsonObject;
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
  mode?: 'rag' | 'research_tool_assisted' | 'research_external_context';
  external_resource_snapshot_id?: string;
};

export type AiFrontierThemeRecord = {
  label: string;
  summary: string;
};

export type AiFrontierEventRecord = {
  title: string;
  summary: string;
  significance: string;
  source_item_ids: string[];
};

export type AiFrontierProjectCardRecord = {
  title: string;
  source_label: string;
  summary: string;
  why_it_matters: string;
  official_url?: string | null;
  repo_url?: string | null;
  docs_url?: string | null;
  tags: string[];
  source_item_ids: string[];
};

export type AiFrontierReferenceSourceRecord = {
  label: string;
  url: string;
  source_kind: "official" | "repository" | "docs" | "paper" | "other";
};

export type AiFrontierResearchOutputRecord = {
  frontier_summary: string;
  trend_judgment: string;
  themes: AiFrontierThemeRecord[];
  events: AiFrontierEventRecord[];
  project_cards: AiFrontierProjectCardRecord[];
  reference_sources: AiFrontierReferenceSourceRecord[];
};

export type AiHotTrackerBriefSignalRecord = {
  title: string;
  summary: string;
  why_now: string;
  impact: string;
  audience: string[];
  change_type: "new" | "continuing" | "cooling";
  priority_level: "high" | "medium" | "low";
  confidence: "high" | "medium" | "low";
  source_item_ids: string[];
};

export type AiHotTrackerKeepWatchingRecord = {
  title: string;
  reason: string;
  source_item_ids: string[];
};

export type AiHotTrackerReferenceSourceRecord = {
  label: string;
  url: string;
  source_kind: "official" | "repository" | "docs" | "paper" | "media" | "other";
};

export type AiHotTrackerBriefOutputRecord = {
  headline: string;
  summary: string;
  change_state: "first_run" | "meaningful_update" | "steady_state" | "degraded" | "failed";
  signals: AiHotTrackerBriefSignalRecord[];
  keep_watching: AiHotTrackerKeepWatchingRecord[];
  blindspots: string[];
  reference_sources: AiHotTrackerReferenceSourceRecord[];
};

export type AiHotTrackerSourceDefinitionRecord = {
  id: string;
  label: string;
  category: string;
  source_family: "official" | "media" | "research" | "open_source";
  source_kind: "rss_feed" | "atom_feed" | "html_list";
  parse_mode?: "rss_feed" | "atom_feed" | "html_list" | null;
  feed_url: string;
  site_url?: string | null;
  tags: string[];
  audience_tags: string[];
  authority_weight: number;
};

export type AiHotTrackerScoreBreakdownRecord = {
  novelty: number;
  freshness: number;
  authority: number;
  relevance: number;
  impact: number;
};

export type AiHotTrackerSourceItemRecord = {
  id: string;
  source_id: string;
  source_label: string;
  source_kind: "rss_feed" | "atom_feed" | "html_list";
  category: string;
  source_family: "official" | "media" | "research" | "open_source";
  title: string;
  url: string;
  summary: string;
  published_at?: string | null;
  tags: string[];
  audience_tags: string[];
  rank_score: number;
  score_breakdown: AiHotTrackerScoreBreakdownRecord;
  rank_reason: string;
  cluster_id?: string | null;
  event_id?: string | null;
};

export type AiHotTrackerSourceFailureRecord = {
  source_id: string;
  source_label: string;
  message: string;
};

export type AiHotTrackerReportRecord = {
  title: string;
  question: string;
  output: AiHotTrackerBriefOutputRecord;
  source_catalog: AiHotTrackerSourceDefinitionRecord[];
  source_items: AiHotTrackerSourceItemRecord[];
  source_failures: AiHotTrackerSourceFailureRecord[];
  source_set: JsonObject;
  generated_at: string;
  degraded_reason?: string | null;
};

export type AiHotTrackerTrackingProfileRecord = {
  topic: string;
  scope: string;
  source_strategy: "allowlist_curated";
  enabled_categories: string[];
  cadence: "manual" | "daily" | "twice_daily" | "weekly";
  alert_threshold: number;
  max_items_per_run: number;
};

export type AiHotTrackerTrackingRunDeltaRecord = {
  previous_run_id?: string | null;
  change_state: "first_run" | "meaningful_update" | "steady_state" | "degraded" | "failed";
  summary: string;
  should_notify: boolean;
  priority_level: "high" | "medium" | "low";
  notify_reason?: string | null;
  new_item_count: number;
  continuing_item_count: number;
  cooled_down_item_count: number;
  new_titles: string[];
  continuing_titles: string[];
  cooled_down_titles: string[];
};

export type AiHotTrackerTrackingRunRecord = {
  id: string;
  workspace_id: string;
  previous_run_id?: string | null;
  created_by: string;
  trigger_kind: "manual" | "scheduled";
  status: "completed" | "degraded" | "failed";
  title: string;
  question: string;
  profile: AiHotTrackerTrackingProfileRecord;
  output: AiHotTrackerBriefOutputRecord;
  source_catalog: AiHotTrackerSourceDefinitionRecord[];
  source_items: AiHotTrackerSourceItemRecord[];
  source_failures: AiHotTrackerSourceFailureRecord[];
  source_set: JsonObject;
  delta: AiHotTrackerTrackingRunDeltaRecord;
  follow_ups: AiFrontierFollowUpEntryRecord[];
  degraded_reason?: string | null;
  error_message?: string | null;
  generated_at: string;
  created_at: string;
  updated_at: string;
};

export type AiHotTrackerTrackingRunCreatePayload = {
  trigger_kind?: "manual" | "scheduled";
};

export type AiHotTrackerTrackingRunFollowUpPayload = {
  question: string;
  focus_label?: string;
  focus_context?: string;
};

export type AiHotTrackerTrackingRunFollowUpResponse = {
  answer: string;
  follow_up: AiFrontierFollowUpEntryRecord;
};

export type AiFrontierFollowUpEntryRecord = {
  question: string;
  answer: string;
  grounding_source_item_ids?: string[];
  grounding_event_ids?: string[];
  grounding_blindspots?: string[];
  grounding_notes?: string[];
  created_at?: string | null;
};

export type AiFrontierResearchRecordWritePayload = {
  title?: string;
  question: string;
  answer_text?: string | null;
  output: AiFrontierResearchOutputRecord;
  follow_ups: AiFrontierFollowUpEntryRecord[];
  source_set?: JsonObject;
  conversation_id?: string;
  source_trace_id?: string;
};

export type AiHotTrackerFollowUpPayload = {
  report_question: string;
  report_answer?: string | null;
  report_output: AiHotTrackerBriefOutputRecord;
  follow_up_question: string;
  prior_follow_ups: AiFrontierFollowUpEntryRecord[];
  source_set?: JsonObject;
};

export type AiHotTrackerFollowUpResponse = {
  answer: string;
  follow_up: AiFrontierFollowUpEntryRecord;
};

export type AiFrontierResearchRecord = {
  id: string;
  workspace_id: string;
  conversation_id?: string | null;
  source_run_id?: string | null;
  source_trace_id?: string | null;
  created_by: string;
  title: string;
  question: string;
  answer_text?: string | null;
  output: AiFrontierResearchOutputRecord;
  follow_ups: AiFrontierFollowUpEntryRecord[];
  source_set: JsonObject;
  created_at: string;
  updated_at: string;
};

export type AiHotTrackerSignalClusterRecord = {
  cluster_id: string;
  event_id: string;
  title: string;
  category: string;
  representative_item_id: string;
  source_item_ids: string[];
  source_labels: string[];
  rank_score: number;
  priority_level: "high" | "medium" | "low";
  fingerprint: string;
  is_new: boolean;
  is_continuing: boolean;
  is_cooling: boolean;
};

export type AiHotTrackerSignalMemoryRecord = {
  event_id: string;
  fingerprint: string;
  title: string;
  category: string;
  first_seen_at: string;
  last_seen_at: string;
  continuity_state: "new" | "continuing" | "cooling";
  activity_state: "heating" | "continuing" | "cooling" | "replaced";
  source_families: ("official" | "media" | "research" | "open_source")[];
  source_item_ids: string[];
  source_labels: string[];
  latest_priority_level: "high" | "medium" | "low";
  latest_rank_score: number;
  last_seen_run_id?: string | null;
  streak_count: number;
  cooling_since?: string | null;
  superseded_by_event_id?: string | null;
  last_cluster_snapshot: JsonObject;
  note?: string | null;
};

export type AiHotTrackerAgentRoleTraceRecord = {
  role: "scout" | "resolver" | "analyst" | "editor" | "evaluator" | "follow_up";
  summary: string;
  status: "completed" | "degraded" | "failed";
  details: JsonObject;
};

export type AiHotTrackerTrackingStateRecord = {
  workspace_id: string;
  tracking_profile: AiHotTrackerTrackingProfileRecord;
  last_checked_at?: string | null;
  last_successful_scan_at?: string | null;
  next_due_at?: string | null;
  consecutive_failure_count: number;
  last_error_message?: string | null;
  latest_saved_run_id?: string | null;
  latest_saved_run_generated_at?: string | null;
  latest_change_state?:
    | "first_run"
    | "meaningful_update"
    | "steady_state"
    | "degraded"
    | "failed"
    | null;
  latest_notify_reason?: string | null;
  latest_meaningful_update_at?: string | null;
};

export type AiHotTrackerJudgmentFindingRecord = {
  code: string;
  status: "pass" | "warn" | "fail";
  summary: string;
  details: JsonObject;
};

export type AiHotTrackerRunEvaluationRecord = {
  run_id: string;
  ranked_items: AiHotTrackerSourceItemRecord[];
  clustered_signals: AiHotTrackerSignalClusterRecord[];
  event_memories: AiHotTrackerSignalMemoryRecord[];
  source_failures: AiHotTrackerSourceFailureRecord[];
  output: AiHotTrackerBriefOutputRecord;
  delta: AiHotTrackerTrackingRunDeltaRecord;
  agent_trace: AiHotTrackerAgentRoleTraceRecord[];
  quality_checks: AiHotTrackerJudgmentFindingRecord[];
  judgment_findings: AiHotTrackerJudgmentFindingRecord[];
  brief_alignment_checks: AiHotTrackerJudgmentFindingRecord[];
  follow_up_grounding_checks: AiHotTrackerJudgmentFindingRecord[];
};

export type AiHotTrackerReplayStepEvaluationRecord = {
  label: string;
  status: "pass" | "fail";
  delta_change_state: AiHotTrackerTrackingRunDeltaRecord["change_state"];
  should_notify: boolean;
  notify_reason: string | null;
  ranked_item_ids: string[];
  cluster_titles: string[];
  findings: AiHotTrackerJudgmentFindingRecord[];
};

export type AiHotTrackerReplayCaseEvaluationRecord = {
  case_id: string;
  title: string;
  description: string;
  status: "pass" | "fail";
  steps: AiHotTrackerReplayStepEvaluationRecord[];
};

export type AiHotTrackerReplayEvaluationRecord = {
  status: "pass" | "fail";
  total_case_count: number;
  passed_case_count: number;
  failed_case_count: number;
  cases: AiHotTrackerReplayCaseEvaluationRecord[];
};

export type ChatSource = {
  document_id: string;
  chunk_id: string;
  document_title: string;
  chunk_index: number;
  snippet: string;
  source_kind: "workspace_document" | "external_context";
};

export type ChatToolStep = {
  tool_name: string;
  summary: string;
  detail?: string | null;
};

export type ResearchExternalResourceSnapshotItemRecord = {
  resource_id: string;
  title: string;
  source_label: string;
  snippet: string;
};

export type ResearchExternalResourceSnapshotRecord = {
  id: string;
  workspace_id: string;
  conversation_id?: string | null;
  created_by: string;
  connector_id: string;
  source_run_id?: string | null;
  title: string;
  analysis_focus?: string | null;
  search_query: string;
  resource_count: number;
  resources: ResearchExternalResourceSnapshotItemRecord[];
  created_at: string;
  updated_at: string;
};

export type ChatResponsePayload = {
  answer: string;
  sources: ChatSource[];
  trace_id: string;
  mode: 'rag' | 'research_tool_assisted' | 'research_external_context';
  tool_steps: ChatToolStep[];
  external_resource_snapshot?: ResearchExternalResourceSnapshotRecord | null;
  frontier_output?: AiFrontierResearchOutputRecord | null;
  research_record?: AiFrontierResearchRecord | null;
};

export type ResearchAnalysisRunStatus = "pending" | "running" | "completed" | "degraded" | "failed";

export type ResearchAnalysisRunCreatePayload = {
  question: string;
  conversation_id?: string;
  mode?: "research_tool_assisted" | "research_external_context";
  external_resource_snapshot_id?: string;
};

export type ResearchAnalysisRunMemoryRecord = {
  memory_version: number;
  summary: string;
  evidence_state: string;
  recommended_next_step: string;
  source_titles: string[];
};

export type ResearchAnalysisRunRecord = {
  id: string;
  workspace_id: string;
  conversation_id: string;
  created_by: string;
  status: ResearchAnalysisRunStatus;
  question: string;
  mode: "research_tool_assisted" | "research_external_context";
  resumed_from_run_id?: string | null;
  answer?: string | null;
  trace_id?: string | null;
  sources: ChatSource[];
  tool_steps: ChatToolStep[];
  external_resource_snapshot?: ResearchExternalResourceSnapshotRecord | null;
  frontier_output?: AiFrontierResearchOutputRecord | null;
  research_record?: AiFrontierResearchRecord | null;
  run_memory?: ResearchAnalysisRunMemoryRecord | null;
  analysis_focus?: string | null;
  search_query?: string | null;
  degraded_reason?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  updated_at: string;
};

export type ResearchAnalysisReviewRecord = {
  run_id: string;
  question: string;
  status: ResearchAnalysisRunStatus;
  mode: "research_tool_assisted" | "research_external_context";
  trace_id?: string | null;
  resumed_from_run_id?: string | null;
  degraded_reason?: string | null;
  run_memory_summary?: string | null;
  connector_id?: string | null;
  connector_consent_state?: "granted" | "not_granted" | "revoked" | null;
  external_context_used?: boolean | null;
  external_match_count?: number | null;
  selected_external_resource_snapshot_id?: string | null;
  selected_external_resource_snapshot_title?: string | null;
  external_resource_snapshot_id?: string | null;
  external_resource_snapshot_title?: string | null;
  resource_selection_mode?: "explicit" | "auto" | "none" | null;
  context_selection_mode?: "snapshot" | "mcp_resource" | "none" | null;
  mcp_server_id?: string | null;
  mcp_endpoint_source?: "repo_local" | "external_configured" | null;
  mcp_endpoint_display_name?: string | null;
  mcp_endpoint_auth_state?: "not_required" | "configured" | "missing" | "denied" | null;
  mcp_endpoint_auth_detail?: string | null;
  mcp_resource_id?: string | null;
  mcp_resource_uri?: string | null;
  mcp_resource_display_name?: string | null;
  mcp_tool_name?: string | null;
  mcp_prompt_name?: string | null;
  mcp_transport?: "local_inproc" | "stdio_process" | null;
  mcp_read_status?:
    | "consent_required"
    | "consent_revoked"
    | "auth_required"
    | "auth_denied"
    | "snapshot_reused"
    | "used"
    | "transport_unavailable"
    | "no_useful_matches"
    | null;
  mcp_transport_error?: string | null;
  passed: boolean;
  issues: string[];
  regression_baseline: JsonObject;
  created_at: string;
  completed_at?: string | null;
};

export type ResearchAnalysisReviewResponse = {
  baseline_version: string;
  reviewed_count: number;
  passing_count: number;
  failing_count: number;
  items: ResearchAnalysisReviewRecord[];
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

export type ConnectorDefinitionRecord = {
  id: string;
  display_name: string;
  summary: string;
  kind: "external_context";
  consent_scope: "workspace";
  module_types: string[];
  requires_consent: boolean;
  pilot_status: "bounded_pilot";
};

export type WorkspaceConnectorStatusRecord = {
  connector: ConnectorDefinitionRecord;
  workspace_id: string;
  consent_state: "not_granted" | "granted" | "revoked";
  granted_by?: string | null;
  consent_note?: string | null;
  granted_at?: string | null;
  revoked_at?: string | null;
  updated_at?: string | null;
};

export type ConnectorConsentGrantPayload = {
  consent_note?: string;
};

export type ConnectorConsentRevokePayload = {
  consent_note?: string;
};
