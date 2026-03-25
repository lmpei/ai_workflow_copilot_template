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
  JsonObject,
  SupportArtifacts,
  SupportCaseBrief,
  SupportEvidenceStatus,
  SupportFinding,
  SupportReplyDraft,
  SupportSeverity,
  SupportTaskInput,
  SupportTaskResult,
  SupportTaskType,
  TaskRecord,
  Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type SupportCopilotPanelProps = {
  workspaceId: string;
};

const TASK_OPTIONS: Record<
  SupportTaskType,
  {
    label: string;
    description: string;
    placeholder: string;
  }
> = {
  ticket_summary: {
    label: "Ticket Summary",
    description: "Summarize the case, identify grounded findings, and recommend triage.",
    placeholder: "Example: Customer cannot reset their password after clicking the email link.",
  },
  reply_draft: {
    label: "Reply Draft",
    description: "Draft a customer response grounded in the current workspace knowledge base.",
    placeholder: "Example: Customer asks how to fix an expired password reset link.",
  },
};

const SEVERITY_OPTIONS: Array<{
  value: "" | SupportSeverity;
  label: string;
}> = [
  { value: "", label: "Not specified" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

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

function parseSupportTaskResult(task: TaskRecord): SupportTaskResult | null {
  const result = task.output_json.result;
  if (!isJsonObject(result)) {
    return null;
  }

  if (
    result.module_type !== "support" ||
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

  return result as unknown as SupportTaskResult;
}

function parseSupportTaskInput(task: TaskRecord, result: SupportTaskResult | null = null): SupportTaskInput {
  const source = result?.input && isJsonObject(result.input) ? result.input : task.input_json;
  return {
    customer_issue: normalizeOptionalString(source.customer_issue),
    product_area: normalizeOptionalString(source.product_area),
    severity: normalizeOptionalString(source.severity) as SupportSeverity | undefined,
    desired_outcome: normalizeOptionalString(source.desired_outcome),
    reproduction_steps: normalizeStringList(source.reproduction_steps),
  };
}

function parseEntryTaskTypes(workspace: Workspace | null): SupportTaskType[] {
  const entryTaskTypes = workspace?.module_config_json.entry_task_types;
  if (!Array.isArray(entryTaskTypes)) {
    return ["ticket_summary", "reply_draft"];
  }

  const supported = entryTaskTypes.filter(
    (entryTaskType): entryTaskType is SupportTaskType =>
      entryTaskType === "ticket_summary" || entryTaskType === "reply_draft",
  );
  return supported.length > 0 ? supported : ["ticket_summary", "reply_draft"];
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

function renderEvidenceStatusBadge(evidenceStatus: SupportEvidenceStatus) {
  const styles: Record<SupportEvidenceStatus, { label: string; color: string }> = {
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

function renderArtifactStats(artifacts: SupportArtifacts) {
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
      <div>
        <strong>Evidence status:</strong> {renderEvidenceStatusBadge(artifacts.evidence_status)}
      </div>
    </div>
  );
}

function extractCustomerIssue(task: TaskRecord, result: SupportTaskResult | null = null): string | null {
  const input = parseSupportTaskInput(task, result);
  return input.customer_issue && input.customer_issue.length > 0 ? input.customer_issue : null;
}

function formatIssueSnapshot(input: SupportTaskInput): string {
  const segments: string[] = [];
  if (input.product_area) {
    segments.push(input.product_area);
  }
  if (input.severity) {
    segments.push(`Severity ${input.severity}`);
  }
  if (input.desired_outcome) {
    segments.push(`Outcome: ${input.desired_outcome}`);
  }
  return segments.join(" | ");
}

function parseReproductionSteps(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((step) => step.trim())
    .filter((step, index, allSteps) => step.length > 0 && allSteps.indexOf(step) === index);
}

function formatReproductionSteps(steps: string[]): string {
  return steps.join("\n");
}

function renderListSection<T extends string>({
  title,
  items,
  emptyText,
}: {
  title: string;
  items: T[];
  emptyText: string;
}) {
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

function renderFindings(findings: SupportFinding[]) {
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
        <p>No grounded findings were produced for this case.</p>
      )}
    </div>
  );
}

function renderCaseBrief(caseBrief: SupportCaseBrief) {
  return (
    <div
      style={{
        border: "1px solid #cbd5e1",
        borderRadius: 12,
        padding: 16,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
        <strong>Case brief</strong>
        {renderEvidenceStatusBadge(caseBrief.evidence_status)}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>Issue summary:</strong> {caseBrief.issue_summary}
        </div>
        {caseBrief.product_area ? (
          <div>
            <strong>Product area:</strong> {caseBrief.product_area}
          </div>
        ) : null}
        {caseBrief.severity ? (
          <div>
            <strong>Severity:</strong> {caseBrief.severity}
          </div>
        ) : null}
        {caseBrief.desired_outcome ? (
          <div>
            <strong>Desired outcome:</strong> {caseBrief.desired_outcome}
          </div>
        ) : null}
        <div>
          <strong>Reproduction steps:</strong>
          {caseBrief.reproduction_steps.length > 0 ? (
            <ol style={{ marginBottom: 0, marginTop: 8, paddingLeft: 20 }}>
              {caseBrief.reproduction_steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          ) : (
            <p style={{ marginBottom: 0, marginTop: 8 }}>No reproduction steps were captured for this task.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function renderReplyDraft(replyDraft: SupportReplyDraft | undefined) {
  if (!replyDraft) {
    return null;
  }

  return (
    <div
      style={{
        border: "1px solid #cbd5e1",
        borderRadius: 12,
        padding: 16,
      }}
    >
      <strong>Reply draft</strong>
      <div style={{ marginTop: 12 }}>
        <div>
          <strong>Subject:</strong> {replyDraft.subject_line}
        </div>
        <p style={{ marginBottom: 12, marginTop: 12, whiteSpace: "pre-wrap" }}>{replyDraft.body}</p>
        <div style={{ color: "#475569" }}>
          <strong>Confidence note:</strong> {replyDraft.confidence_note}
        </div>
      </div>
    </div>
  );
}

export default function SupportCopilotPanel({ workspaceId }: SupportCopilotPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<SupportTaskType>("ticket_summary");
  const [customerIssue, setCustomerIssue] = useState("");
  const [productArea, setProductArea] = useState("");
  const [severity, setSeverity] = useState<"" | SupportSeverity>("");
  const [desiredOutcome, setDesiredOutcome] = useState("");
  const [reproductionStepsText, setReproductionStepsText] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const availableTaskTypes = useMemo(() => parseEntryTaskTypes(workspace), [workspace]);

  useEffect(() => {
    if (!availableTaskTypes.includes(taskType)) {
      setTaskType(availableTaskTypes[0] ?? "ticket_summary");
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
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load support tasks");
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
    () => (selectedTask ? parseSupportTaskResult(selectedTask) : null),
    [selectedTask],
  );
  const selectedInput = useMemo(
    () => (selectedTask ? parseSupportTaskInput(selectedTask, selectedResult) : null),
    [selectedResult, selectedTask],
  );

  const handleCreateTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      return;
    }

    const reproductionSteps = parseReproductionSteps(reproductionStepsText);
    const input: JsonObject = {};
    const normalizedIssue = customerIssue.trim();
    const normalizedProductArea = productArea.trim();
    const normalizedDesiredOutcome = desiredOutcome.trim();

    if (normalizedIssue) {
      input.customer_issue = normalizedIssue;
    }
    if (normalizedProductArea) {
      input.product_area = normalizedProductArea;
    }
    if (severity) {
      input.severity = severity;
    }
    if (normalizedDesiredOutcome) {
      input.desired_outcome = normalizedDesiredOutcome;
    }
    if (reproductionSteps.length > 0) {
      input.reproduction_steps = reproductionSteps;
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
      setCustomerIssue("");
      setProductArea("");
      setSeverity("");
      setDesiredOutcome("");
      setReproductionStepsText("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to launch support task");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Support Copilot">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to run support tasks and inspect grounded outputs." />;
  }

  return (
    <>
      <SectionCard
        title="Support Copilot"
        description="Launch grounded support case workflows, inspect evidence quality, and decide whether a case can stay frontline or needs escalation."
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
                : "knowledge_base, reply_drafts, tasks, evals"}
            </div>
          </div>
        ) : null}
        {workspace?.module_type && workspace.module_type !== "support" ? (
          <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 12 }}>
            This surface is only available for support workspaces. Current module: {workspace.module_type}.
          </p>
        ) : null}
      </SectionCard>

      <SectionCard
        title="Launch support case"
        description="Capture the case, decide how much context you already know, and run a grounded support task against the current workspace knowledge base."
      >
        <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12, maxWidth: 760 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Task type</span>
            <select
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
              onChange={(event) => setTaskType(event.target.value as SupportTaskType)}
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
            <span>Customer issue</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
              onChange={(event) => setCustomerIssue(event.target.value)}
              placeholder={TASK_OPTIONS[taskType].placeholder}
              rows={4}
              value={customerIssue}
            />
          </label>

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span>Product area</span>
              <input
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
                onChange={(event) => setProductArea(event.target.value)}
                placeholder="Auth, billing, admin console..."
                type="text"
                value={productArea}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>Severity</span>
              <select
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
                onChange={(event) => setSeverity(event.target.value as "" | SupportSeverity)}
                value={severity}
              >
                {SEVERITY_OPTIONS.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label style={{ display: "grid", gap: 6 }}>
            <span>Desired outcome</span>
            <input
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
              onChange={(event) => setDesiredOutcome(event.target.value)}
              placeholder="Example: restore login access without forcing a full account recovery."
              type="text"
              value={desiredOutcome}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span>Reproduction steps</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
              onChange={(event) => setReproductionStepsText(event.target.value)}
              placeholder={"One step per line\n1. Open reset email\n2. Click link\n3. Expired page appears"}
              rows={5}
              value={reproductionStepsText}
            />
          </label>

          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button
            disabled={
              isCreating || (workspace?.module_type !== undefined && workspace.module_type !== "support")
            }
            type="submit"
          >
            {isCreating ? "Launching..." : "Launch support task"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Support runs"
        description="Tasks refresh automatically every 2 seconds so you can watch case analysis settle into a grounded triage decision."
      >
        {isLoadingTasks ? <p>Loading support tasks...</p> : null}
        {!isLoadingTasks && tasks.length === 0 ? <p>No support tasks yet. Launch one to generate a structured case workflow.</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {tasks.map((task) => {
            const result = parseSupportTaskResult(task);
            const input = parseSupportTaskInput(task, result);
            const issueSnapshot = formatIssueSnapshot(input);

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
                  <strong>{TASK_OPTIONS[task.task_type as SupportTaskType]?.label ?? task.task_type}</strong>
                  {renderStatus(task.status)}
                  {result ? renderEvidenceStatusBadge(result.artifacts.evidence_status) : null}
                </div>
                <div style={{ color: "#475569", marginBottom: 6 }}>
                  {result?.summary ?? extractCustomerIssue(task, result) ?? "No customer issue provided."}
                </div>
                {issueSnapshot ? (
                  <div style={{ color: "#64748b", fontSize: 14, marginBottom: 6 }}>{issueSnapshot}</div>
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
        title="Structured case result"
        description="Inspect the case brief, grounded findings, triage decision, and customer-ready reply generated for the selected support task."
      >
        {!selectedTask ? <p>Select a support task to inspect its output.</p> : null}
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
                <strong>Task type:</strong> {TASK_OPTIONS[selectedTask.task_type as SupportTaskType]?.label ?? selectedTask.task_type}
              </div>
              {selectedInput?.customer_issue ? (
                <div>
                  <strong>Customer issue:</strong> {selectedInput.customer_issue}
                </div>
              ) : null}
            </div>

            {selectedTask.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>Support error</strong>
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
                {renderCaseBrief(selectedResult.case_brief)}

                <div
                  style={{
                    border: "1px solid #cbd5e1",
                    borderRadius: 12,
                    padding: 16,
                  }}
                >
                  <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
                    <strong>Triage decision</strong>
                    {renderEvidenceStatusBadge(selectedResult.triage.evidence_status)}
                  </div>
                  <div style={{ display: "grid", gap: 8 }}>
                    <div>
                      <strong>Recommended owner:</strong> {selectedResult.triage.recommended_owner}
                    </div>
                    <div>
                      <strong>Manual review required:</strong> {selectedResult.triage.needs_manual_review ? "Yes" : "No"}
                    </div>
                    <div>
                      <strong>Escalate:</strong> {selectedResult.triage.should_escalate ? "Yes" : "No"}
                    </div>
                    <div>
                      <strong>Rationale:</strong> {selectedResult.triage.rationale}
                    </div>
                  </div>
                </div>

                {renderFindings(selectedResult.findings)}
                {renderReplyDraft(selectedResult.reply_draft)}

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
                              <Link href={`/workspaces/${workspaceId}/documents`}>Open knowledge base context</Link>
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No linked evidence was returned. This usually means the workspace had limited indexed support context.</p>
                  )}
                </div>
              </>
            ) : (
              <p>
                This task does not have a completed structured support payload yet. If it is still running,
                wait for the next refresh cycle.
              </p>
            )}
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}
