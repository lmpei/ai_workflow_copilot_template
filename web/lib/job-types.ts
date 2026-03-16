import type {
  JsonObject,
  ResearchDocumentSummary,
  ResearchMatch,
  ScenarioEvidenceItem,
} from "./types";

export type JobTaskType = "jd_summary" | "resume_match";

export type JobArtifacts = {
  document_count: number;
  match_count: number;
  documents: ResearchDocumentSummary[];
  matches: ResearchMatch[];
  tool_call_ids: string[];
  fit_signal?: string | null;
  recommended_next_step?: string | null;
};

export type JobTaskResult = {
  module_type: "job";
  task_type: JobTaskType;
  title: string;
  summary: string;
  highlights: string[];
  evidence: ScenarioEvidenceItem[];
  artifacts: JobArtifacts;
  metadata: JsonObject;
};
