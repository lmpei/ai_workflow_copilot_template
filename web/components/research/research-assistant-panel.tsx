"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  cancelTask,
  compareResearchAssets,
  createWorkspaceResearchAsset,
  createWorkspaceTask,
  getResearchAsset,
  getWorkspace,
  isApiClientError,
  listWorkspaceResearchAssets,
  listWorkspaceTasks,
  retryTask,
} from "../../lib/api";
import type {
  JsonObject,
  ResearchArtifacts,
  ResearchAssetComparisonRecord,
  ResearchAssetLink,
  ResearchAssetRecord,
  ResearchAssetRevisionRecord,
  ResearchAssetSummaryRecord,
  ResearchDeliverable,
  ResearchFormalReport,
  ResearchLineage,
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
import RecoveryDetailCard from "../ui/recovery-detail-card";
import SectionCard from "../ui/section-card";
import ResearchWorkbenchSection from "./research-workbench-section";

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
    research_asset_id:
      typeof value.research_asset_id === "string" && value.research_asset_id.length > 0
        ? value.research_asset_id
        : undefined,
    parent_task_id:
      typeof value.parent_task_id === "string" && value.parent_task_id.length > 0 ? value.parent_task_id : undefined,
    continuation_notes:
      typeof value.continuation_notes === "string" && value.continuation_notes.length > 0
        ? value.continuation_notes
        : undefined,
  };
}

