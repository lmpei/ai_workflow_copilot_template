"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createEvalDataset,
  createEvalRun,
  getEvalRun,
  isApiClientError,
  listEvalDatasets,
  listEvalRunResults,
} from "../../lib/api";
import type {
  EvalCaseRecord,
  EvalDatasetRecord,
  EvalResultRecord,
  EvalRunRecord,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import SectionCard from "../ui/section-card";

type EvalManagerProps = {
  workspaceId: string;
};

const ACTIVE_RUN_STATUSES = new Set<EvalRunRecord["status"]>(["pending", "running"]);
const STORAGE_KEY_PREFIX = "ai_workflow_eval_runs:";

function getStorageKey(workspaceId: string) {
  return `${STORAGE_KEY_PREFIX}${workspaceId}`;
}

function readStoredRunIds(workspaceId: string): string[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const rawValue = window.localStorage.getItem(getStorageKey(workspaceId));
    if (!rawValue) {
      return [];
    }

    const parsedValue = JSON.parse(rawValue);
    if (!Array.isArray(parsedValue)) {
      return [];
    }

    return parsedValue.filter((item): item is string => typeof item === "string");
  } catch {
    return [];
  }
}

function writeStoredRunIds(workspaceId: string, runIds: string[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(getStorageKey(workspaceId), JSON.stringify(runIds));
}

function sortDatasets(datasets: EvalDatasetRecord[]): EvalDatasetRecord[] {
  return [...datasets].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

function sortRuns(runs: EvalRunRecord[]): EvalRunRecord[] {
  return [...runs].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

function renderRunStatus(status: EvalRunRecord["status"]) {
  const statusStyles: Record<EvalRunRecord["status"], { label: string; color: string }> = {
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

function renderResultStatus(status: EvalResultRecord["status"]) {
  const color = status === "completed" ? "#15803d" : status === "failed" ? "#b91c1c" : "#1d4ed8";
  return (
    <span style={{ color, fontWeight: 600, textTransform: "uppercase" }}>
      {status}
    </span>
  );
}

function getSummaryMetric(summaryJson: Record<string, unknown>, key: string): string {
  const value = summaryJson[key];
  return typeof value === "number" || typeof value === "string" ? String(value) : "0";
}

function getQuestion(evalCase: EvalCaseRecord | undefined): string | null {
  if (!evalCase) {
    return null;
  }

  const question = evalCase.input_json.question;
  return typeof question === "string" && question.length > 0 ? question : null;
}

export default function EvalManager({ workspaceId }: EvalManagerProps) {
  const { session, isReady } = useAuthSession();
  const [datasets, setDatasets] = useState<EvalDatasetRecord[]>([]);
  const [runs, setRuns] = useState<EvalRunRecord[]>([]);
  const [resultsByRunId, setResultsByRunId] = useState<Record<string, EvalResultRecord[]>>({});
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const [datasetDescription, setDatasetDescription] = useState("");
  const [datasetQuestions, setDatasetQuestions] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingDataset, setIsCreatingDataset] = useState(false);
  const [isCreatingRunId, setIsCreatingRunId] = useState<string | null>(null);

  const loadDatasets = useCallback(async () => {
    if (!session) {
      setDatasets([]);
      return;
    }

    setIsLoading(true);
    try {
      const loadedDatasets = await listEvalDatasets(session.accessToken, workspaceId);
      setDatasets(sortDatasets(loadedDatasets));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load eval datasets");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  const loadRunResults = useCallback(
    async (runId: string) => {
      if (!session) {
        return;
      }

      try {
        const results = await listEvalRunResults(session.accessToken, runId);
        setResultsByRunId((currentResultsByRunId) => ({
          ...currentResultsByRunId,
          [runId]: results,
        }));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load eval results");
      }
    },
    [session],
  );

  const refreshRun = useCallback(
    async (runId: string) => {
      if (!session) {
        return;
      }

      try {
        const refreshedRun = await getEvalRun(session.accessToken, runId);
        setRuns((currentRuns) => {
          const nextRuns = currentRuns.some((run) => run.id === refreshedRun.id)
            ? currentRuns.map((run) => (run.id === refreshedRun.id ? refreshedRun : run))
            : [refreshedRun, ...currentRuns];
          return sortRuns(nextRuns);
        });
        setSelectedRunId(refreshedRun.id);
        if (!ACTIVE_RUN_STATUSES.has(refreshedRun.status)) {
          await loadRunResults(refreshedRun.id);
        }
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to refresh eval run");
      }
    },
    [loadRunResults, session],
  );

  const loadStoredRuns = useCallback(async () => {
    if (!session) {
      setRuns([]);
      setSelectedRunId(null);
      setResultsByRunId({});
      return;
    }

    const storedRunIds = readStoredRunIds(workspaceId);
    if (storedRunIds.length === 0) {
      setRuns([]);
      setSelectedRunId(null);
      setResultsByRunId({});
      return;
    }

    const loadedRuns = await Promise.all(
      storedRunIds.map(async (runId) => {
        try {
          return await getEvalRun(session.accessToken, runId);
        } catch {
          return null;
        }
      }),
    );
    const nextRuns = sortRuns(loadedRuns.filter((run): run is EvalRunRecord => run !== null));
    setRuns(nextRuns);
    setSelectedRunId((currentSelectedRunId) => currentSelectedRunId ?? nextRuns[0]?.id ?? null);

    await Promise.all(
      nextRuns
        .filter((run) => !ACTIVE_RUN_STATUSES.has(run.status))
        .map(async (run) => loadRunResults(run.id)),
    );

    writeStoredRunIds(
      workspaceId,
      nextRuns.map((run) => run.id),
    );
  }, [loadRunResults, session, workspaceId]);

  useEffect(() => {
    void loadDatasets();
    void loadStoredRuns();
  }, [loadDatasets, loadStoredRuns]);

  useEffect(() => {
    if (!session) {
      return undefined;
    }

    const activeRunIds = runs.filter((run) => ACTIVE_RUN_STATUSES.has(run.status)).map((run) => run.id);
    if (activeRunIds.length === 0) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void Promise.all(activeRunIds.map(async (runId) => refreshRun(runId)));
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [refreshRun, runs, session]);

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );
  const selectedRunResults = selectedRunId ? resultsByRunId[selectedRunId] ?? [] : [];
  const datasetNameById = useMemo(
    () => Object.fromEntries(datasets.map((dataset) => [dataset.id, dataset.name])),
    [datasets],
  );
  const caseById = useMemo(
    () =>
      Object.fromEntries(
        datasets.flatMap((dataset) => dataset.cases.map((evalCase) => [evalCase.id, evalCase])),
      ) as Record<string, EvalCaseRecord>,
    [datasets],
  );

  const handleCreateDataset = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) {
      return;
    }

    setIsCreatingDataset(true);
    setErrorMessage(null);

    try {
      const cases = datasetQuestions
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0)
        .map((question) => ({ input_json: { question } }));

      const createdDataset = await createEvalDataset(session.accessToken, workspaceId, {
        name: datasetName.trim(),
        eval_type: "retrieval_chat",
        description: datasetDescription.trim() || undefined,
        cases,
      });
      setDatasets((currentDatasets) => sortDatasets([createdDataset, ...currentDatasets]));
      setDatasetName("");
      setDatasetDescription("");
      setDatasetQuestions("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to create eval dataset");
    } finally {
      setIsCreatingDataset(false);
    }
  };

  const handleCreateRun = async (datasetId: string) => {
    if (!session) {
      return;
    }

    setIsCreatingRunId(datasetId);
    setErrorMessage(null);

    try {
      const createdRun = await createEvalRun(session.accessToken, workspaceId, { dataset_id: datasetId });
      setRuns((currentRuns) => sortRuns([createdRun, ...currentRuns]));
      setSelectedRunId(createdRun.id);
      const storedRunIds = readStoredRunIds(workspaceId);
      writeStoredRunIds(workspaceId, Array.from(new Set([createdRun.id, ...storedRunIds])));
      if (!ACTIVE_RUN_STATUSES.has(createdRun.status)) {
        await loadRunResults(createdRun.id);
      }
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to create eval run");
    } finally {
      setIsCreatingRunId(null);
    }
  };

  if (!isReady) {
    return <SectionCard title="Evaluations">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to create eval datasets and inspect run outcomes." />;
  }

  return (
    <>
      <SectionCard
        title="Eval datasets"
        description={`Workspace: ${workspaceId}. Create minimal retrieval-chat datasets and launch eval runs.`}
      >
        <form onSubmit={handleCreateDataset} style={{ display: "grid", gap: 12, maxWidth: 720 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Dataset name</span>
            <input
              onChange={(event) => setDatasetName(event.target.value)}
              placeholder="Phase 4 retrieval chat dataset"
              required
              value={datasetName}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Description</span>
            <input
              onChange={(event) => setDatasetDescription(event.target.value)}
              placeholder="Optional description for this eval dataset"
              value={datasetDescription}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>Questions</span>
            <textarea
              onChange={(event) => setDatasetQuestions(event.target.value)}
              placeholder="One question per line. Leave empty if you want to create an empty dataset to test failure handling."
              rows={5}
              value={datasetQuestions}
            />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isCreatingDataset} type="submit">
            {isCreatingDataset ? "Creating dataset..." : "Create eval dataset"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Dataset list" description="Launch eval runs from any dataset in this workspace.">
        {isLoading ? <p>Loading datasets...</p> : null}
        {!isLoading && datasets.length === 0 ? <p>No eval datasets yet.</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {datasets.map((dataset) => (
            <li
              key={dataset.id}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                marginBottom: 12,
                padding: 12,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                <div>
                  <strong>{dataset.name}</strong>
                  <div>Type: {dataset.eval_type}</div>
                  <div>Cases: {dataset.cases.length}</div>
                  <div>Created: {new Date(dataset.created_at).toLocaleString()}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center" }}>
                  <button onClick={() => void handleCreateRun(dataset.id)} type="button">
                    {isCreatingRunId === dataset.id ? "Launching..." : "Run eval"}
                  </button>
                </div>
              </div>
              {dataset.description ? <p style={{ marginBottom: 0 }}>{dataset.description}</p> : null}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="Eval runs" description="Runs created here are remembered in local storage for this workspace.">
        {runs.length === 0 ? <p>No eval runs yet.</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {runs.map((run) => (
            <li
              key={run.id}
              style={{
                border: run.id === selectedRunId ? "1px solid #0f172a" : "1px solid #cbd5e1",
                borderRadius: 12,
                marginBottom: 12,
                padding: 12,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 10, marginBottom: 6, flexWrap: "wrap" }}>
                <strong>{datasetNameById[run.dataset_id] ?? run.dataset_id}</strong>
                {renderRunStatus(run.status)}
              </div>
              <div>Run ID: {run.id}</div>
              <div>Created: {new Date(run.created_at).toLocaleString()}</div>
              <div>
                Summary: {getSummaryMetric(run.summary_json, "completed_cases")} completed / {" "}
                {getSummaryMetric(run.summary_json, "total_cases")} total
              </div>
              <div style={{ marginTop: 8 }}>
                <button onClick={() => void refreshRun(run.id)} type="button">
                  {ACTIVE_RUN_STATUSES.has(run.status) ? "Refresh / Poll" : "Open"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="Eval run detail" description="Inspect summary metrics and per-case results.">
        {!selectedRun ? <p>Select or create an eval run to inspect it.</p> : null}
        {selectedRun ? (
          <div style={{ display: "grid", gap: 12 }}>
            <div>
              <strong>Run ID:</strong> {selectedRun.id}
            </div>
            <div>
              <strong>Status:</strong> {renderRunStatus(selectedRun.status)}
            </div>
            <div>
              <strong>Dataset:</strong> {datasetNameById[selectedRun.dataset_id] ?? selectedRun.dataset_id}
            </div>
            <div
              style={{
                display: "grid",
                gap: 12,
                gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
              }}
            >
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>Total cases</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "total_cases")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>Completed</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "completed_cases")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>Passed</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "passed_cases")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>Pass rate</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "pass_rate")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>Avg score</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "avg_score")}</div>
              </div>
            </div>
            <div>
              <strong>Summary JSON:</strong>
              <pre style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
                {JSON.stringify(selectedRun.summary_json, null, 2)}
              </pre>
            </div>
            {selectedRun.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>Run error:</strong>
                <p style={{ color: "#b91c1c", marginTop: 8 }}>{selectedRun.error_message}</p>
              </div>
            ) : null}
            <div>
              <strong>Per-case results</strong>
              {selectedRunResults.length === 0 ? (
                <p style={{ marginTop: 8 }}>
                  {ACTIVE_RUN_STATUSES.has(selectedRun.status)
                    ? "Results will appear once the run completes."
                    : "No results were recorded for this run."}
                </p>
              ) : (
                <ul style={{ listStyle: "none", margin: "12px 0 0", padding: 0 }}>
                  {selectedRunResults.map((result) => {
                    const answer =
                      typeof result.output_json.answer === "string" ? result.output_json.answer : null;
                    const sources = Array.isArray(result.output_json.sources)
                      ? result.output_json.sources
                      : [];
                    const question = getQuestion(caseById[result.eval_case_id]);

                    return (
                      <li
                        key={result.id}
                        style={{
                          border: "1px solid #cbd5e1",
                          borderRadius: 12,
                          marginBottom: 12,
                          padding: 12,
                        }}
                      >
                        <div style={{ alignItems: "center", display: "flex", gap: 8, flexWrap: "wrap" }}>
                          <strong>Case {result.eval_case_id}</strong>
                          {renderResultStatus(result.status)}
                        </div>
                        {question ? (
                          <p style={{ marginBottom: 8, marginTop: 8 }}>
                            <strong>Question:</strong> {question}
                          </p>
                        ) : null}
                        <div>Score: {result.score ?? "n/a"}</div>
                        <div>Passed: {result.passed == null ? "n/a" : result.passed ? "yes" : "no"}</div>
                        <div>Source count: {sources.length}</div>
                        {answer ? (
                          <p style={{ marginTop: 8 }}>
                            <strong>Answer:</strong> {answer}
                          </p>
                        ) : null}
                        {result.error_message ? (
                          <p style={{ color: "#b91c1c", marginTop: 8 }}>
                            <strong>Error:</strong> {result.error_message}
                          </p>
                        ) : null}
                        <details style={{ marginTop: 8 }}>
                          <summary>Raw result</summary>
                          <pre style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
                            {JSON.stringify(result, null, 2)}
                          </pre>
                        </details>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}
