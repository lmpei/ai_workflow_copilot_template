"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createWorkspaceTask,
  getWorkspace,
  isApiClientError,
  listWorkspaceTasks,
} from "../../lib/api";
import type {
  JobArtifacts,
  JobEvidenceStatus,
  JobFinding,
  JobFitAssessment,
  JobFitSignal,
  JobReviewBrief,
  JobTaskInput,
  JobTaskResult,
  JobTaskType,
  JsonObject,
  TaskRecord,
  Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type JobAssistantPanelProps = {
  workspaceId: string;
};

const TASK_OPTIONS: Record<
  JobTaskType,
  {
    label: string;
    description: string;
    placeholder: string;
  }
> = {
  jd_summary: {
    label: "JD Summary",
    description: "Summarize role requirements, hiring signals, and reviewer-facing next steps.",
    placeholder: "Example: Senior backend engineer role focused on APIs, reliability, and Python.",
  },
  resume_match: {
    label: "Resume Match",
    description: "Assess grounded fit between indexed hiring materials and the target role.",
    placeholder: "Example: Platform engineer role with Python, systems design, and reliability focus.",
  },
};

const SENIORITY_OPTIONS = ["", "intern", "junior", "mid", "senior", "staff", "principal"] as const;

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeOptionalString(value: unknown): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : undefined;
}

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const normalized: string[] = [];
  const seen = new Set<string>();
  for (const item of value) {
    if (typeof item !== "string") {
      continue;
    }
    const trimmed = item.trim();
    if (!trimmed || seen.has(trimmed)) {
      continue;
    }
    normalized.push(trimmed);
    seen.add(trimmed);
  }
  return normalized;
}

function parseJobTaskResult(task: TaskRecord): JobTaskResult | null {
  const result = task.output_json.result;
  if (!isJsonObject(result)) {
    return null;
  }

  if (
    result.module_type !== "job" ||
    typeof result.task_type !== "string" ||
    typeof result.title !== "string" ||
    typeof result.summary !== "string" ||
    !Array.isArray(result.highlights) ||
    !Array.isArray(result.evidence) ||
    !isJsonObject(result.artifacts) ||
    !isJsonObject(result.metadata)
  ) {
    return null;
  }

  return result as unknown as JobTaskResult;
}

function parseJobTaskInput(task: TaskRecord, result: JobTaskResult | null = null): JobTaskInput {
  const source = result?.input && isJsonObject(result.input) ? result.input : task.input_json;
  return {
    target_role: normalizeOptionalString(source.target_role),
    seniority: normalizeOptionalString(source.seniority),
    must_have_skills: normalizeStringList(source.must_have_skills),
    preferred_skills: normalizeStringList(source.preferred_skills),
    hiring_context: normalizeOptionalString(source.hiring_context),
  };
}

function parseEntryTaskTypes(workspace: Workspace | null): JobTaskType[] {
  const entryTaskTypes = workspace?.module_config_json.entry_task_types;
  if (!Array.isArray(entryTaskTypes)) {
    return ["jd_summary", "resume_match"];
  }

  const supported = entryTaskTypes.filter(
    (entryTaskType): entryTaskType is JobTaskType =>
      entryTaskType === "jd_summary" || entryTaskType === "resume_match",
  );
  return supported.length > 0 ? supported : ["jd_summary", "resume_match"];
}

