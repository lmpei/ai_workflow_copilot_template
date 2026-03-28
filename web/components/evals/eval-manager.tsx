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
  "工作区访问、文档页和任务历史必须在没有隐藏前置步骤的情况下正常加载。",
  "每个模块都应展示 grounded 输出，或明确给出降级结果，而不是假装有把握。",
  "每个模块都应至少有一个场景感知的评测数据集，或明确记录为什么评测覆盖仍在等待。",
  "发布证据和交接记录应明确写出候选演练时检查了哪些模块界面。",
] as const;
const MODULE_READINESS_CHECKS: Record<ModuleType, string[]> = {
  research: [
    "运行一个 Research 任务，确认它能生成结构化报告，或在无文档时给出诚实结果。",
    "检查 trace 或任务历史，确认仍能看到证据和回归元数据。",
  ],
  support: [
    "运行一个 Support 任务，确认案例摘要、分诊和回复建议保持 grounded，或明确降级。",
    "确认上下文不足时，Support 会诚实升级，而不是暗示已经有 grounded 解决方案。",
  ],
  job: [
    "运行一个 Job 任务，确认招聘摘要、匹配评估和下一步建议保持 grounded，或明确降级。",
    "确认上下文不足时，Job 会明确暴露岗位定义或材料缺口，而不是暗示招聘结论。",
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
    covered: { label: "已覆盖", color: "#166534" },
    template_only: { label: "仅模板", color: "#92400e" },
    missing: { label: "缺少覆盖", color: "#b91c1c" },
    no_workspace: { label: "无工作区", color: "#475569" },
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

  let summary = "这个模块的跨模块评测覆盖仍在等待中。";
  let knownGap = "目前还看不到默认任务的评测数据集。";

  if (status === "covered") {
    summary = `发现 ${defaultTaskDatasetCount} 个默认任务数据集，共 ${defaultTaskCaseCount} 个 case。`;
    knownGap = "目前没有可见的默认任务覆盖阻塞项。";
  } else if (status === "template_only") {
    summary = `默认任务数据集已存在，但当前只有 ${defaultTaskCaseCount} 个可见 case。`;
    knownGap = "已经有模板数据集，但仍需要真实的模块级评测 case。";
  } else if (status === "no_workspace") {
    summary = "当前协作者看不到这个模块对应的工作区。";
    knownGap = "在宣称跨模块评测覆盖之前，先创建或暴露一个工作区。";
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
    pending: { label: "待处理", color: "#92400e" },
    running: { label: "运行中", color: "#1d4ed8" },
    completed: { label: "已完成", color: "#15803d" },
    failed: { label: "失败", color: "#b91c1c" },
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
  const label = status === "completed" ? "已完成" : status === "failed" ? "失败" : "运行中";
  return (
    <span style={{ color, fontWeight: 600, textTransform: "uppercase" }}>
      {label}
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作区");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载跨模块评测覆盖信息");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载评测数据集");
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
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载评测结果");
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
        setErrorMessage(isApiClientError(error) ? error.message : "无法刷新评测运行");
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
      "# 跨模块演练证据记录",
      "",
      "## 元数据",
      "- 完成时间：",
      "- 发布负责人：",
      "- 候选工作区：",
      `- 当前工作区：${workspace?.name ?? workspaceId}`,
      "- 变更引用：",
      "- 回滚目标：",
      "",
      "## 覆盖快照",
    ];

    for (const coverage of moduleCoverage) {
      lines.push(
        `- ${coverage.module.title}: ${coverage.summary}`,
        `  - 状态：${coverage.status}`,
        `  - 默认评测任务：${getScenarioTaskLabel(scenarioModules, coverage.module.default_eval_task_type)}`,
        `  - 质量基线：${coverage.module.quality_baseline}`,
        `  - 通过阈值：${formatThreshold(coverage.module.pass_threshold)}`,
        `  - 已知缺口：${coverage.known_gap}`,
      );
      if (coverage.workspaces.length > 0) {
        for (const workspaceCoverage of coverage.workspaces) {
          lines.push(
            `  - 工作区 ${workspaceCoverage.workspace_name}：${workspaceCoverage.default_task_dataset_count} 个默认评测数据集，${workspaceCoverage.default_task_case_count} 个 case，状态 ${workspaceCoverage.status}`,
          );
        }
      } else {
        lines.push("  - 工作区覆盖：当前协作者不可见");
      }
    }

    lines.push(
      "",
      "## 手动模块检查",
      "- Research 界面检查：",
      "- Support 界面检查：",
      "- Job 界面检查：",
      "- 已检查的评测数据集或运行：",
      "- 已确认在上下文不足时会诚实降级输出：",
      "",
      "## 已知缺口 / 后续",
      "- 剩余缺失的评测覆盖：",
      "- 当前不在范围内的模块界面：",
      "- 扩大使用前的后续事项：",
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法创建评测数据集");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法创建评测运行");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法取消评测运行");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法重试评测运行");
    } finally {
      setIsControllingRunId(null);
    }
  };

  const handleCopyEvidenceDraft = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(rehearsalEvidenceDraft);
      setCopyFeedback("证据草稿已复制到剪贴板。");
    } catch {
      setCopyFeedback("复制到剪贴板失败，请手动选择草稿内容。");
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
    return <SectionCard title="评测">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能创建评测数据集并查看运行结果。" />;
  }

  return (
    <>
      <SectionCard
        title="跨模块 readiness 基线"
        description="用一套共享 readiness 标准覆盖 Research、Support 和 Job，确保演示候选版本在交接前按同一标准检查。"
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div>
            <strong>共享候选检查项</strong>
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
                      当前工作区
                    </span>
                  ) : null}
                </div>
                <div>基线：{module.quality_baseline}</div>
                <div>通过阈值：{formatThreshold(module.pass_threshold)}</div>
                <div>
                  默认评测任务：{getScenarioTaskLabel(scenarioModules, module.default_eval_task_type)}
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
        title="跨模块评测覆盖"
        description="聚合当前可见的工作区和评测数据集，让协作者知道哪些模块默认评测已存在、哪些仍停留在模板、哪些仍然缺失。"
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
                默认评测任务：{getScenarioTaskLabel(scenarioModules, coverage.module.default_eval_task_type)}
              </div>
              <div>
                覆盖快照：{coverage.default_task_dataset_count} 个默认任务数据集 / {coverage.default_task_case_count} 个 case
              </div>
              <div>{coverage.summary}</div>
              <div style={{ color: "#475569", marginTop: 8 }}>
                <strong>已知缺口：</strong> {coverage.known_gap}
              </div>
              {coverage.workspaces.length > 0 ? (
                <ul style={{ marginBottom: 0, marginTop: 10 }}>
                  {coverage.workspaces.map((workspaceCoverage) => (
                    <li key={workspaceCoverage.workspace_id}>
                      {workspaceCoverage.workspace_name}: {workspaceCoverage.default_task_dataset_count} 个默认任务数据集，{workspaceCoverage.default_task_case_count} 个 case, status {workspaceCoverage.status}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ marginBottom: 0, marginTop: 10 }}>当前没有可见工作区代表这个模块。</p>
              )}
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="跨模块演练证据草稿"
        description="用这份轻量草稿作为跨模块演练证据记录。它会明确写出模块检查项、默认评测覆盖和已知缺口，而不会夸大运行保障。"
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            <button onClick={() => void handleCopyEvidenceDraft()} type="button">
              复制证据草稿
            </button>
            <span style={{ color: "#475569" }}>模板文档：`docs/development/STAGE_C_REHEARSAL_EVIDENCE_TEMPLATE.md`</span>
          </div>
          {copyFeedback ? <p style={{ color: "#0369a1", margin: 0 }}>{copyFeedback}</p> : null}
          <pre style={{ margin: 0, overflowX: "auto", whiteSpace: "pre-wrap" }}>{rehearsalEvidenceDraft}</pre>
        </div>
      </SectionCard>

      <SectionCard
        title="评测数据集"
        description={`工作区：${workspace?.name ?? workspaceId}。创建场景感知的检索评测数据集，并启动评测运行。`}
      >
        <form onSubmit={handleCreateDataset} style={{ display: "grid", gap: 12, maxWidth: 720 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>数据集名称</span>
            <input
              onChange={(event) => setDatasetName(event.target.value)}
              placeholder="示例：阶段四检索对话数据集"
              required
              value={datasetName}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>描述</span>
            <input
              onChange={(event) => setDatasetDescription(event.target.value)}
              placeholder="可选：为这个评测数据集补充描述"
              value={datasetDescription}
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span>场景焦点</span>
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
              placeholder={`${getScenarioInputPlaceholder(scenarioModules, scenarioTaskType)}。如果你想创建空数据集来测试失败处理，可以留空。`}
              rows={5}
              value={datasetQuestions}
            />
          </label>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button disabled={isCreatingDataset} type="submit">
            {isCreatingDataset ? "正在创建数据集..." : "创建评测数据集"}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="数据集列表" description="可以从当前工作区中的任意数据集启动评测运行。">
        {isLoading ? <p>正在加载数据集...</p> : null}
        {!isLoading && datasets.length === 0 ? <p>还没有评测数据集。</p> : null}
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
                  <div>类型：{dataset.eval_type}</div>
                  <div>
                    Module: {String(dataset.config_json.module_type ?? "research")} / Task:{" "}
                    {String(dataset.config_json.scenario_task_type ?? "research_summary")}
                  </div>
                  <div>基线：{String(dataset.config_json.quality_baseline ?? "n/a")}</div>
                  <div>Case 数：{dataset.cases.length}</div>
                  <div>创建时间：{new Date(dataset.created_at).toLocaleString()}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center" }}>
                  <button onClick={() => void handleCreateRun(dataset.id)} type="button">
                    {isCreatingRunId === dataset.id ? "正在启动..." : "运行评测"}
                  </button>
                </div>
              </div>
              {dataset.description ? <p style={{ marginBottom: 0 }}>{dataset.description}</p> : null}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="评测运行" description="这里创建的运行会记录在当前工作区的本地存储中。">
        {runs.length === 0 ? <p>还没有评测运行。</p> : null}
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
              <div>运行 ID：{run.id}</div>
              <div>创建时间：{new Date(run.created_at).toLocaleString()}</div>
              <div>恢复状态：{run.recovery_state}</div>
              <div>
                摘要：{getSummaryMetric(run.summary_json, "completed_cases")} 已完成 / {" "}
                {getSummaryMetric(run.summary_json, "total_cases")} 总数
              </div>
              <div style={{ marginTop: 8 }}>
                <button onClick={() => void refreshRun(run.id)} type="button">
                  {ACTIVE_RUN_STATUSES.has(run.status) ? "刷新 / 轮询" : "打开"}
                </button>
                {run.status === "pending" || run.status === "running" ? (
                  <button
                    disabled={isControllingRunId === run.id}
                    onClick={() => void handleCancelRun(run)}
                    type="button"
                  >
                    {isControllingRunId === run.id ? "正在取消..." : "取消运行"}
                  </button>
                ) : null}
                {run.status === "failed" ? (
                  <button
                    disabled={isControllingRunId === run.id}
                    onClick={() => void handleRetryRun(run)}
                    type="button"
                  >
                    {isControllingRunId === run.id ? "正在重试..." : "重试运行"}
                  </button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="评测运行详情" description="查看汇总指标和逐 case 结果。">
        {!selectedRun ? <p>请选择或创建一个评测运行来查看详情。</p> : null}
        {selectedRun ? (
          <div style={{ display: "grid", gap: 12 }}>
            <div>
              <strong>运行 ID：</strong> {selectedRun.id}
            </div>
            <div>
              <strong>状态：</strong> {renderRunStatus(selectedRun.status)}
            </div>
            <div>
              <strong>恢复状态：</strong> {selectedRun.recovery_state}
            </div>
            <div>
              <strong>数据集：</strong> {datasetNameById[selectedRun.dataset_id] ?? selectedRun.dataset_id}
            </div>
            <div>
              <strong>场景：</strong> {String(selectedRun.summary_json.module_type ?? "research")} /{" "}
              {String(selectedRun.summary_json.scenario_task_type ?? "research_summary")}
            </div>
            <div>
              <strong>基线：</strong> {String(selectedRun.summary_json.quality_baseline ?? "n/a")} (
              阈值 {getSummaryMetric(selectedRun.summary_json, "pass_threshold")})
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              <button onClick={() => void refreshRun(selectedRun.id)} type="button">
                {ACTIVE_RUN_STATUSES.has(selectedRun.status) ? "刷新 / 轮询" : "刷新运行"}
              </button>
              {selectedRun.status === "pending" || selectedRun.status === "running" ? (
                <button
                  disabled={isControllingRunId === selectedRun.id}
                  onClick={() => void handleCancelRun(selectedRun)}
                  type="button"
                >
                  {isControllingRunId === selectedRun.id ? "正在取消..." : "取消运行"}
                </button>
              ) : null}
              {selectedRun.status === "failed" ? (
                <button
                  disabled={isControllingRunId === selectedRun.id}
                  onClick={() => void handleRetryRun(selectedRun)}
                  type="button"
                >
                  {isControllingRunId === selectedRun.id ? "正在重试..." : "重试运行"}
                </button>
              ) : null}
            </div>
            <RecoveryDetailCard
              detail={selectedRun.recovery_detail}
              emptyText="这个评测运行目前还没有记录任何取消或重试历史。"
              title="评测运行恢复详情"
            />
            <div
              style={{
                display: "grid",
                gap: 12,
                gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
              }}
            >
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>总 Case 数</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "total_cases")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>已完成</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "completed_cases")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>通过数</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "passed_cases")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>通过率</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "pass_rate")}</div>
              </div>
              <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
                <strong>平均分</strong>
                <div>{getSummaryMetric(selectedRun.summary_json, "avg_score")}</div>
              </div>
            </div>
            <div>
              <strong>汇总 JSON：</strong>
              <pre style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
                {JSON.stringify(selectedRun.summary_json, null, 2)}
              </pre>
            </div>
            {selectedRun.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>运行错误：</strong>
                <p style={{ color: "#b91c1c", marginTop: 8 }}>{selectedRun.error_message}</p>
              </div>
            ) : null}
            <div>
              <strong>逐 Case 结果</strong>
              {selectedRunResults.length === 0 ? (
                <p style={{ marginTop: 8 }}>
                  {ACTIVE_RUN_STATUSES.has(selectedRun.status)
                    ? "运行完成后会显示结果。"
                    : "这个运行没有记录任何结果。"}
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
                            <strong>提示词：</strong> {casePrompt}
                          </p>
                        ) : null}
                        <div>分数：{result.score ?? "n/a"}</div>
                        <div>是否通过：{result.passed == null ? "n/a" : result.passed ? "是" : "否"}</div>
                        <div>来源数量：{sources.length}</div>
                        {answer ? (
                          <p style={{ marginTop: 8 }}>
                            <strong>答案：</strong> {answer}
                          </p>
                        ) : null}
                        {result.error_message ? (
                          <p style={{ color: "#b91c1c", marginTop: 8 }}>
                            <strong>错误：</strong> {result.error_message}
                          </p>
                        ) : null}
                        <details style={{ marginTop: 8 }}>
                          <summary>原始结果</summary>
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