function parseResearchLineage(value: unknown): ResearchLineage | undefined {
  if (!isJsonObject(value)) {
    return undefined;
  }

  if (
    typeof value.parent_task_id !== "string" ||
    typeof value.parent_task_type !== "string" ||
    typeof value.parent_title !== "string" ||
    typeof value.parent_summary !== "string"
  ) {
    return undefined;
  }

  return {
    parent_task_id: value.parent_task_id,
    parent_task_type:
      value.parent_task_type === "research_summary" || value.parent_task_type === "workspace_report"
        ? value.parent_task_type
        : "research_summary",
    parent_title: value.parent_title,
    parent_goal: typeof value.parent_goal === "string" && value.parent_goal.length > 0 ? value.parent_goal : undefined,
    parent_summary: value.parent_summary,
    parent_report_headline:
      typeof value.parent_report_headline === "string" && value.parent_report_headline.length > 0
        ? value.parent_report_headline
        : undefined,
    continuation_notes:
      typeof value.continuation_notes === "string" && value.continuation_notes.length > 0
        ? value.continuation_notes
        : undefined,
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

function parseResearchReport(value: unknown): ResearchFormalReport | undefined {
  if (!isJsonObject(value)) {
    return undefined;
  }

  const sections = Array.isArray(value.sections)
    ? value.sections
        .filter((section): section is JsonObject => isJsonObject(section))
        .map((section, index) => ({
          slug: typeof section.slug === "string" ? section.slug : `section-${index + 1}`,
          title: typeof section.title === "string" ? section.title : `Section ${index + 1}`,
          summary: typeof section.summary === "string" ? section.summary : "",
          bullets: parseStringArray(section.bullets),
          evidence_ref_ids: parseStringArray(section.evidence_ref_ids),
        }))
    : [];

  return {
    headline: typeof value.headline === "string" ? value.headline : "Research Report",
    executive_summary: typeof value.executive_summary === "string" ? value.executive_summary : "",
    sections,
    open_questions: parseStringArray(value.open_questions),
    recommended_next_steps: parseStringArray(value.recommended_next_steps),
    evidence_ref_ids: parseStringArray(value.evidence_ref_ids),
  };
}

function parseResearchAssetLink(value: unknown): ResearchAssetLink | undefined {
  if (!isJsonObject(value)) {
    return undefined;
  }

  if (
    typeof value.asset_id !== "string" ||
    typeof value.revision_id !== "string" ||
    typeof value.revision_number !== "number"
  ) {
    return undefined;
  }

  return {
    asset_id: value.asset_id,
    revision_id: value.revision_id,
    revision_number: value.revision_number,
  };
}

function parseResearchTaskResultValue(value: unknown): ResearchTaskResult | null {
  if (!isJsonObject(value)) {
    return null;
  }

  if (
    value.module_type !== "research" ||
    typeof value.task_type !== "string" ||
    typeof value.title !== "string" ||
    typeof value.summary !== "string" ||
    !Array.isArray(value.highlights) ||
    !Array.isArray(value.evidence) ||
    !isJsonObject(value.artifacts) ||
    !isJsonObject(value.metadata)
  ) {
    return null;
  }

  return {
    ...(value as unknown as ResearchTaskResult),
    task_type: value.task_type === "workspace_report" ? "workspace_report" : "research_summary",
    input: parseResearchTaskInput(value.input),
    lineage: parseResearchLineage(value.lineage),
    sections: parseResearchSections(value.sections, value),
    report: parseResearchReport(value.report),
  };
}

function parseResearchTaskResult(task: TaskRecord): ResearchTaskResult | null {
  return parseResearchTaskResultValue(task.output_json.result);
}

function parseResearchAssetLatestResult(
  asset: ResearchAssetSummaryRecord | ResearchAssetRecord,
): ResearchTaskResult | null {
  return parseResearchTaskResultValue(asset.latest_result_json);
}

function parseResearchAssetRevisionResult(revision: ResearchAssetRevisionRecord): ResearchTaskResult | null {
  return parseResearchTaskResultValue(revision.result_json);
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

function renderEvidenceReferenceBadges(
  evidenceRefIds: string[],
  evidenceLookup: Map<string, { title?: string | null }>,
) {
  if (evidenceRefIds.length === 0) {
    return null;
  }

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
      {evidenceRefIds.map((refId) => {
        const evidence = evidenceLookup.get(refId);
        const label = evidence?.title ? `${evidence.title} (${refId})` : refId;
        return (
          <span
            key={refId}
            style={{
              backgroundColor: "#e2e8f0",
              borderRadius: 999,
              color: "#0f172a",
              fontSize: 12,
              fontWeight: 600,
              padding: "4px 10px",
            }}
          >
            {label}
          </span>
        );
      })}
    </div>
  );
}

export default function ResearchAssistantPanel({ workspaceId }: ResearchAssistantPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [researchAssets, setResearchAssets] = useState<ResearchAssetSummaryRecord[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<ResearchAssetRecord | null>(null);
  const [compareAssetId, setCompareAssetId] = useState<string | null>(null);
  const [compareAsset, setCompareAsset] = useState<ResearchAssetRecord | null>(null);
  const [selectedAssetCompareRevisionId, setSelectedAssetCompareRevisionId] = useState<string | null>(null);
  const [compareAssetRevisionId, setCompareAssetRevisionId] = useState<string | null>(null);
  const [assetComparison, setAssetComparison] = useState<ResearchAssetComparisonRecord | null>(null);
  const [isComparingAssets, setIsComparingAssets] = useState(false);
  const [taskType, setTaskType] = useState<ResearchTaskType>("research_summary");
  const [goal, setGoal] = useState("");
  const [focusAreasText, setFocusAreasText] = useState("");
  const [keyQuestionsText, setKeyQuestionsText] = useState("");
  const [constraintsText, setConstraintsText] = useState("");
  const [deliverable, setDeliverable] = useState<ResearchDeliverable | "">("");
  const [requestedSections, setRequestedSections] = useState<ResearchRequestedSection[]>(
    DEFAULT_REQUESTED_SECTIONS.research_summary,
  );
  const [researchAssetId, setResearchAssetId] = useState<string | null>(null);
  const [parentTaskId, setParentTaskId] = useState<string | null>(null);
  const [continuationNotes, setContinuationNotes] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isLoadingAssets, setIsLoadingAssets] = useState(false);
  const [isLoadingSelectedAsset, setIsLoadingSelectedAsset] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isSavingAsset, setIsSavingAsset] = useState(false);
  const [isControllingTaskId, setIsControllingTaskId] = useState<string | null>(null);

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

  const loadSelectedAsset = useCallback(
    async (assetId: string, silent = false) => {
      if (!session) {
        setSelectedAsset(null);
        return;
      }

      if (!silent) {
        setIsLoadingSelectedAsset(true);
      }

      try {
        setSelectedAsset(await getResearchAsset(session.accessToken, assetId));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load research asset");
      } finally {
        if (!silent) {
          setIsLoadingSelectedAsset(false);
        }
      }
    },
    [session],
  );

  const loadCompareAsset = useCallback(
    async (assetId: string) => {
      if (!session) {
        setCompareAsset(null);
        return;
      }

      try {
        setCompareAsset(await getResearchAsset(session.accessToken, assetId));
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load comparison asset");
      }
    },
    [session],
  );

  const loadResearchAssets = useCallback(
    async (silent = false) => {
      if (!session) {
        setResearchAssets([]);
        setSelectedAssetId(null);
        setSelectedAsset(null);
        setCompareAssetId(null);
        setCompareAsset(null);
        setAssetComparison(null);
        return;
      }

      if (!silent) {
        setIsLoadingAssets(true);
      }

      try {
        const loadedAssets = await listWorkspaceResearchAssets(session.accessToken, workspaceId);
        const sortedAssets = [...loadedAssets].sort((left, right) => right.updated_at.localeCompare(left.updated_at));
        setResearchAssets(sortedAssets);
        setSelectedAssetId((currentSelectedAssetId) => {
          if (currentSelectedAssetId && sortedAssets.some((asset) => asset.id === currentSelectedAssetId)) {
            return currentSelectedAssetId;
          }
          return sortedAssets[0]?.id ?? null;
        });
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "Unable to load research workbench");
      } finally {
        if (!silent) {
          setIsLoadingAssets(false);
        }
      }
    },
    [session, workspaceId],
  );

  useEffect(() => {
    void loadWorkspace();
    void loadTasks();
    void loadResearchAssets();
  }, [loadResearchAssets, loadTasks, loadWorkspace]);

  useEffect(() => {
    if (!session) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void loadTasks(true);
      void loadResearchAssets(true);
      if (selectedAssetId) {
        void loadSelectedAsset(selectedAssetId, true);
      }
      if (compareAssetId) {
        void loadCompareAsset(compareAssetId);
      }
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [compareAssetId, loadCompareAsset, loadResearchAssets, loadSelectedAsset, loadTasks, selectedAssetId, session]);

  useEffect(() => {
    if (!selectedAssetId) {
      setSelectedAsset(null);
      return;
    }

    void loadSelectedAsset(selectedAssetId);
  }, [loadSelectedAsset, selectedAssetId]);

  useEffect(() => {
    const compareCandidates = researchAssets.filter((asset) => asset.id !== selectedAssetId);
    setCompareAssetId((currentCompareAssetId) => {
      if (compareCandidates.length === 0) {
        return null;
      }
      if (currentCompareAssetId && compareCandidates.some((asset) => asset.id === currentCompareAssetId)) {
        return currentCompareAssetId;
      }
      return compareCandidates[0]?.id ?? null;
    });
  }, [researchAssets, selectedAssetId]);

  useEffect(() => {
    if (!compareAssetId) {
      setCompareAsset(null);
      return;
    }

    void loadCompareAsset(compareAssetId);
  }, [compareAssetId, loadCompareAsset]);

  useEffect(() => {
    if (
      selectedAssetCompareRevisionId &&
      !selectedAsset?.revisions.some((revision) => revision.id === selectedAssetCompareRevisionId)
    ) {
      setSelectedAssetCompareRevisionId(null);
    }
  }, [selectedAsset, selectedAssetCompareRevisionId]);

  useEffect(() => {
    if (
      compareAssetRevisionId &&
      !compareAsset?.revisions.some((revision) => revision.id === compareAssetRevisionId)
    ) {
      setCompareAssetRevisionId(null);
    }
  }, [compareAsset, compareAssetRevisionId]);

  useEffect(() => {
    setAssetComparison(null);
  }, [compareAssetId, compareAssetRevisionId, selectedAssetCompareRevisionId, selectedAssetId]);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? null,
    [selectedTaskId, tasks],
  );
  const selectedResult = useMemo(
    () => (selectedTask ? parseResearchTaskResult(selectedTask) : null),
    [selectedTask],
  );
  const selectedTaskAssetLink = useMemo(
    () => (selectedResult ? parseResearchAssetLink(selectedResult.metadata.research_asset) : undefined),
    [selectedResult],
  );
  const continuationParentTask = useMemo(
    () => tasks.find((task) => task.id === parentTaskId) ?? null,
    [parentTaskId, tasks],
  );
  const continuationParentResult = useMemo(
    () => (continuationParentTask ? parseResearchTaskResult(continuationParentTask) : null),
    [continuationParentTask],
  );
  const continuationAssetSummary = useMemo(
    () => researchAssets.find((asset) => asset.id === researchAssetId) ?? null,
    [researchAssetId, researchAssets],
  );
  const evidenceLookup = useMemo(
    () =>
      new Map(
        (selectedResult?.evidence ?? []).map((item) => [item.ref_id, { title: item.title }]),
      ),
    [selectedResult],
  );

  const toggleRequestedSection = (section: ResearchRequestedSection) => {
    setRequestedSections((currentSections) => {
      if (currentSections.includes(section)) {
        return currentSections.filter((item) => item !== section);
      }
      return [...currentSections, section];
    });
  };

  const populateResearchForm = (
    nextTaskType: ResearchTaskType,
    input: ResearchTaskInput,
    options?: {
      assetId?: string | null;
      parentId?: string | null;
      continuation?: string;
      openTaskId?: string | null;
      openAssetId?: string | null;
    },
  ) => {
    setTaskType(nextTaskType);
    setGoal(input.goal ?? "");
    setFocusAreasText(input.focus_areas.join("\n"));
    setKeyQuestionsText(input.key_questions.join("\n"));
    setConstraintsText(input.constraints.join("\n"));
    setDeliverable(input.deliverable ?? (nextTaskType === "workspace_report" ? "report" : "brief"));
    setRequestedSections(
      input.requested_sections.length > 0 ? input.requested_sections : DEFAULT_REQUESTED_SECTIONS[nextTaskType],
    );
    setResearchAssetId(options?.assetId ?? input.research_asset_id ?? null);
    setParentTaskId(options?.parentId ?? input.parent_task_id ?? null);
    setContinuationNotes(options?.continuation ?? input.continuation_notes ?? "");
    if (options?.openTaskId) {
      setSelectedTaskId(options.openTaskId);
    }
    if (options?.openAssetId) {
      setSelectedAssetId(options.openAssetId);
    }
    setErrorMessage(null);
  };

  const clearWorkbenchLinkage = () => {
    setResearchAssetId(null);
    setParentTaskId(null);
    setContinuationNotes("");
  };

  const startFollowUpFromTask = (task: TaskRecord, result: ResearchTaskResult) => {
    populateResearchForm(result.task_type, result.input, {
      assetId: parseResearchAssetLink(result.metadata.research_asset)?.asset_id ?? null,
      parentId: task.id,
      continuation: result.sections.open_questions[0] ?? result.input.continuation_notes ?? "",
      openTaskId: task.id,
      openAssetId: parseResearchAssetLink(result.metadata.research_asset)?.asset_id ?? null,
    });
  };

  const startResearchFromAsset = (asset: ResearchAssetSummaryRecord | ResearchAssetRecord) => {
    const latestResult = parseResearchAssetLatestResult(asset);
    const latestInput = latestResult?.input ?? parseResearchTaskInput(asset.latest_input_json);
    populateResearchForm(latestResult?.task_type ?? asset.latest_task_type, latestInput, {
      assetId: asset.id,
      parentId: asset.latest_task_id ?? null,
      continuation: latestResult?.sections.open_questions[0] ?? latestInput.continuation_notes ?? "",
      openTaskId: asset.latest_task_id ?? null,
      openAssetId: asset.id,
    });
  };

  const startResearchFromRevision = (asset: ResearchAssetRecord, revision: ResearchAssetRevisionRecord) => {
    const revisionResult = parseResearchAssetRevisionResult(revision);
    const revisionInput = revisionResult?.input ?? parseResearchTaskInput(revision.input_json);
    populateResearchForm(revision.task_type, revisionInput, {
      assetId: asset.id,
      parentId: revision.task_id,
      continuation: revisionResult?.sections.open_questions[0] ?? revisionInput.continuation_notes ?? "",
      openTaskId: revision.task_id,
      openAssetId: asset.id,
    });
  };

  const handleRunAssetComparison = async () => {
    if (!session || !selectedAsset || !compareAssetId) {
      return;
    }

    setIsComparingAssets(true);
    setErrorMessage(null);

    try {
      const comparison = await compareResearchAssets(session.accessToken, {
        left_asset_id: selectedAsset.id,
        right_asset_id: compareAssetId,
        left_revision_id: selectedAssetCompareRevisionId ?? undefined,
        right_revision_id: compareAssetRevisionId ?? undefined,
      });
      setAssetComparison(comparison);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to compare research assets");
    } finally {
      setIsComparingAssets(false);
    }
  };

  const handleSaveTaskToWorkbench = async (task: TaskRecord) => {
    if (!session) {
      return;
    }

    setIsSavingAsset(true);
    setErrorMessage(null);

    try {
      const asset = await createWorkspaceResearchAsset(session.accessToken, workspaceId, {
        task_id: task.id,
      });
      await loadTasks(true);
      await loadResearchAssets(true);
      setSelectedAssetId(asset.id);
      setSelectedAsset(asset);
      setSelectedTaskId(task.id);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to save research asset");
    } finally {
      setIsSavingAsset(false);
    }
  };

  const handleCancelTask = async (task: TaskRecord) => {
    if (!session) {
      return;
    }

    setIsControllingTaskId(task.id);
    setErrorMessage(null);

    try {
      const updatedTask = await cancelTask(session.accessToken, task.id);
      setSelectedTaskId(updatedTask.id);
      await loadTasks(true);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to cancel research task");
    } finally {
      setIsControllingTaskId(null);
    }
  };

  const handleRetryTask = async (task: TaskRecord) => {
    if (!session) {
      return;
    }

    setIsControllingTaskId(task.id);
    setErrorMessage(null);

    try {
      const retriedTask = await retryTask(session.accessToken, task.id);
      setSelectedTaskId(retriedTask.id);
      await loadTasks(true);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to retry research task");
    } finally {
      setIsControllingTaskId(null);
    }
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

    if (researchAssetId) {
      payloadInput.research_asset_id = researchAssetId;
    }

    if (parentTaskId) {
      payloadInput.parent_task_id = parentTaskId;
    }

    const trimmedContinuationNotes = continuationNotes.trim();
    if (trimmedContinuationNotes.length > 0) {
      payloadInput.continuation_notes = trimmedContinuationNotes;
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
      setResearchAssetId(null);
      setParentTaskId(null);
      setContinuationNotes("");
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

      <ResearchWorkbenchSection
        researchAssets={researchAssets}
        selectedAssetId={selectedAssetId}
        selectedAsset={selectedAsset}
        compareAssetId={compareAssetId}
        compareAsset={compareAsset}
        selectedAssetCompareRevisionId={selectedAssetCompareRevisionId}
        compareAssetRevisionId={compareAssetRevisionId}
        comparison={assetComparison}
        isLoadingAssets={isLoadingAssets}
        isLoadingSelectedAsset={isLoadingSelectedAsset}
        isComparing={isComparingAssets}
        onSelectAsset={setSelectedAssetId}
        onSelectCompareAsset={setCompareAssetId}
        onSelectSelectedAssetCompareRevision={(revisionId) =>
          setSelectedAssetCompareRevisionId(revisionId && revisionId.length > 0 ? revisionId : null)
        }
        onSelectCompareAssetRevision={(revisionId) =>
          setCompareAssetRevisionId(revisionId && revisionId.length > 0 ? revisionId : null)
        }
        onRunComparison={() => void handleRunAssetComparison()}
        onContinueAsset={startResearchFromAsset}
        onContinueRevision={startResearchFromRevision}
        onOpenTask={setSelectedTaskId}
      />

      <SectionCard
        title="Launch research task"
        description="Define the research goal, scope, and output expectations for a reusable Stage B research run."
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
          {continuationAssetSummary ? (
            <div
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                display: "grid",
                gap: 8,
                padding: 12,
              }}
            >
              <div style={{ fontWeight: 700 }}>Workbench context</div>
              <div>
                <strong>Asset:</strong> {continuationAssetSummary.title}
              </div>
              <div>
                <strong>Latest revision:</strong> v{continuationAssetSummary.latest_revision_number}
              </div>
              <div>
                <strong>Latest summary:</strong> {continuationAssetSummary.latest_summary}
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button onClick={() => setSelectedAssetId(continuationAssetSummary.id)} type="button">
                  Open asset
                </button>
                <button onClick={clearWorkbenchLinkage} type="button">
                  Clear workbench link
                </button>
              </div>
            </div>
          ) : null}
          {continuationParentTask && continuationParentResult ? (
            <div
              style={{
                backgroundColor: "#f8fafc",
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                display: "grid",
                gap: 8,
                padding: 12,
              }}
            >
              <div style={{ fontWeight: 700 }}>Follow-up context</div>
              <div>
                <strong>Parent task:</strong> {continuationParentTask.id}
              </div>
              <div>
                <strong>Parent title:</strong> {continuationParentResult.title}
              </div>
              <div>
                <strong>Parent summary:</strong> {continuationParentResult.summary}
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button onClick={() => setSelectedTaskId(continuationParentTask.id)} type="button">
                  Open parent result
                </button>
                <button onClick={clearWorkbenchLinkage} type="button">
                  Clear follow-up
                </button>
              </div>
            </div>
          ) : null}
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
            <span>Continuation notes</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "research"}
              onChange={(event) => setContinuationNotes(event.target.value)}
              placeholder="Optional. Describe what this follow-up run should refine, compare, or challenge."
              rows={3}
              value={continuationNotes}
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
            const assetLink = result ? parseResearchAssetLink(result.metadata.research_asset) : undefined;
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
                  {assetLink ? (
                    <span
                      style={{
                        backgroundColor: "#dbeafe",
                        borderRadius: 999,
                        color: "#1d4ed8",
                        fontSize: 12,
                        fontWeight: 700,
                        padding: "4px 10px",
                      }}
                    >
                      Workbench v{assetLink.revision_number}
                    </span>
                  ) : null}
                </div>
                <div style={{ color: "#475569", marginBottom: 6 }}>
                  {result?.summary ?? extractGoal(task, result) ?? "No custom goal provided."}
                </div>
                <div>Task ID: {task.id}</div>
                <div>Updated: {new Date(task.updated_at).toLocaleString()}</div>
                <div>Recovery: {task.recovery_state}</div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button onClick={() => setSelectedTaskId(task.id)} type="button">
                      Open result
                    </button>
                    {task.status === "pending" || task.status === "running" ? (
                      <button
                        disabled={isControllingTaskId === task.id}
                        onClick={() => void handleCancelTask(task)}
                        type="button"
                      >
                        {isControllingTaskId === task.id ? "Cancelling..." : "Cancel task"}
                      </button>
                    ) : null}
                    {task.status === "failed" ? (
                      <button
                        disabled={isControllingTaskId === task.id}
                        onClick={() => void handleRetryTask(task)}
                        type="button"
                      >
                        {isControllingTaskId === task.id ? "Retrying..." : "Retry task"}
                      </button>
                    ) : null}
                    {task.status === "completed" && result ? (
                      <button onClick={() => startFollowUpFromTask(task, result)} type="button">
                        Continue research
                      </button>
                    ) : null}
                    {task.status === "completed" && result ? (
                      <button disabled={isSavingAsset} onClick={() => void handleSaveTaskToWorkbench(task)} type="button">
                        {assetLink ? "Refresh asset" : isSavingAsset ? "Saving..." : "Save to workbench"}
                      </button>
                    ) : null}
                    {assetLink ? (
                      <button onClick={() => setSelectedAssetId(assetLink.asset_id)} type="button">
                        Open asset
                      </button>
                    ) : null}
                  </div>
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
                <strong>Recovery:</strong> {selectedTask.recovery_state}
              </div>
              <div>
                <strong>Task type:</strong> {TASK_OPTIONS[selectedTask.task_type as ResearchTaskType].label}
              </div>
              {extractGoal(selectedTask, selectedResult) ? (
                <div>
                  <strong>Goal:</strong> {extractGoal(selectedTask, selectedResult)}
                </div>
              ) : null}
              {selectedTask.status === "completed" && selectedResult ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button onClick={() => startFollowUpFromTask(selectedTask, selectedResult)} type="button">
                    Continue from this result
                  </button>
                  <button disabled={isSavingAsset} onClick={() => void handleSaveTaskToWorkbench(selectedTask)} type="button">
                    {selectedTaskAssetLink ? "Refresh asset" : isSavingAsset ? "Saving..." : "Save to workbench"}
                  </button>
                  {selectedTaskAssetLink ? (
                    <button onClick={() => setSelectedAssetId(selectedTaskAssetLink.asset_id)} type="button">
                      Open linked asset
                    </button>
                  ) : null}
                </div>
              ) : null}
              {selectedTask.status === "pending" || selectedTask.status === "running" ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button
                    disabled={isControllingTaskId === selectedTask.id}
                    onClick={() => void handleCancelTask(selectedTask)}
                    type="button"
                  >
                    {isControllingTaskId === selectedTask.id ? "Cancelling..." : "Cancel task"}
                  </button>
                </div>
              ) : null}
              {selectedTask.status === "failed" ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button
                    disabled={isControllingTaskId === selectedTask.id}
                    onClick={() => void handleRetryTask(selectedTask)}
                    type="button"
                  >
                    {isControllingTaskId === selectedTask.id ? "Retrying..." : "Retry task"}
                  </button>
                </div>
              ) : null}
            </div>

            {selectedTask.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>Research error</strong>
                <p style={{ color: "#b91c1c", marginBottom: 0 }}>{selectedTask.error_message}</p>
              </div>
            ) : null}

            <RecoveryDetailCard
              detail={selectedTask.recovery_detail}
              emptyText="This task has not recorded any cancel or retry lineage yet."
              title="Task recovery detail"
            />

            {selectedResult ? (
              <>
                <div>
                  <h3 style={{ marginBottom: 8, marginTop: 0 }}>{selectedResult.title}</h3>
                  <p style={{ margin: 0 }}>{selectedResult.summary}</p>
                </div>

                {selectedTaskAssetLink ? (
                  <div
                    style={{
                      backgroundColor: "#eff6ff",
                      border: "1px solid #bfdbfe",
                      borderRadius: 16,
                      display: "grid",
                      gap: 8,
                      padding: 16,
                    }}
                  >
                    <div style={{ color: "#1d4ed8", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
                      Linked workbench asset
                    </div>
                    <div>
                      <strong>Asset:</strong> {selectedTaskAssetLink.asset_id}
                    </div>
                    <div>
                      <strong>Revision:</strong> v{selectedTaskAssetLink.revision_number}
                    </div>
                    <div>
                      <button onClick={() => setSelectedAssetId(selectedTaskAssetLink.asset_id)} type="button">
                        Open workbench asset
                      </button>
                    </div>
                  </div>
                ) : null}

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
                    <strong>Workbench asset:</strong> {selectedResult.input.research_asset_id ?? "none"}
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
                  <div>
                    <strong>Continuation notes</strong>
                    <p style={{ marginBottom: 0, marginTop: 8 }}>
                      {selectedResult.input.continuation_notes ?? "No continuation notes were provided."}
                    </p>
                  </div>
                </div>

                {selectedResult.lineage ? (
                  <div
                    style={{
                      backgroundColor: "#eff6ff",
                      border: "1px solid #bfdbfe",
                      borderRadius: 16,
                      display: "grid",
                      gap: 10,
                      padding: 16,
                    }}
                  >
                    <div style={{ color: "#1d4ed8", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
                      Follow-up lineage
                    </div>
                    <div>
                      <strong>Parent task:</strong> {selectedResult.lineage.parent_task_id}
                    </div>
                    <div>
                      <strong>Parent title:</strong> {selectedResult.lineage.parent_title}
                    </div>
                    {selectedResult.lineage.parent_goal ? (
                      <div>
                        <strong>Parent goal:</strong> {selectedResult.lineage.parent_goal}
                      </div>
                    ) : null}
                    {selectedResult.lineage.parent_report_headline ? (
                      <div>
                        <strong>Parent report:</strong> {selectedResult.lineage.parent_report_headline}
                      </div>
                    ) : null}
                    <div>
                      <strong>Parent summary:</strong> {selectedResult.lineage.parent_summary}
                    </div>
                    {selectedResult.lineage.continuation_notes ? (
                      <div>
                        <strong>Follow-up guidance:</strong> {selectedResult.lineage.continuation_notes}
                      </div>
                    ) : null}
                  </div>
                ) : null}

                {selectedResult.report ? (
                  <div
                    style={{
                      backgroundColor: "#f8fafc",
                      border: "1px solid #cbd5e1",
                      borderRadius: 16,
                      display: "grid",
                      gap: 16,
                      padding: 16,
                    }}
                  >
                    <div style={{ display: "grid", gap: 8 }}>
                      <div style={{ color: "#475569", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
                        Formal report
                      </div>
                      <h3 style={{ margin: 0 }}>{selectedResult.report.headline}</h3>
                      <p style={{ margin: 0 }}>{selectedResult.report.executive_summary}</p>
                      {renderEvidenceReferenceBadges(selectedResult.report.evidence_ref_ids, evidenceLookup)}
                    </div>

                    <div style={{ display: "grid", gap: 12 }}>
                      {selectedResult.report.sections.map((section) => (
                        <div
                          key={section.slug}
                          style={{
                            backgroundColor: "#ffffff",
                            border: "1px solid #cbd5e1",
                            borderRadius: 14,
                            padding: 14,
                          }}
                        >
                          <div style={{ fontWeight: 700 }}>{section.title}</div>
                          <p style={{ marginBottom: 0, marginTop: 8 }}>{section.summary}</p>
                          {section.bullets.length > 0 ? (
                            <ul style={{ marginBottom: 0, marginTop: 10 }}>
                              {section.bullets.map((bullet) => (
                                <li key={bullet}>{bullet}</li>
                              ))}
                            </ul>
                          ) : null}
                          {renderEvidenceReferenceBadges(section.evidence_ref_ids, evidenceLookup)}
                        </div>
                      ))}
                    </div>

                    <div style={{ display: "grid", gap: 12 }}>
                      <div>
                        <strong>Report open questions</strong>
                        {renderStringList(
                          selectedResult.report.open_questions,
                          "The report did not identify additional open questions.",
                        )}
                      </div>
                      <div>
                        <strong>Recommended next steps</strong>
                        {renderStringList(
                          selectedResult.report.recommended_next_steps,
                          "The report did not recommend follow-up work.",
                        )}
                      </div>
                    </div>
                  </div>
                ) : null}

                <div>
                  <strong>{selectedResult.report ? "Underlying structured sections" : "Section summary"}</strong>
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
                          {renderEvidenceReferenceBadges(finding.evidence_ref_ids, evidenceLookup)}
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
