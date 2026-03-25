"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  cancelEvalRun,
  createEvalDataset,
  createEvalRun,
  getEvalRun,
  getWorkspace,
  isApiClientError,
  listWorkspaces,
  listEvalDatasets,
  listEvalRunResults,
  listScenarioModules,
  retryEvalRun,
} from "../../lib/api";
import type {
  EvalCaseRecord,
  EvalDatasetRecord,
  EvalResultRecord,
  EvalRunRecord,
  ModuleType,
  ScenarioModuleRecord,
  TaskType,
  Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import RecoveryDetailCard from "../ui/recovery-detail-card";
import SectionCard from "../ui/section-card";

type EvalManagerProps = {
  workspaceId: string;
};

const ACTIVE_RUN_STATUSES = new Set<EvalRunRecord["status"]>(["pending", "running"]);
const STORAGE_KEY_PREFIX = "ai_workflow_eval_runs:";
const SHARED_READINESS_CHECKS = [
  "Workspace access, documents view, and task history must load without hidden setup steps.",
  "Each module should show either grounded output or an explicit degraded result instead of pretending confidence.",
  "Each module should have at least one scenario-aware eval dataset or a documented reason why eval coverage is pending.",
  "Release evidence and handoff notes should name which module surfaces were checked during the candidate rehearsal.",
] as const;
const MODULE_READINESS_CHECKS: Record<ModuleType, string[]> = {
  research: [
    "Run a Research task that produces either a structured report or an honest no-documents output.",
    "Inspect traces or task history to confirm evidence and regression metadata remain visible.",
  ],
  support: [
    "Run a Support task and verify case brief, triage, and reply guidance stay grounded or explicitly degraded.",
    "Confirm limited-context support runs escalate honestly instead of implying a grounded fix.",
  ],
  job: [
    "Run a Job task and verify hiring brief, fit assessment, and next steps stay grounded or explicitly degraded.",
    "Confirm limited-context hiring runs surface role-definition or materials gaps instead of implying a hiring decision.",
  ],
};

type CoverageStatus = "covered" | "template_only" | "missing" | "no_workspace";

type ModuleWorkspaceCoverageRecord = {
  workspace_id: string;
  workspace_name: string;
  dataset_count: number;
  default_task_dataset_count: number;
  default_task_case_count: number;
  latest_dataset_name?: string;
  status: CoverageStatus;
};

type ModuleEvalCoverageRecord = {
  module: ScenarioModuleRecord;
  status: CoverageStatus;
  total_workspace_count: number;
  total_dataset_count: number;
  default_task_dataset_count: number;
  default_task_case_count: number;
  covered_workspace_count: number;
  summary: string;
  known_gap: string;
  workspaces: ModuleWorkspaceCoverageRecord[];
};

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

function sortWorkspaces(workspaces: Workspace[]): Workspace[] {
  return [...workspaces].sort((left, right) => left.name.localeCompare(right.name));
}

function getDatasetScenarioTaskType(dataset: EvalDatasetRecord): TaskType | null {
  const scenarioTaskType = dataset.config_json.scenario_task_type;
  return typeof scenarioTaskType === "string" ? (scenarioTaskType as TaskType) : null;
}

function getCoverageStatusBadge(status: CoverageStatus) {
  const styles: Record<CoverageStatus, { label: string; color: string }> = {
    covered: { label: "Covered", color: "#166534" },
    template_only: { label: "Template only", color: "#92400e" },
    missing: { label: "Coverage missing", color: "#b91c1c" },
    no_workspace: { label: "No workspace", color: "#475569" },
  };
  const style = styles[status];

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

function buildModuleCoverage(
  module: ScenarioModuleRecord,
  workspaces: Workspace[],
  datasetsByWorkspaceId: Record<string, EvalDatasetRecord[]>,
): ModuleEvalCoverageRecord {
  const moduleWorkspaces = workspaces.filter((workspace) => workspace.module_type === module.module_type);
  const workspaceCoverage = moduleWorkspaces.map((workspace) => {
    const workspaceDatasets = sortDatasets(datasetsByWorkspaceId[workspace.id] ?? []);
    const defaultTaskDatasets = workspaceDatasets.filter(
      (dataset) => getDatasetScenarioTaskType(dataset) === module.default_eval_task_type,
    );
    const defaultTaskCaseCount = defaultTaskDatasets.reduce((total, dataset) => total + dataset.cases.length, 0);
    const status: CoverageStatus =
      defaultTaskDatasets.length === 0
        ? "missing"
        : defaultTaskCaseCount > 0
          ? "covered"
          : "template_only";

    return {
      workspace_id: workspace.id,
      workspace_name: workspace.name,
      dataset_count: workspaceDatasets.length,
      default_task_dataset_count: defaultTaskDatasets.length,
      default_task_case_count: defaultTaskCaseCount,
      latest_dataset_name: workspaceDatasets[0]?.name,
      status,
    } satisfies ModuleWorkspaceCoverageRecord;
  });

  const totalDatasetCount = workspaceCoverage.reduce((total, workspace) => total + workspace.dataset_count, 0);
  const defaultTaskDatasetCount = workspaceCoverage.reduce(
    (total, workspace) => total + workspace.default_task_dataset_count,
    0,
  );
  const defaultTaskCaseCount = workspaceCoverage.reduce((total, workspace) => total + workspace.default_task_case_count, 0);
  const coveredWorkspaceCount = workspaceCoverage.filter((workspace) => workspace.status === "covered").length;
  const status: CoverageStatus =
    workspaceCoverage.length === 0
      ? "no_workspace"
      : coveredWorkspaceCount > 0
        ? "covered"
        : workspaceCoverage.some((workspace) => workspace.status === "template_only")
          ? "template_only"
          : "missing";

  let summary = "Cross-module eval coverage is pending for this module.";
  let knownGap = "No default-task eval dataset is visible yet.";

  if (status === "covered") {
    summary = `Found ${defaultTaskDatasetCount} default-task dataset(s) with ${defaultTaskCaseCount} total case(s).`;
    knownGap = "No blocking default-task coverage gap is currently visible.";
  } else if (status === "template_only") {
    summary = `Default-task datasets exist, but they still have ${defaultTaskCaseCount} visible case(s).`;
    knownGap = "A template dataset exists, but it still needs real module-specific eval cases.";
  } else if (status === "no_workspace") {
    summary = "No workspace for this module is visible to the current collaborator.";
    knownGap = "Create or expose a workspace before claiming cross-module eval coverage.";
  }

  return {
    module,
    status,
    total_workspace_count: workspaceCoverage.length,
    total_dataset_count: totalDatasetCount,
    default_task_dataset_count: defaultTaskDatasetCount,
    default_task_case_count: defaultTaskCaseCount,
    covered_workspace_count: coveredWorkspaceCount,
    summary,
    known_gap: knownGap,
    workspaces: workspaceCoverage,
  };
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

function getScenarioModuleRecord(
  scenarioModules: ScenarioModuleRecord[],
  moduleType: ModuleType,
): ScenarioModuleRecord | null {
  return scenarioModules.find((module) => module.module_type === moduleType) ?? null;
}

function getScenarioTaskLabel(
  scenarioModules: ScenarioModuleRecord[],
  taskType: TaskType,
): string {
  const scenarioModule = scenarioModules.find((candidateModule) =>
    candidateModule.tasks.some((task) => task.task_type === taskType),
  );
  return scenarioModule?.task_labels[taskType] ?? taskType;
}

function getScenarioTaskTypeOptions(
  workspace: Workspace | null,
  scenarioModules: ScenarioModuleRecord[],
): TaskType[] {
  const moduleType = workspace?.module_type ?? "research";
  const scenarioModule = getScenarioModuleRecord(scenarioModules, moduleType);
  if (!scenarioModule) {
    return [];
  }

  const entryTaskTypes = workspace?.module_config_json.entry_task_types;
  if (Array.isArray(entryTaskTypes)) {
    const supportedTaskTypes = new Set(scenarioModule.tasks.map((task) => task.task_type));
    const filteredTaskTypes = entryTaskTypes.filter(
      (taskType): taskType is TaskType =>
        typeof taskType === "string" && supportedTaskTypes.has(taskType as TaskType),
    );
    if (filteredTaskTypes.length > 0) {
      return filteredTaskTypes;
    }
  }

  return scenarioModule.entry_task_types;
}

function getScenarioInputLabel(
  workspace: Workspace | null,
  scenarioModules: ScenarioModuleRecord[],
): string {
  const moduleType = workspace?.module_type ?? "research";
  return getScenarioModuleRecord(scenarioModules, moduleType)?.eval_input_label ?? "Scenario prompts";
}

function getScenarioInputPlaceholder(
  scenarioModules: ScenarioModuleRecord[],
  taskType: TaskType,
): string {
  const scenarioModule = scenarioModules.find((candidateModule) =>
    candidateModule.tasks.some((task) => task.task_type === taskType),
  );
  return scenarioModule?.tasks.find((task) => task.task_type === taskType)?.eval_prompt_placeholder ?? "One prompt per line";
}

function formatThreshold(passThreshold: number): string {
  return `${Math.round(passThreshold * 100)}%`;
}

function getCasePrompt(
  evalCase: EvalCaseRecord | undefined,
  moduleType: ModuleType,
  scenarioModules: ScenarioModuleRecord[],
): string | null {
  if (!evalCase) {
    return null;
  }

  const promptField = getScenarioModuleRecord(scenarioModules, moduleType)?.eval_prompt_field;
  if (!promptField) {
    return null;
  }

  const value = evalCase.input_json[promptField];
  return typeof value === "string" && value.length > 0 ? value : null;
}

function buildCaseInputJson(
  moduleType: ModuleType,
  prompt: string,
  scenarioModules: ScenarioModuleRecord[],
): Record<string, string> {
  const promptField = getScenarioModuleRecord(scenarioModules, moduleType)?.eval_prompt_field ?? "question";
  return { [promptField]: prompt };
}
export default function EvalManager({ workspaceId }: EvalManagerProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [scenarioModules, setScenarioModules] = useState<ScenarioModuleRecord[]>([]);
  const [allWorkspaces, setAllWorkspaces] = useState<Workspace[]>([]);
  const [coverageDatasetsByWorkspaceId, setCoverageDatasetsByWorkspaceId] = useState<Record<string, EvalDatasetRecord[]>>({});
  const [datasets, setDatasets] = useState<EvalDatasetRecord[]>([]);
  const [runs, setRuns] = useState<EvalRunRecord[]>([]);
  const [resultsByRunId, setResultsByRunId] = useState<Record<string, EvalResultRecord[]>>({});
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const [datasetDescription, setDatasetDescription] = useState("");
  const [datasetQuestions, setDatasetQuestions] = useState("");
  const [scenarioTaskType, setScenarioTaskType] = useState<TaskType>("research_summary");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingDataset, setIsCreatingDataset] = useState(false);
  const [isCreatingRunId, setIsCreatingRunId] = useState<string | null>(null);
  const [isControllingRunId, setIsControllingRunId] = useState<string | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  const scenarioTaskTypeOptions = useMemo(
    () => getScenarioTaskTypeOptions(workspace, scenarioModules),
    [workspace, scenarioModules],
  );

  useEffect(() => {
    if (!scenarioTaskTypeOptions.includes(scenarioTaskType)) {
      setScenarioTaskType(scenarioTaskTypeOptions[0] ?? "research_summary");
    }
  }, [scenarioTaskType, scenarioTaskTypeOptions]);

  const loadWorkspace = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      setScenarioModules([]);
      return;
    }

    try {
      const [loadedWorkspace, loadedScenarioModules] = await Promise.all([
        getWorkspace(session.accessToken, workspaceId),
        listScenarioModules(),
      ]);
      setWorkspace(loadedWorkspace);
      setScenarioModules(loadedScenarioModules);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load workspace");
    }
  }, [session, workspaceId]);

  const loadCoverage = useCallback(async () => {
    if (!session) {
      setAllWorkspaces([]);
      setCoverageDatasetsByWorkspaceId({});
      return;
    }

    try {
      const loadedWorkspaces = sortWorkspaces(await listWorkspaces(session.accessToken));
      setAllWorkspaces(loadedWorkspaces);
      const coverageEntries = await Promise.all(
        loadedWorkspaces.map(async (candidateWorkspace) => {
          const workspaceDatasets = sortDatasets(
            await listEvalDatasets(session.accessToken, candidateWorkspace.id),
          );
          return [candidateWorkspace.id, workspaceDatasets] as const;
        }),
      );
      setCoverageDatasetsByWorkspaceId(Object.fromEntries(coverageEntries));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load cross-module eval coverage");
    }
  }, [session]);

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
    void loadWorkspace();
    void loadCoverage();
    void loadDatasets();
    void loadStoredRuns();
  }, [loadCoverage, loadDatasets, loadStoredRuns, loadWorkspace]);

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
  const moduleCoverage = useMemo(
    () =>
      scenarioModules.map((module) =>
        buildModuleCoverage(module, allWorkspaces, coverageDatasetsByWorkspaceId),
      ),
    [allWorkspaces, coverageDatasetsByWorkspaceId, scenarioModules],
  );
  const rehearsalEvidenceDraft = useMemo(() => {
    const lines = [
      "# Stage C Cross-Module Rehearsal Evidence",
      "",
      "## Metadata",
      "- Completed At:",
      "- Release Owner:",
      "- Candidate Workspace:",
      `- Current Workspace: ${workspace?.name ?? workspaceId}`,
      "- Change Ref:",
      "- Rollback Target:",
      "",
      "## Coverage Snapshot",
    ];

    for (const coverage of moduleCoverage) {
      lines.push(
        `- ${coverage.module.title}: ${coverage.summary}`,
        `  - Status: ${coverage.status}`,
        `  - Default eval task: ${getScenarioTaskLabel(scenarioModules, coverage.module.default_eval_task_type)}`,
        `  - Quality baseline: ${coverage.module.quality_baseline}`,
        `  - Pass threshold: ${formatThreshold(coverage.module.pass_threshold)}`,
        `  - Known gap: ${coverage.known_gap}`,
      );
      if (coverage.workspaces.length > 0) {
        for (const workspaceCoverage of coverage.workspaces) {
          lines.push(
            `  - Workspace ${workspaceCoverage.workspace_name}: ${workspaceCoverage.default_task_dataset_count} default-task dataset(s), ${workspaceCoverage.default_task_case_count} case(s), status ${workspaceCoverage.status}`,
          );
        }
      } else {
        lines.push("  - Workspace coverage: none visible to the current collaborator");
      }
    }

    lines.push(
      "",
      "## Manual Module Checks",
      "- Research surface checked:",
      "- Support surface checked:",
      "- Job surface checked:",
      "- Eval datasets or runs inspected:",
      "- Honest degraded output confirmed where context was thin:",
      "",
      "## Known Gaps / Follow-up",
      "- Remaining missing eval coverage:",
      "- Out-of-scope module surfaces:",
      "- Follow-up before wider use:",
    );

    return lines.join("\n");
  }, [moduleCoverage, scenarioModules, workspace, workspaceId]);
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
      const moduleType = workspace?.module_type ?? "research";
      const cases = datasetQuestions
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0)
        .map((prompt) => ({ input_json: buildCaseInputJson(moduleType, prompt, scenarioModules) }));

      const createdDataset = await createEvalDataset(session.accessToken, workspaceId, {
        name: datasetName.trim(),
        eval_type: "retrieval_chat",
        description: datasetDescription.trim() || undefined,
        config_json: {
          module_type: moduleType,
          scenario_task_type: scenarioTaskType,
        },
        cases,
      });
      setDatasets((currentDatasets) => sortDatasets([createdDataset, ...currentDatasets]));
      await loadCoverage();
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

  const handleCancelRun = async (run: EvalRunRecord) => {
    if (!session) {
      return;
    }

    setIsControllingRunId(run.id);
    setErrorMessage(null);

    try {
      const updatedRun = await cancelEvalRun(session.accessToken, run.id);
      setRuns((currentRuns) => sortRuns(currentRuns.map((currentRun) => (currentRun.id === updatedRun.id ? updatedRun : currentRun))));
      setSelectedRunId(updatedRun.id);
      if (!ACTIVE_RUN_STATUSES.has(updatedRun.status)) {
        await loadRunResults(updatedRun.id);
      }
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to cancel eval run");
    } finally {
      setIsControllingRunId(null);
    }
  };

  const handleRetryRun = async (run: EvalRunRecord) => {
    if (!session) {
      return;
    }

    setIsControllingRunId(run.id);
    setErrorMessage(null);

    try {
      const retriedRun = await retryEvalRun(session.accessToken, run.id);
      setRuns((currentRuns) => sortRuns([retriedRun, ...currentRuns.filter((currentRun) => currentRun.id !== retriedRun.id)]));
      setSelectedRunId(retriedRun.id);
      const storedRunIds = readStoredRunIds(workspaceId);
      writeStoredRunIds(workspaceId, Array.from(new Set([retriedRun.id, ...storedRunIds])));
      if (!ACTIVE_RUN_STATUSES.has(retriedRun.status)) {
        await loadRunResults(retriedRun.id);
      }
      const refreshedSourceRun = await getEvalRun(session.accessToken, run.id);
      setRuns((currentRuns) =>
        sortRuns(
          [retriedRun, ...currentRuns.filter((currentRun) => currentRun.id !== retriedRun.id)].map((currentRun) =>
            currentRun.id === refreshedSourceRun.id ? refreshedSourceRun : currentRun,
          ),
        ),
      );
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to retry eval run");
    } finally {
      setIsControllingRunId(null);
    }
  };

  const handleCopyEvidenceDraft = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(rehearsalEvidenceDraft);
      setCopyFeedback("Evidence draft copied to clipboard.");
    } catch {
      setCopyFeedback("Clipboard copy failed. Select the draft manually.");
    }
  }, [rehearsalEvidenceDraft]);

  useEffect(() => {
    if (!copyFeedback) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setCopyFeedback(null);
    }, 2500);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [copyFeedback]);

  if (!isReady) {
    return <SectionCard title="Evaluations">Loading session...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to create eval datasets and inspect run outcomes." />;
  }

  return (
    <>
      <SectionCard
        title="Cross-module readiness baseline"
        description="Use one shared readiness standard across Research, Support, and Job so demo candidates are checked the same way before handoff."
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div>
            <strong>Shared candidate checks</strong>
            <ul>
              {SHARED_READINESS_CHECKS.map((check) => (
                <li key={check}>{check}</li>
              ))}
            </ul>
          </div>
          <div
            style={{
              display: "grid",
              gap: 12,
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            }}
          >
            {scenarioModules.map((module) => (
              <div
                key={module.module_type}
                style={{
                  border: "1px solid #cbd5e1",
                  borderRadius: 12,
                  padding: 12,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                  <strong>{module.title}</strong>
                  {workspace?.module_type === module.module_type ? (
                    <span
                      style={{
                        backgroundColor: "#0f172a12",
                        borderRadius: 999,
                        color: "#0f172a",
                        fontSize: 12,
                        fontWeight: 600,
                        padding: "2px 10px",
                        textTransform: "uppercase",
                      }}
                    >
                      active workspace
                    </span>
                  ) : null}
                </div>
                <div>Baseline: {module.quality_baseline}</div>
                <div>Pass threshold: {formatThreshold(module.pass_threshold)}</div>
                <div>
                  Default eval task: {getScenarioTaskLabel(scenarioModules, module.default_eval_task_type)}
                </div>
                <ul style={{ marginBottom: 0, marginTop: 10 }}>
                  {MODULE_READINESS_CHECKS[module.module_type].map((check) => (
                    <li key={check}>{check}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Cross-module eval coverage"
        description="Aggregate visible workspaces and eval datasets so collaborators can tell which default module evals exist, which are still template-only, and which remain missing."
      >
        <div style={{ display: "grid", gap: 12 }}>
          {moduleCoverage.map((coverage) => (
            <div
              key={coverage.module.module_type}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                padding: 12,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
                <strong>{coverage.module.title}</strong>
                {getCoverageStatusBadge(coverage.status)}
              </div>
              <div>
                Default eval task: {getScenarioTaskLabel(scenarioModules, coverage.module.default_eval_task_type)}
              </div>
              <div>
                Coverage snapshot: {coverage.default_task_dataset_count} default-task dataset(s) / {coverage.default_task_case_count} case(s)
              </div>
              <div>{coverage.summary}</div>
              <div style={{ color: "#475569", marginTop: 8 }}>
                <strong>Known gap:</strong> {coverage.known_gap}
              </div>
              {coverage.workspaces.length > 0 ? (
                <ul style={{ marginBottom: 0, marginTop: 10 }}>
                  {coverage.workspaces.map((workspaceCoverage) => (
                    <li key={workspaceCoverage.workspace_id}>
                      {workspaceCoverage.workspace_name}: {workspaceCoverage.default_task_dataset_count} default-task dataset(s), {workspaceCoverage.default_task_case_count} case(s), status {workspaceCoverage.status}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ marginBottom: 0, marginTop: 10 }}>No visible workspace currently represents this module.</p>
              )}
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Cross-module rehearsal evidence draft"
        description="Use this lightweight draft as the durable record for Stage C rehearsal evidence. It stays explicit about module checks, default eval coverage, and known gaps without pretending stronger operational guarantees."
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            <button onClick={() => void handleCopyEvidenceDraft()} type="button">
              Copy evidence draft
            </button>
            <span style={{ color: "#475569" }}>Template doc: `docs/development/STAGE_C_REHEARSAL_EVIDENCE_TEMPLATE.md`</span>
          </div>
          {copyFeedback ? <p style={{ color: "#0369a1", margin: 0 }}>{copyFeedback}</p> : null}
          <pre style={{ margin: 0, overflowX: "auto", whiteSpace: "pre-wrap" }}>{rehearsalEvidenceDraft}</pre>
        </div>
      </SectionCard>

      <SectionCard
        title="Eval datasets"
        description={`Workspace: ${workspace?.name ?? workspaceId}. Create scenario-aware retrieval eval datasets and launch eval runs.`}
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
            <span>Scenario focus</span>
            <select
              onChange={(event) => setScenarioTaskType(event.target.value as TaskType)}
              value={scenarioTaskType}
            >
              {scenarioTaskTypeOptions.map((taskType) => (
                <option key={taskType} value={taskType}>
                  {getScenarioTaskLabel(scenarioModules, taskType)}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>{getScenarioInputLabel(workspace, scenarioModules)}</span>
            <textarea
              onChange={(event) => setDatasetQuestions(event.target.value)}
              placeholder={`${getScenarioInputPlaceholder(scenarioModules, scenarioTaskType)}. Leave empty if you want to create an empty dataset to test failure handling.`}
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
                  <div>
                    Module: {String(dataset.config_json.module_type ?? "research")} / Task:{" "}
                    {String(dataset.config_json.scenario_task_type ?? "research_summary")}
                  </div>
                  <div>Baseline: {String(dataset.config_json.quality_baseline ?? "n/a")}</div>
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
              <div>Recovery: {run.recovery_state}</div>
              <div>
                Summary: {getSummaryMetric(run.summary_json, "completed_cases")} completed / {" "}
                {getSummaryMetric(run.summary_json, "total_cases")} total
              </div>
              <div style={{ marginTop: 8 }}>
                <button onClick={() => void refreshRun(run.id)} type="button">
                  {ACTIVE_RUN_STATUSES.has(run.status) ? "Refresh / Poll" : "Open"}
                </button>
                {run.status === "pending" || run.status === "running" ? (
                  <button
                    disabled={isControllingRunId === run.id}
                    onClick={() => void handleCancelRun(run)}
                    type="button"
                  >
                    {isControllingRunId === run.id ? "Cancelling..." : "Cancel run"}
                  </button>
                ) : null}
                {run.status === "failed" ? (
                  <button
                    disabled={isControllingRunId === run.id}
                    onClick={() => void handleRetryRun(run)}
                    type="button"
                  >
                    {isControllingRunId === run.id ? "Retrying..." : "Retry run"}
                  </button>
                ) : null}
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
              <strong>Recovery:</strong> {selectedRun.recovery_state}
            </div>
            <div>
              <strong>Dataset:</strong> {datasetNameById[selectedRun.dataset_id] ?? selectedRun.dataset_id}
            </div>
            <div>
              <strong>Scenario:</strong> {String(selectedRun.summary_json.module_type ?? "research")} /{" "}
              {String(selectedRun.summary_json.scenario_task_type ?? "research_summary")}
            </div>
            <div>
              <strong>Baseline:</strong> {String(selectedRun.summary_json.quality_baseline ?? "n/a")} (
              threshold {getSummaryMetric(selectedRun.summary_json, "pass_threshold")})
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              <button onClick={() => void refreshRun(selectedRun.id)} type="button">
                {ACTIVE_RUN_STATUSES.has(selectedRun.status) ? "Refresh / Poll" : "Refresh run"}
              </button>
              {selectedRun.status === "pending" || selectedRun.status === "running" ? (
                <button
                  disabled={isControllingRunId === selectedRun.id}
                  onClick={() => void handleCancelRun(selectedRun)}
                  type="button"
                >
                  {isControllingRunId === selectedRun.id ? "Cancelling..." : "Cancel run"}
                </button>
              ) : null}
              {selectedRun.status === "failed" ? (
                <button
                  disabled={isControllingRunId === selectedRun.id}
                  onClick={() => void handleRetryRun(selectedRun)}
                  type="button"
                >
                  {isControllingRunId === selectedRun.id ? "Retrying..." : "Retry run"}
                </button>
              ) : null}
            </div>
            <RecoveryDetailCard
              detail={selectedRun.recovery_detail}
              emptyText="This eval run has not recorded any cancel or retry lineage yet."
              title="Eval run recovery detail"
            />
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
                    const casePrompt = getCasePrompt(caseById[result.eval_case_id], String(selectedRun.summary_json.module_type ?? "research") as ModuleType, scenarioModules);

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
                        {casePrompt ? (
                          <p style={{ marginBottom: 8, marginTop: 8 }}>
                            <strong>Prompt:</strong> {casePrompt}
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
