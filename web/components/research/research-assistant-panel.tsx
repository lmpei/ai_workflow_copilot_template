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
  ResearchArtifacts,
  ResearchDeliverable,
  ResearchRequestedSection,
  ResearchResultSections,
  ResearchTaskInput,
  ResearchTaskResult,
  ResearchTaskType,
  TaskRecord,
  Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type ResearchAssistantPanelProps = {
  workspaceId: string;
};

const TASK_OPTIONS: Record<
  ResearchTaskType,
  {
    label: string;
    description: string;
    placeholder: string;
  }
> = {
  research_summary: {
    label: "Research Summary",
    description: "Summarize the most relevant indexed findings for a focused question or goal.",
    placeholder: "Optional. Example: Summarize the strongest findings about Project Apollo.",
  },
  workspace_report: {
    label: "Workspace Report",
    description: "Produce a broader report from the currently indexed workspace context.",
    placeholder: "Optional. Example: Build a concise report on the current workspace knowledge base.",
  },
};

const DEFAULT_REQUESTED_SECTIONS: Record<ResearchTaskType, ResearchRequestedSection[]> = {
  research_summary: ["summary", "findings", "evidence", "next_steps"],
  workspace_report: ["summary", "findings", "evidence", "open_questions", "next_steps"],
};

const REQUESTED_SECTION_OPTIONS: Array<{ value: ResearchRequestedSection; label: string }> = [
  { value: "summary", label: "Summary" },
  { value: "findings", label: "Findings" },
  { value: "evidence", label: "Evidence" },
  { value: "open_questions", label: "Open questions" },
  { value: "next_steps", label: "Next steps" },
];

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string" && item.length > 0);
}

function splitLines(value: string): string[] {
  const seen = new Set<string>();
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter((item) => {
      if (!item || seen.has(item)) {
        return false;
      }
      seen.add(item);
      return true;
    });
}

function parseResearchTaskInput(value: unknown): ResearchTaskInput {
  if (!isJsonObject(value)) {
    return {
      focus_areas: [],
      key_questions: [],
      constraints: [],
      requested_sections: [],
    };
  }

  const deliverable = value.deliverable === "brief" || value.deliverable === "report" ? value.deliverable : undefined;
  const goal = typeof value.goal === "string" && value.goal.length > 0 ? value.goal : undefined;

  return {
    goal,
    focus_areas: parseStringArray(value.focus_areas),
    key_questions: parseStringArray(value.key_questions),
    constraints: parseStringArray(value.constraints),
    deliverable,
    requested_sections: parseStringArray(value.requested_sections).filter(
      (item): item is ResearchRequestedSection =>
        item === "summary" ||
        item === "findings" ||
        item === "evidence" ||
        item === "open_questions" ||
        item === "next_steps",
    ),
  };
}

function parseResearchSections(value: unknown, result: JsonObject): ResearchResultSections {
  if (!isJsonObject(value)) {
    return {
      summary: typeof result.summary === "string" ? result.summary : "",
      findings: Array.isArray(result.highlights)
        ? result.highlights
            .filter((highlight): highlight is string => typeof highlight === "string")
            .map((highlight, index) => ({
              title: `Finding ${index + 1}`,
              summary: highlight,
              evidence_ref_ids: [],
            }))
        : [],
      evidence_overview: [],
      open_questions: [],
      next_steps: [],
    };
  }

  const findings = Array.isArray(value.findings)
    ? value.findings
        .filter((finding): finding is JsonObject => isJsonObject(finding))
        .map((finding, index) => ({
          title: typeof finding.title === "string" ? finding.title : `Finding ${index + 1}`,
          summary: typeof finding.summary === "string" ? finding.summary : "",
          evidence_ref_ids: parseStringArray(finding.evidence_ref_ids),
        }))
    : [];

  return {
    summary: typeof value.summary === "string" ? value.summary : typeof result.summary === "string" ? result.summary : "",
    findings,
    evidence_overview: parseStringArray(value.evidence_overview),
    open_questions: parseStringArray(value.open_questions),
    next_steps: parseStringArray(value.next_steps),
  };
}

