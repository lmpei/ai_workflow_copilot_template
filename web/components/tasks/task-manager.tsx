// Legacy research-only task manager. This component is not on the live route path and still reflects the older freeform-goal Research surface.
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createWorkspaceTask,
  getTask,
  isApiClientError,
  listWorkspaceTasks,
} from "../../lib/api";
import type { JsonObject, TaskRecord, TaskType } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type TaskManagerProps = {
  workspaceId: string;
};

const TASK_OPTIONS: Array<{
  type: TaskType;
  label: string;
  description: string;
}> = [
  {
    type: "research_summary",
    label: "Research Summary",
    description: "Run the workspace research agent and summarize the most relevant findings.",
  },
  {
    type: "workspace_report",
    label: "Workspace Report",
    description: "Build a concise report for the current workspace, even with limited context.",
  },
];

const ACTIVE_STATUSES = new Set<TaskRecord["status"]>(["pending", "running"]);

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

function extractSummary(task: TaskRecord): string | null {
  const result = task.output_json.result;
  if (!result || typeof result !== "object") {
    return null;
  }

  const summary = (result as JsonObject).summary;
  return typeof summary === "string" && summary.length > 0 ? summary : null;
}

export default function LegacyTaskManager({ workspaceId }: TaskManagerProps) {
  const { session, isReady } = useAuthSession();
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<TaskType>("research_summary");
  const [goal, setGoal] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isRefreshingTask, setIsRefreshingTask] = useState(false);

  const loadTasks = useCallback(
    async (silent = false) => {
      if (!session) {
        setTasks([]);
        setSelectedTaskId(null);
        return;
      }

      if (!silent) {
        setIsLoading(true);
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
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load tasks");
      } finally {
        if (!silent) {
          setIsLoading(false);
        }
      }
    },
    [session, workspaceId],
  );

  const refreshTask = useCallback(
    async (taskId: string) => {
      if (!session) {
        return;
      }

      setIsRefreshingTask(true);
      setErrorMessage(null);

      try {
        const refreshedTask = await getTask(session.accessToken, taskId);
        setTasks((currentTasks) => {
          const updatedTasks = currentTasks.some((task) => task.id === refreshedTask.id)
            ? currentTasks.map((task) => (task.id === refreshedTask.id ? refreshedTask : task))
            : [refreshedTask, ...currentTasks];
          return sortTasks(updatedTasks);
        });
        setSelectedTaskId(refreshedTask.id);
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to refresh task");
      } finally {
        setIsRefreshingTask(false);
      }
    },
    [session],
  );

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

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

  const handleCreateTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      return;
    }

    setIsCreating(true);
    setErrorMessage(null);

    try {
      const createdTask = await createWorkspaceTask(session.accessToken, workspaceId, {
        task_type: taskType,
        input: goal.trim().length > 0 ? { goal: goal.trim() } : {},
      });
      setTasks((currentTasks) => sortTasks([createdTask, ...currentTasks]));
      setSelectedTaskId(createdTask.id);
      setGoal("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to create task");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Tasks">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to create and inspect workspace tasks." />;
  }

  return (
    <>
      <SectionCard
        title="Legacy task form"
        description={`Workspace: ${workspaceId}. This legacy component is not on the live route path and still reflects the older Research-only task flow.`}
      >
        <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12, maxWidth: 640 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Task type</span>
            <select
              onChange={(event) => setTaskType(event.target.value as TaskType)}
              value={taskType}
            >
              {TASK_OPTIONS.map((option) => (
                <option key={option.type} value={option.type}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <p style={{ color: "#475569", margin: 0 }}>
            {TASK_OPTIONS.find((option) => option.type === taskType)?.description}
          </p>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Goal</span>
            <textarea
              onChange={(event) => setGoal(event.target.value)}
              placeholder="Optional. Leave blank to use the default goal for this task type."
              rows={4}
              value={goal}
            />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isCreating} type="submit">
            {isCreating ? "Creating..." : "Create task"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Task list" description="Tasks are polled automatically every 2 seconds.">
        {isLoading ? <p>Loading tasks...</p> : null}
        {!isLoading && tasks.length === 0 ? <p>No tasks created yet.</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {tasks.map((task) => (
            <li
              key={task.id}
              style={{
                border: task.id === selectedTaskId ? "1px solid #0f172a" : "1px solid #cbd5e1",
                borderRadius: 12,
                marginBottom: 12,
                padding: 12,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 10, marginBottom: 6 }}>
                <strong>{task.task_type}</strong>
                {renderStatus(task.status)}
              </div>
              <div>Task ID: {task.id}</div>
              <div>Updated: {new Date(task.updated_at).toLocaleString()}</div>
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button onClick={() => void refreshTask(task.id)} type="button">
                  {isRefreshingTask && task.id === selectedTaskId ? "Refreshing..." : "Open"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="Task detail" description="Inspect the latest task status, result, and errors.">
        {!selectedTask ? <p>Select a task to inspect its output.</p> : null}
        {selectedTask ? (
          <div style={{ display: "grid", gap: 12 }}>
            <div>
              <strong>Task ID:</strong> {selectedTask.id}
            </div>
            <div>
              <strong>Status:</strong> {renderStatus(selectedTask.status)}
            </div>
            <div>
              <strong>Created:</strong> {new Date(selectedTask.created_at).toLocaleString()}
            </div>
            <div>
              <strong>Updated:</strong> {new Date(selectedTask.updated_at).toLocaleString()}
            </div>
            <div>
              <strong>Input:</strong>
              <pre style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
                {JSON.stringify(selectedTask.input_json, null, 2)}
              </pre>
            </div>
            {extractSummary(selectedTask) ? (
              <div>
                <strong>Summary:</strong>
                <p style={{ marginTop: 8 }}>{extractSummary(selectedTask)}</p>
              </div>
            ) : null}
            {selectedTask.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>Error:</strong>
                <p style={{ color: "#b91c1c", marginTop: 8 }}>{selectedTask.error_message}</p>
              </div>
            ) : null}
            <div>
              <strong>Output JSON:</strong>
              <pre style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
                {JSON.stringify(selectedTask.output_json, null, 2)}
              </pre>
            </div>
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}