function sortTasks(tasks: TaskRecord[]): TaskRecord[] {
  return [...tasks].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

function renderStatus(status: TaskRecord["status"]) {
  const statusStyles: Record<TaskRecord["status"], { label: string; color: string }> = {
    pending: { label: "pending", color: "#92400e" },
    running: { label: "running", color: "#1d4ed8" },
    completed: { label: "completed", color: "#15803d" },
    failed: { label: "failed", color: "#b91c1c" },
  };
  const style = statusStyles[status];

  return (
    <span
      style={{
        display: "inline-block",
        borderRadius: 999,
        padding: "2px 10px",
        fontSize: 12,
        fontWeight: 600,
        color: style.color,
        backgroundColor: `${style.color}14`,
        textTransform: "uppercase",
      }}
    >
      {style.label}
    </span>
  );
}

function renderEvidenceStatusBadge(evidenceStatus: JobEvidenceStatus) {
  const styles: Record<JobEvidenceStatus, { label: string; color: string }> = {
    grounded_matches: { label: "Grounded matches", color: "#166534" },
    documents_only: { label: "Documents only", color: "#92400e" },
    no_documents: { label: "No documents", color: "#b91c1c" },
  };
  const style = styles[evidenceStatus];

  return (
    <span
      style={{
        display: "inline-block",
        borderRadius: 999,
        padding: "4px 10px",
        fontSize: 12,
        fontWeight: 600,
        color: style.color,
        backgroundColor: `${style.color}14`,
      }}
    >
      {style.label}
    </span>
  );
}

function renderFitSignalBadge(fitSignal: JobFitSignal) {
  const styles: Record<JobFitSignal, { label: string; color: string }> = {
    grounded_match_found: { label: "Grounded match", color: "#166534" },
    role_requirements_grounded: { label: "Role grounded", color: "#0369a1" },
    insufficient_grounding: { label: "Needs more grounding", color: "#92400e" },
    no_documents_available: { label: "No materials", color: "#b91c1c" },
  };
  const style = styles[fitSignal];

  return (
    <span
      style={{
        display: "inline-block",
        borderRadius: 999,
        padding: "4px 10px",
        fontSize: 12,
        fontWeight: 600,
        color: style.color,
        backgroundColor: `${style.color}14`,
      }}
    >
      {style.label}
    </span>
  );
}

function renderArtifactStats(artifacts: JobArtifacts) {
  const cards = [
    { label: "Documents", value: artifacts.document_count },
    { label: "Matches", value: artifacts.match_count },
    { label: "Tool calls", value: artifacts.tool_call_ids.length },
  ];

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        {cards.map((card) => (
          <div
            key={card.label}
            style={{
              border: "1px solid #cbd5e1",
              borderRadius: 12,
              minWidth: 120,
              padding: 12,
            }}
          >
            <div style={{ color: "#475569", fontSize: 12, textTransform: "uppercase" }}>{card.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{card.value}</div>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {renderEvidenceStatusBadge(artifacts.evidence_status)}
        {renderFitSignalBadge(artifacts.fit_signal)}
      </div>
    </div>
  );
}

function extractTargetRole(task: TaskRecord, result: JobTaskResult | null = null): string | null {
  const input = parseJobTaskInput(task, result);
  return input.target_role && input.target_role.length > 0 ? input.target_role : null;
}

function formatRoleSnapshot(input: JobTaskInput): string {
  const segments: string[] = [];
  if (input.seniority) {
    segments.push(`Seniority ${input.seniority}`);
  }
  if (input.must_have_skills.length > 0) {
    segments.push(`Must-have: ${input.must_have_skills.slice(0, 2).join(", ")}`);
  }
  return segments.join(" | ");
}

function parseSkillList(value: string): string[] {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter((item, index, allItems) => item.length > 0 && allItems.indexOf(item) === index);
}

function renderListSection({ title, items, emptyText }: { title: string; items: string[]; emptyText: string }) {
  return (
    <div>
      <strong>{title}</strong>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{emptyText}</p>
      )}
    </div>
  );
}

function renderFindings(findings: JobFinding[]) {
  return (
    <div>
      <strong>Grounded findings</strong>
      {findings.length > 0 ? (
        <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
          {findings.map((finding) => (
            <li
              key={`${finding.title}-${finding.summary}`}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                padding: 12,
              }}
            >
              <div style={{ fontWeight: 600 }}>{finding.title}</div>
              <p style={{ color: "#475569", marginBottom: 0, marginTop: 8 }}>{finding.summary}</p>
              {finding.evidence_ref_ids.length > 0 ? (
                <div style={{ color: "#475569", fontSize: 14, marginTop: 8 }}>
                  Evidence refs: {finding.evidence_ref_ids.join(", ")}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p>No grounded hiring findings were produced for this run.</p>
      )}
    </div>
  );
}

function renderReviewBrief(reviewBrief: JobReviewBrief) {
  return (
    <div
      style={{
        border: "1px solid #cbd5e1",
        borderRadius: 12,
        padding: 16,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
        <strong>Hiring brief</strong>
        {renderEvidenceStatusBadge(reviewBrief.evidence_status)}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>Role summary:</strong> {reviewBrief.role_summary}
        </div>
        {reviewBrief.seniority ? (
          <div>
            <strong>Seniority:</strong> {reviewBrief.seniority}
          </div>
        ) : null}
        <div>
          <strong>Must-have skills:</strong>{" "}
          {reviewBrief.must_have_skills.length > 0 ? reviewBrief.must_have_skills.join(", ") : "Not specified"}
        </div>
        <div>
          <strong>Preferred skills:</strong>{" "}
          {reviewBrief.preferred_skills.length > 0 ? reviewBrief.preferred_skills.join(", ") : "Not specified"}
        </div>
        {reviewBrief.hiring_context ? (
          <div>
            <strong>Hiring context:</strong> {reviewBrief.hiring_context}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function renderAssessment(assessment: JobFitAssessment, recommendedNextStep: string) {
  return (
    <div
      style={{
        border: "1px solid #cbd5e1",
        borderRadius: 12,
        padding: 16,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
        <strong>Fit assessment</strong>
        {renderEvidenceStatusBadge(assessment.evidence_status)}
        {renderFitSignalBadge(assessment.fit_signal)}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>Recommended outcome:</strong> {assessment.recommended_outcome}
        </div>
        <div>
          <strong>Confidence note:</strong> {assessment.confidence_note}
        </div>
        <div>
          <strong>Rationale:</strong> {assessment.rationale}
        </div>
        <div>
          <strong>Recommended next step:</strong> {recommendedNextStep}
        </div>
      </div>
    </div>
  );
}

export default function JobAssistantPanel({ workspaceId }: JobAssistantPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<JobTaskType>("jd_summary");
  const [targetRole, setTargetRole] = useState("");
  const [seniority, setSeniority] = useState<(typeof SENIORITY_OPTIONS)[number]>("");
  const [mustHaveSkillsText, setMustHaveSkillsText] = useState("");
  const [preferredSkillsText, setPreferredSkillsText] = useState("");
  const [hiringContext, setHiringContext] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const availableTaskTypes = useMemo(() => parseEntryTaskTypes(workspace), [workspace]);

  useEffect(() => {
    if (!availableTaskTypes.includes(taskType)) {
      setTaskType(availableTaskTypes[0] ?? "jd_summary");
    }
  }, [availableTaskTypes, taskType]);

  const loadWorkspace = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      return;
    }

    setIsLoadingWorkspace(true);
    try {
      setWorkspace(await getWorkspace(session.accessToken, workspaceId));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load workspace");
    } finally {
      setIsLoadingWorkspace(false);
    }
  }, [session, workspaceId]);

  const loadTasks = useCallback(
    async (silent = false) => {
      if (!session) {
        setTasks([]);
        setSelectedTaskId(null);
        return;
      }

      if (!silent) {
        setIsLoadingTasks(true);
      }

      try {
        const loadedTasks = sortTasks(await listWorkspaceTasks(session.accessToken, workspaceId));
        setTasks(loadedTasks);
        setSelectedTaskId((currentSelectedTaskId) => {
          if (currentSelectedTaskId && loadedTasks.some((task) => task.id === currentSelectedTaskId)) {
            return currentSelectedTaskId;
          }
          return loadedTasks[0]?.id ?? null;
        });
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load job tasks");
      } finally {
        if (!silent) {
          setIsLoadingTasks(false);
        }
      }
    },
    [session, workspaceId],
  );

  useEffect(() => {
    void loadWorkspace();
    void loadTasks();
  }, [loadTasks, loadWorkspace]);

  useEffect(() => {
    if (!session) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void loadTasks(true);
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [loadTasks, session]);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? null,
    [selectedTaskId, tasks],
  );
  const selectedResult = useMemo(
    () => (selectedTask ? parseJobTaskResult(selectedTask) : null),
    [selectedTask],
  );
  const selectedInput = useMemo(
    () => (selectedTask ? parseJobTaskInput(selectedTask, selectedResult) : null),
    [selectedResult, selectedTask],
  );

  const handleCreateTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      return;
    }

    const mustHaveSkills = parseSkillList(mustHaveSkillsText);
    const preferredSkills = parseSkillList(preferredSkillsText);
    const input: JsonObject = {};
    const normalizedTargetRole = targetRole.trim();
    const normalizedHiringContext = hiringContext.trim();

    if (normalizedTargetRole) {
      input.target_role = normalizedTargetRole;
    }
    if (seniority) {
      input.seniority = seniority;
    }
    if (mustHaveSkills.length > 0) {
      input.must_have_skills = mustHaveSkills;
    }
    if (preferredSkills.length > 0) {
      input.preferred_skills = preferredSkills;
    }
    if (normalizedHiringContext) {
      input.hiring_context = normalizedHiringContext;
    }

    setIsCreating(true);
    setErrorMessage(null);

    try {
      const createdTask = await createWorkspaceTask(session.accessToken, workspaceId, {
        task_type: taskType,
        input,
      });
      setTasks((currentTasks) => sortTasks([createdTask, ...currentTasks]));
      setSelectedTaskId(createdTask.id);
      setTargetRole("");
      setSeniority("");
      setMustHaveSkillsText("");
      setPreferredSkillsText("");
      setHiringContext("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to launch job task");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Job Assistant">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to run job tasks and inspect structured hiring outputs." />;
  }

  return (
    <>
      <SectionCard
        title="Job Assistant"
        description="Launch structured hiring workflows, inspect evidence quality, and review grounded fit assessments from indexed hiring materials."
      >
        {isLoadingWorkspace ? <p>Loading workspace configuration...</p> : null}
        {workspace ? (
          <div style={{ display: "grid", gap: 8 }}>
            <div>
              <strong>Workspace:</strong> {workspace.name}
            </div>
            <div>
              <strong>Module:</strong> {workspace.module_type}
            </div>
            <div>
              <strong>Features:</strong>{" "}
              {Array.isArray(workspace.module_config_json.features)
                ? workspace.module_config_json.features.join(", ")
                : "document_intake, structured_extraction, tasks, evals"}
            </div>
          </div>
        ) : null}
        {workspace?.module_type && workspace.module_type !== "job" ? (
          <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 12 }}>
            This surface is only available for job workspaces. Current module: {workspace.module_type}.
          </p>
        ) : null}
      </SectionCard>

      <SectionCard
        title="Launch hiring review"
        description="Capture the role focus, skills, and hiring context you already know, then run a grounded job task against the indexed workspace materials."
      >
        <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12, maxWidth: 760 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Task type</span>
            <select
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
              onChange={(event) => setTaskType(event.target.value as JobTaskType)}
              value={taskType}
            >
              {availableTaskTypes.map((availableTaskType) => (
                <option key={availableTaskType} value={availableTaskType}>
                  {TASK_OPTIONS[availableTaskType].label}
                </option>
              ))}
            </select>
          </label>
          <p style={{ color: "#475569", margin: 0 }}>{TASK_OPTIONS[taskType].description}</p>

          <label style={{ display: "grid", gap: 6 }}>
            <span>Target role</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
              onChange={(event) => setTargetRole(event.target.value)}
              placeholder={TASK_OPTIONS[taskType].placeholder}
              rows={4}
              value={targetRole}
            />
          </label>

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span>Seniority</span>
              <select
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setSeniority(event.target.value as (typeof SENIORITY_OPTIONS)[number])}
                value={seniority}
              >
                {SENIORITY_OPTIONS.map((option) => (
                  <option key={option || "none"} value={option}>
                    {option || "Not specified"}
                  </option>
                ))}
              </select>
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>Hiring context</span>
              <input
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setHiringContext(event.target.value)}
                placeholder="Platform team, API modernization, internal tooling..."
                type="text"
                value={hiringContext}
              />
            </label>
          </div>

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span>Must-have skills</span>
              <textarea
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setMustHaveSkillsText(event.target.value)}
                placeholder={"One skill per line or comma separated\nPython\nAPI design\nSystem reliability"}
                rows={5}
                value={mustHaveSkillsText}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>Preferred skills</span>
              <textarea
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setPreferredSkillsText(event.target.value)}
                placeholder={"One skill per line or comma separated\nDistributed systems\nData pipelines"}
                rows={5}
                value={preferredSkillsText}
              />
            </label>
          </div>

          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button
            disabled={isCreating || (workspace?.module_type !== undefined && workspace.module_type !== "job")}
            type="submit"
          >
            {isCreating ? "Launching..." : "Launch job task"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Job runs"
        description="Tasks refresh automatically every 2 seconds so you can watch hiring reviews settle into a grounded structured result."
      >
        {isLoadingTasks ? <p>Loading job tasks...</p> : null}
        {!isLoadingTasks && tasks.length === 0 ? <p>No job tasks yet. Launch one to generate a structured hiring workflow.</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {tasks.map((task) => {
            const result = parseJobTaskResult(task);
            const input = parseJobTaskInput(task, result);
            const roleSnapshot = formatRoleSnapshot(input);
            return (
              <li
                key={task.id}
                style={{
                  border: task.id === selectedTaskId ? "1px solid #0f172a" : "1px solid #cbd5e1",
                  borderRadius: 12,
                  marginBottom: 12,
                  padding: 12,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 6 }}>
                  <strong>{TASK_OPTIONS[task.task_type as JobTaskType]?.label ?? task.task_type}</strong>
                  {renderStatus(task.status)}
                  {result ? renderFitSignalBadge(result.artifacts.fit_signal) : null}
                </div>
                <div style={{ color: "#475569", marginBottom: 6 }}>
                  {result?.summary ?? extractTargetRole(task, result) ?? "No custom role focus provided."}
                </div>
                {roleSnapshot ? (
                  <div style={{ color: "#64748b", fontSize: 14, marginBottom: 6 }}>{roleSnapshot}</div>
                ) : null}
                <div>Task ID: {task.id}</div>
                <div>Updated: {new Date(task.updated_at).toLocaleString()}</div>
                <div style={{ marginTop: 8 }}>
                  <button onClick={() => setSelectedTaskId(task.id)} type="button">
                    Open result
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </SectionCard>

      <SectionCard
        title="Structured hiring result"
        description="Inspect the hiring brief, grounded findings, fit assessment, and follow-up guidance from the selected job task."
      >
        {!selectedTask ? <p>Select a job task to inspect its output.</p> : null}
        {selectedTask ? (
          <div style={{ display: "grid", gap: 16 }}>
            <div style={{ display: "grid", gap: 6 }}>
              <div>
                <strong>Task ID:</strong> {selectedTask.id}
              </div>
              <div>
                <strong>Status:</strong> {renderStatus(selectedTask.status)}
              </div>
              <div>
                <strong>Task type:</strong> {TASK_OPTIONS[selectedTask.task_type as JobTaskType]?.label ?? selectedTask.task_type}
              </div>
              {selectedInput?.target_role ? (
                <div>
                  <strong>Target role:</strong> {selectedInput.target_role}
                </div>
              ) : null}
            </div>

            {selectedTask.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>Job task error</strong>
                <p style={{ color: "#b91c1c", marginBottom: 0 }}>{selectedTask.error_message}</p>
              </div>
            ) : null}

            {selectedResult ? (
              <>
                <div>
                  <h3 style={{ marginBottom: 8, marginTop: 0 }}>{selectedResult.title}</h3>
                  <p style={{ margin: 0 }}>{selectedResult.summary}</p>
                </div>

                {renderArtifactStats(selectedResult.artifacts)}
                {renderReviewBrief(selectedResult.review_brief)}
                {renderAssessment(selectedResult.assessment, selectedResult.artifacts.recommended_next_step)}
                {renderFindings(selectedResult.findings)}

                {renderListSection({
                  title: "Gaps",
                  items: selectedResult.gaps,
                  emptyText: "No explicit hiring gaps were produced for this run.",
                })}

                {renderListSection({
                  title: "Highlights",
                  items: selectedResult.highlights,
                  emptyText: "No highlight bullets were produced for this run.",
                })}

                {renderListSection({
                  title: "Open questions",
                  items: selectedResult.open_questions,
                  emptyText: "No further open questions were produced for this run.",
                })}

                {renderListSection({
                  title: "Next steps",
                  items: selectedResult.next_steps,
                  emptyText: "No next steps were produced for this run.",
                })}

                <div>
                  <strong>Linked evidence</strong>
                  {selectedResult.evidence.length > 0 ? (
                    <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
                      {selectedResult.evidence.map((evidence) => (
                        <li
                          key={evidence.ref_id}
                          style={{
                            border: "1px solid #cbd5e1",
                            borderRadius: 12,
                            padding: 12,
                          }}
                        >
                          <div style={{ fontWeight: 600 }}>{evidence.title ?? evidence.kind}</div>
                          {evidence.snippet ? (
                            <p style={{ color: "#475569", marginBottom: 8, marginTop: 8 }}>{evidence.snippet}</p>
                          ) : null}
                          <div style={{ color: "#475569", fontSize: 14 }}>Ref ID: {evidence.ref_id}</div>
                          {typeof evidence.metadata.document_id === "string" ? (
                            <div style={{ marginTop: 8 }}>
                              <Link href={`/workspaces/${workspaceId}/documents`}>Open hiring context</Link>
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No linked evidence was returned. This usually means the workspace had limited indexed hiring context.</p>
                  )}
                </div>
              </>
            ) : (
              <p>
                This task does not have a completed structured job payload yet. If it is still running,
                wait for the next refresh cycle.
              </p>
            )}
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}