function parseResearchTaskResult(task: TaskRecord): ResearchTaskResult | null {
  const result = task.output_json.result;
  if (!isJsonObject(result)) {
    return null;
  }

  if (
    result.module_type !== "research" ||
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

  return {
    ...(result as unknown as ResearchTaskResult),
    input: parseResearchTaskInput(result.input),
    sections: parseResearchSections(result.sections, result),
  };
}

function parseEntryTaskTypes(workspace: Workspace | null): ResearchTaskType[] {
  const entryTaskTypes = workspace?.module_config_json.entry_task_types;
  if (!Array.isArray(entryTaskTypes)) {
    return ["research_summary", "workspace_report"];
  }

  const supported = entryTaskTypes.filter(
    (entryTaskType): entryTaskType is ResearchTaskType =>
      entryTaskType === "research_summary" || entryTaskType === "workspace_report",
  );
  return supported.length > 0 ? supported : ["research_summary", "workspace_report"];
}

function sortTasks(tasks: TaskRecord[]): TaskRecord[] {
  return [...tasks].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

function renderStatus(status: TaskRecord["status"]) {
  const statusStyles: Record<TaskRecord["status"], { label: string; color: string }> = {
    pending: { label: "pending", color: "#92400e" },
    running: { label: "running", color: "#1d4ed8" },
    done: { label: "done", color: "#15803d" },
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

function renderArtifactStats(artifacts: ResearchArtifacts) {
  const cards = [
    { label: "Documents", value: artifacts.document_count },
    { label: "Matches", value: artifacts.match_count },
    { label: "Tool calls", value: artifacts.tool_call_ids.length },
  ];

  return (
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
  );
}

function extractGoal(task: TaskRecord, result: ResearchTaskResult | null): string | null {
  if (result?.input.goal) {
    return result.input.goal;
  }

  const input = parseResearchTaskInput(task.input_json);
  return input.goal ?? null;
}

function renderStringList(items: string[], emptyText: string) {
  if (items.length === 0) {
    return <p>{emptyText}</p>;
  }

  return (
    <ul>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export default function ResearchAssistantPanel({ workspaceId }: ResearchAssistantPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<ResearchTaskType>("research_summary");
  const [goal, setGoal] = useState("");
  const [focusAreasText, setFocusAreasText] = useState("");
  const [keyQuestionsText, setKeyQuestionsText] = useState("");
  const [constraintsText, setConstraintsText] = useState("");
  const [deliverable, setDeliverable] = useState<ResearchDeliverable | "">("");
  const [requestedSections, setRequestedSections] = useState<ResearchRequestedSection[]>(
    DEFAULT_REQUESTED_SECTIONS.research_summary,
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const availableTaskTypes = useMemo(() => parseEntryTaskTypes(workspace), [workspace]);

  useEffect(() => {
    if (!availableTaskTypes.includes(taskType)) {
      setTaskType(availableTaskTypes[0] ?? "research_summary");
    }
  }, [availableTaskTypes, taskType]);

  useEffect(() => {
    setRequestedSections(DEFAULT_REQUESTED_SECTIONS[taskType]);
    setDeliverable(taskType === "workspace_report" ? "report" : "brief");
  }, [taskType]);

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
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load research tasks");
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
    () => (selectedTask ? parseResearchTaskResult(selectedTask) : null),
    [selectedTask],
  );

  const toggleRequestedSection = (section: ResearchRequestedSection) => {
    setRequestedSections((currentSections) => {
      if (currentSections.includes(section)) {
        return currentSections.filter((item) => item !== section);
      }
      return [...currentSections, section];
    });
  };

  const handleCreateTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      return;
    }

    setIsCreating(true);
    setErrorMessage(null);

    const payloadInput: JsonObject = {};
    const trimmedGoal = goal.trim();
    if (trimmedGoal.length > 0) {
      payloadInput.goal = trimmedGoal;
    }

    const focusAreas = splitLines(focusAreasText);
    if (focusAreas.length > 0) {
      payloadInput.focus_areas = focusAreas;
    }

    const keyQuestions = splitLines(keyQuestionsText);
    if (keyQuestions.length > 0) {
      payloadInput.key_questions = keyQuestions;
    }

    const constraints = splitLines(constraintsText);
    if (constraints.length > 0) {
      payloadInput.constraints = constraints;
    }

    if (deliverable) {
      payloadInput.deliverable = deliverable;
    }

    if (requestedSections.length > 0) {
      payloadInput.requested_sections = requestedSections;
    }

    try {
      const createdTask = await createWorkspaceTask(session.accessToken, workspaceId, {
        task_type: taskType,
        input: payloadInput,
      });
      setTasks((currentTasks) => sortTasks([createdTask, ...currentTasks]));
      setSelectedTaskId(createdTask.id);
      setGoal("");
      setFocusAreasText("");
      setKeyQuestionsText("");
      setConstraintsText("");
      setRequestedSections(DEFAULT_REQUESTED_SECTIONS[taskType]);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to launch research task");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Research Assistant">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to run research tasks and inspect structured findings." />;
  }

  return (
    <>
      <SectionCard
        title="Research Assistant"
        description="Launch research tasks, inspect structured findings, and follow linked evidence back to workspace documents."
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
                : "documents, grounded_chat, tasks, evals"}
            </div>
          </div>
        ) : null}
        {workspace?.module_type && workspace.module_type !== "research" ? (
          <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 12 }}>
            This surface is only available for research workspaces. Current module: {workspace.module_type}.
          </p>
        ) : null}
      </SectionCard>

      <SectionCard
        title="Launch research task"
        description="Define the research goal, scope, and output expectations for a structured Stage A research run."
      >
        <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12, maxWidth: 720 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Task type</span>
            <select
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
              onChange={(event) => setTaskType(event.target.value as ResearchTaskType)}
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
            <span>Research goal</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
              onChange={(event) => setGoal(event.target.value)}
              placeholder={TASK_OPTIONS[taskType].placeholder}
              rows={4}
              value={goal}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Focus areas</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
              onChange={(event) => setFocusAreasText(event.target.value)}
              placeholder="Optional. One focus area per line. Example: Risks, timeline, stakeholder concerns."
              rows={3}
              value={focusAreasText}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Key questions</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
              onChange={(event) => setKeyQuestionsText(event.target.value)}
              placeholder="Optional. One question per line. Example: What evidence supports the deadline risk?"
              rows={3}
              value={keyQuestionsText}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Constraints</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
              onChange={(event) => setConstraintsText(event.target.value)}
              placeholder="Optional. One constraint per line. Example: Use only indexed workspace documents."
              rows={3}
              value={constraintsText}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Deliverable</span>
            <select
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
              onChange={(event) => setDeliverable(event.target.value as ResearchDeliverable | "")}
              value={deliverable}
            >
              <option value="">Use task default</option>
              <option value="brief">Brief</option>
              <option value="report">Report</option>
            </select>
          </label>
          <fieldset
            style={{
              border: "1px solid #cbd5e1",
              borderRadius: 12,
              display: "grid",
              gap: 10,
              padding: 12,
            }}
          >
            <legend>Requested sections</legend>
            {REQUESTED_SECTION_OPTIONS.map((option) => (
              <label key={option.value} style={{ alignItems: "center", display: "flex", gap: 8 }}>
                <input
                  checked={requestedSections.includes(option.value)}
                  disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
                  onChange={() => toggleRequestedSection(option.value)}
                  type="checkbox"
                />
                <span>{option.label}</span>
              </label>
            ))}
          </fieldset>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button
            disabled={isCreating || (workspace?.module_type !== undefined && workspace.module_type !== "research")}
            type="submit"
          >
            {isCreating ? "Launching..." : "Launch research task"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Research runs"
        description="Tasks are refreshed automatically every 2 seconds so you can watch pending and running work settle into final results."
      >
        {isLoadingTasks ? <p>Loading research tasks...</p> : null}
        {!isLoadingTasks && tasks.length === 0 ? <p>No research tasks yet. Launch one to generate a structured result.</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {tasks.map((task) => {
            const result = parseResearchTaskResult(task);
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
                  <strong>{TASK_OPTIONS[task.task_type as ResearchTaskType].label}</strong>
                  {renderStatus(task.status)}
                </div>
                <div style={{ color: "#475569", marginBottom: 6 }}>
                  {result?.summary ?? extractGoal(task, result) ?? "No custom goal provided."}
                </div>
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
        title="Structured result"
        description="Inspect the research output, input contract, evidence trail, and source artifacts from the selected task."
      >
        {!selectedTask ? <p>Select a research task to inspect its output.</p> : null}
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
                <strong>Task type:</strong> {TASK_OPTIONS[selectedTask.task_type as ResearchTaskType].label}
              </div>
              {extractGoal(selectedTask, selectedResult) ? (
                <div>
                  <strong>Goal:</strong> {extractGoal(selectedTask, selectedResult)}
                </div>
              ) : null}
            </div>

            {selectedTask.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>Research error</strong>
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

                <div style={{ display: "grid", gap: 6 }}>
                  <strong>Structured input</strong>
                  <div>
                    <strong>Deliverable:</strong> {selectedResult.input.deliverable ?? "not specified"}
                  </div>
                  <div>
                    <strong>Requested sections:</strong>{" "}
                    {selectedResult.input.requested_sections.length > 0
                      ? selectedResult.input.requested_sections.join(", ")
                      : "task default"}
                  </div>
                  <div>
                    <strong>Focus areas</strong>
                    {renderStringList(selectedResult.input.focus_areas, "No focus areas were provided.")}
                  </div>
                  <div>
                    <strong>Key questions</strong>
                    {renderStringList(selectedResult.input.key_questions, "No key questions were provided.")}
                  </div>
                  <div>
                    <strong>Constraints</strong>
                    {renderStringList(selectedResult.input.constraints, "No explicit constraints were provided.")}
                  </div>
                </div>

                <div>
                  <strong>Section summary</strong>
                  <p style={{ marginBottom: 0, marginTop: 8 }}>{selectedResult.sections.summary}</p>
                </div>

                <div>
                  <strong>Key findings</strong>
                  {selectedResult.sections.findings.length > 0 ? (
                    <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
                      {selectedResult.sections.findings.map((finding) => (
                        <li
                          key={`${finding.title}-${finding.summary}`}
                          style={{
                            border: "1px solid #cbd5e1",
                            borderRadius: 12,
                            padding: 12,
                          }}
                        >
                          <div style={{ fontWeight: 600 }}>{finding.title}</div>
                          <p style={{ marginBottom: 0, marginTop: 8 }}>{finding.summary}</p>
                          {finding.evidence_ref_ids.length > 0 ? (
                            <div style={{ color: "#475569", fontSize: 14, marginTop: 8 }}>
                              Evidence refs: {finding.evidence_ref_ids.join(", ")}
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No structured findings were produced for this run.</p>
                  )}
                </div>

                <div>
                  <strong>Evidence overview</strong>
                  {renderStringList(
                    selectedResult.sections.evidence_overview,
                    "No evidence overview items were produced for this run.",
                  )}
                </div>

                <div>
                  <strong>Open questions</strong>
                  {renderStringList(selectedResult.sections.open_questions, "No open questions were recorded.")}
                </div>

                <div>
                  <strong>Next steps</strong>
                  {renderStringList(selectedResult.sections.next_steps, "No next steps were suggested.")}
                </div>

                <div>
                  <strong>Highlight bullets</strong>
                  {selectedResult.highlights.length > 0 ? (
                    <ul>
                      {selectedResult.highlights.map((highlight) => (
                        <li key={highlight}>{highlight}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No highlight bullets were produced for this run.</p>
                  )}
                </div>

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
                              <Link href={`/workspaces/${workspaceId}/documents`}>Open document context</Link>
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No linked evidence was returned. This usually means the workspace had limited indexed context.</p>
                  )}
                </div>

                <div>
                  <strong>Matched chunks</strong>
                  {selectedResult.artifacts.matches.length > 0 ? (
                    <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
                      {selectedResult.artifacts.matches.map((match) => (
                        <li
                          key={match.chunk_id}
                          style={{
                            border: "1px solid #cbd5e1",
                            borderRadius: 12,
                            padding: 12,
                          }}
                        >
                          <div style={{ fontWeight: 600 }}>{match.document_title}</div>
                          <div style={{ color: "#475569", fontSize: 14, marginTop: 4 }}>Chunk {match.chunk_index}</div>
                          <p style={{ marginBottom: 0, marginTop: 8 }}>{match.snippet}</p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No matched chunks were found for this run.</p>
                  )}
                </div>

                <div>
                  <strong>Workspace documents considered</strong>
                  {selectedResult.artifacts.documents.length > 0 ? (
                    <ul>
                      {selectedResult.artifacts.documents.map((document) => (
                        <li key={document.id}>
                          {document.title} - {document.status} ({document.source_type})
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No workspace documents were available when this task ran.</p>
                  )}
                </div>
              </>
            ) : (
              <p>
                This task does not have a completed structured research payload yet. If it is still running, wait for the
                next refresh cycle.
              </p>
            )}
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}
