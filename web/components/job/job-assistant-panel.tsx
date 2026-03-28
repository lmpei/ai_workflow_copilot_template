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
  JobComparisonCandidate,
  JobEvidenceStatus,
  JobFinding,
  JobFitAssessment,
  JobFitSignal,
  JobReviewBrief,
  JobShortlistResult,
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
    label: "JD 摘要",
    description: "总结岗位要求、招聘信号和面向评审者的下一步建议。",
    placeholder: "示例：负责 API、稳定性与 Python 的高级后端工程师岗位。",
  },
  resume_match: {
    label: "简历匹配",
    description: "基于已索引的招聘材料，评估候选人与目标岗位的 grounded 匹配度。",
    placeholder: "示例：偏 Python、系统设计和稳定性的基础平台工程师岗位。",
  },
};

const SENIORITY_OPTIONS = ["", "intern", "junior", "mid", "senior", "staff", "principal"] as const;

type SeniorityOption = (typeof SENIORITY_OPTIONS)[number];

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isSeniorityOption(value: string | undefined): value is SeniorityOption {
  return typeof value === "string" && SENIORITY_OPTIONS.includes(value as SeniorityOption);
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
    candidate_label: normalizeOptionalString(source.candidate_label),
    seniority: normalizeOptionalString(source.seniority),
    must_have_skills: normalizeStringList(source.must_have_skills),
    preferred_skills: normalizeStringList(source.preferred_skills),
    hiring_context: normalizeOptionalString(source.hiring_context),
    comparison_task_ids: normalizeStringList(source.comparison_task_ids),
    comparison_notes: normalizeOptionalString(source.comparison_notes),
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

function renderEvidenceStatusBadge(evidenceStatus: JobEvidenceStatus) {
  const styles: Record<JobEvidenceStatus, { label: string; color: string }> = {
    grounded_matches: { label: "已命中依据", color: "#166534" },
    documents_only: { label: "仅有文档", color: "#92400e" },
    no_documents: { label: "无文档", color: "#b91c1c" },
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
    grounded_match_found: { label: "已有 grounded 匹配", color: "#166534" },
    role_requirements_grounded: { label: "岗位要求已对齐", color: "#0369a1" },
    insufficient_grounding: { label: "需要更多依据", color: "#92400e" },
    no_documents_available: { label: "无材料", color: "#b91c1c" },
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
    { label: "文档", value: artifacts.document_count },
    { label: "命中片段", value: artifacts.match_count },
    { label: "工具调用", value: artifacts.tool_call_ids.length },
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
  if (input.candidate_label) {
    segments.push(`候选人：${input.candidate_label}`);
  }
  if (input.seniority) {
    segments.push(`级别：${input.seniority}`);
  }
  if (input.must_have_skills.length > 0) {
    segments.push(`必备：${input.must_have_skills.slice(0, 2).join(", ")}`);
  }
  if (input.comparison_task_ids.length > 0) {
    segments.push(`对比任务：${input.comparison_task_ids.length}`);
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
      <strong>有依据的发现</strong>
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
                  证据引用：{finding.evidence_ref_ids.join(", ")}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p>这次运行没有产出有依据的招聘发现。</p>
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
        <strong>招聘摘要</strong>
        {renderEvidenceStatusBadge(reviewBrief.evidence_status)}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>岗位摘要：</strong> {reviewBrief.role_summary}
        </div>
        {reviewBrief.candidate_label ? (
          <div>
            <strong>候选人：</strong> {reviewBrief.candidate_label}
          </div>
        ) : null}
        {reviewBrief.seniority ? (
          <div>
            <strong>级别：</strong> {reviewBrief.seniority}
          </div>
        ) : null}
        <div>
          <strong>必备技能：</strong>{" "}
          {reviewBrief.must_have_skills.length > 0 ? reviewBrief.must_have_skills.join(", ") : "未指定"}
        </div>
        <div>
          <strong>加分技能：</strong>{" "}
          {reviewBrief.preferred_skills.length > 0 ? reviewBrief.preferred_skills.join(", ") : "未指定"}
        </div>
        {reviewBrief.hiring_context ? (
          <div>
            <strong>招聘背景：</strong> {reviewBrief.hiring_context}
          </div>
        ) : null}
        {reviewBrief.comparison_task_count > 0 ? (
          <div>
            <strong>对比任务数：</strong> {reviewBrief.comparison_task_count}
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
        <strong>匹配评估</strong>
        {renderEvidenceStatusBadge(assessment.evidence_status)}
        {renderFitSignalBadge(assessment.fit_signal)}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>建议结论：</strong> {assessment.recommended_outcome}
        </div>
        <div>
          <strong>置信说明：</strong> {assessment.confidence_note}
        </div>
        <div>
          <strong>判断依据：</strong> {assessment.rationale}
        </div>
        <div>
          <strong>建议下一步：</strong> {recommendedNextStep}
        </div>
      </div>
    </div>
  );
}

function renderComparisonCandidates(candidates: JobComparisonCandidate[]) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <div>
      <strong>对比候选人评审</strong>
      <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
        {candidates.map((candidate) => (
          <li
            key={candidate.task_id}
            style={{
              border: "1px solid #cbd5e1",
              borderRadius: 12,
              padding: 12,
            }}
          >
            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
              <strong>{candidate.candidate_label}</strong>
              {renderFitSignalBadge(candidate.fit_signal)}
              {renderEvidenceStatusBadge(candidate.evidence_status)}
            </div>
            <div style={{ color: "#475569", marginBottom: 8 }}>{candidate.summary}</div>
            {candidate.target_role ? (
              <div>
                <strong>岗位：</strong> {candidate.target_role}
              </div>
            ) : null}
            {candidate.highlights.length > 0 ? (
              <div style={{ marginTop: 8 }}>
                <strong>亮点：</strong> {candidate.highlights.join(" | ")}
              </div>
            ) : null}
            {candidate.evidence_ref_ids.length > 0 ? (
              <div style={{ color: "#475569", fontSize: 14, marginTop: 8 }}>
                证据引用：{candidate.evidence_ref_ids.join(", ")}
              </div>
            ) : null}
            <div style={{ color: "#64748b", fontSize: 14, marginTop: 8 }}>Source task: {candidate.task_id}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function renderShortlist(
  shortlist: JobShortlistResult | undefined,
  candidatesByTaskId: ReadonlyMap<string, JobComparisonCandidate>,
) {
  if (!shortlist) {
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
      <strong>候选短名单输出</strong>
      <p style={{ marginBottom: 12, marginTop: 12 }}>{shortlist.shortlist_summary}</p>
      {shortlist.comparison_notes ? (
        <div style={{ marginBottom: 12 }}>
          <strong>短名单关注点：</strong> {shortlist.comparison_notes}
        </div>
      ) : null}

      <div style={{ display: "grid", gap: 12 }}>
        {shortlist.entries.map((entry) => {
          const candidate = candidatesByTaskId.get(entry.task_id);
          return (
            <div
              key={entry.task_id}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 12,
                padding: 12,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
                <strong>
                  #{entry.rank} {entry.candidate_label}
                </strong>
                {renderFitSignalBadge(entry.fit_signal)}
                {renderEvidenceStatusBadge(entry.evidence_status)}
              </div>
              {candidate ? <p style={{ color: "#475569", marginTop: 0 }}>{candidate.summary}</p> : null}
              <div>
                <strong>建议：</strong> {entry.recommendation}
              </div>
              <div style={{ marginTop: 8 }}>
                <strong>判断依据：</strong> {entry.rationale}
              </div>
              {entry.evidence_ref_ids.length > 0 ? (
                <div style={{ color: "#475569", fontSize: 14, marginTop: 8 }}>
                  证据引用：{entry.evidence_ref_ids.join(", ")}
                </div>
              ) : null}
              {renderListSection({
                title: "风险",
                items: entry.risks,
                emptyText: "该候选人没有记录额外短名单风险。",
              })}
              {renderListSection({
                title: "面试关注点",
                items: entry.interview_focus,
                emptyText: "该候选人没有记录额外面试关注点。",
              })}
            </div>
          );
        })}
      </div>

      {renderListSection({
        title: "短名单整体风险",
        items: shortlist.risks,
        emptyText: "没有记录短名单整体风险。",
      })}
      {renderListSection({
        title: "Shared interview focus",
        items: shortlist.interview_focus,
        emptyText: "没有记录共通的面试关注点。",
      })}
      {renderListSection({
        title: "Grounding gaps",
        items: shortlist.gaps,
        emptyText: "没有记录额外短名单缺口。",
      })}
    </div>
  );
}

function isSelectableComparisonTask(task: TaskRecord, result: JobTaskResult | null): boolean {
  if (task.status !== "completed" || task.task_type !== "resume_match" || result === null) {
    return false;
  }
  return result.input.comparison_task_ids.length === 0;
}

export default function JobAssistantPanel({ workspaceId }: JobAssistantPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<JobTaskType>("jd_summary");
  const [targetRole, setTargetRole] = useState("");
  const [candidateLabel, setCandidateLabel] = useState("");
  const [seniority, setSeniority] = useState<SeniorityOption>("");
  const [mustHaveSkillsText, setMustHaveSkillsText] = useState("");
  const [preferredSkillsText, setPreferredSkillsText] = useState("");
  const [hiringContext, setHiringContext] = useState("");
  const [comparisonTaskIds, setComparisonTaskIds] = useState<string[]>([]);
  const [comparisonNotes, setComparisonNotes] = useState("");
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
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作区");
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
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载招聘任务");
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
  const comparisonTaskIdSet = useMemo(() => new Set(comparisonTaskIds), [comparisonTaskIds]);
  const selectedComparisonTasks = useMemo(
    () => tasks.filter((task) => comparisonTaskIdSet.has(task.id)),
    [comparisonTaskIdSet, tasks],
  );
  const comparisonRole = useMemo(() => {
    for (const task of selectedComparisonTasks) {
      const result = parseJobTaskResult(task);
      const input = parseJobTaskInput(task, result);
      if (input.target_role) {
        return input.target_role;
      }
    }
    return undefined;
  }, [selectedComparisonTasks]);
  const isShortlistMode = comparisonTaskIds.length > 0;
  const selectedComparisonCandidatesByTaskId = useMemo(
    () =>
      new Map(
        (selectedResult?.comparison_candidates ?? []).map((candidate) => [candidate.task_id, candidate] as const),
      ),
    [selectedResult],
  );

  const handleToggleComparisonTask = useCallback((task: TaskRecord) => {
    const result = parseJobTaskResult(task);
    const input = parseJobTaskInput(task, result);

    setTaskType("resume_match");
    setCandidateLabel("");
    setComparisonTaskIds((currentIds) =>
      currentIds.includes(task.id) ? currentIds.filter((taskId) => taskId !== task.id) : [...currentIds, task.id],
    );
    setTargetRole((currentValue) => (currentValue.trim() ? currentValue : input.target_role ?? ""));
    setHiringContext((currentValue) => (currentValue.trim() ? currentValue : input.hiring_context ?? ""));
    setMustHaveSkillsText((currentValue) =>
      currentValue.trim() ? currentValue : input.must_have_skills.join("\n"),
    );
    setPreferredSkillsText((currentValue) =>
      currentValue.trim() ? currentValue : input.preferred_skills.join("\n"),
    );
    if (isSeniorityOption(input.seniority)) {
      const inferredSeniority = input.seniority;
      setSeniority((currentValue) => (currentValue ? currentValue : inferredSeniority));
    }
  }, []);

  const handleClearComparison = useCallback(() => {
    setComparisonTaskIds([]);
    setComparisonNotes("");
  }, []);

  const handleCreateTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!session) {
      return;
    }

    const mustHaveSkills = parseSkillList(mustHaveSkillsText);
    const preferredSkills = parseSkillList(preferredSkillsText);
    const input: JsonObject = {};
    const normalizedTargetRole = targetRole.trim() || comparisonRole || "";
    const normalizedCandidateLabel = candidateLabel.trim();
    const normalizedHiringContext = hiringContext.trim();
    const normalizedComparisonNotes = comparisonNotes.trim();

    if (normalizedTargetRole) {
      input.target_role = normalizedTargetRole;
    }
    if (!isShortlistMode && normalizedCandidateLabel) {
      input.candidate_label = normalizedCandidateLabel;
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
    if (comparisonTaskIds.length > 0) {
      input.comparison_task_ids = comparisonTaskIds;
    }
    if (normalizedComparisonNotes) {
      input.comparison_notes = normalizedComparisonNotes;
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
      setCandidateLabel("");
      setSeniority("");
      setMustHaveSkillsText("");
      setPreferredSkillsText("");
      setHiringContext("");
      setComparisonTaskIds([]);
      setComparisonNotes("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法启动招聘任务");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Job Assistant">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in to run job tasks and inspect structured hiring outputs." />;
  }

  return (
    <>
      <SectionCard
        title="Job Assistant"
        description="启动结构化招聘流程，查看证据质量，并基于已索引材料审阅 grounded 匹配评估。"
      >
        {isLoadingWorkspace ? <p>正在加载工作区配置...</p> : null}
        {workspace ? (
          <div style={{ display: "grid", gap: 8 }}>
            <div>
              <strong>工作区：</strong> {workspace.name}
            </div>
            <div>
              <strong>模块：</strong> {workspace.module_type}
            </div>
            <div>
              <strong>能力：</strong>{" "}
              {Array.isArray(workspace.module_config_json.features)
                ? workspace.module_config_json.features.join(", ")
                : "文档摄取、结构化提取、任务、评测"}
            </div>
          </div>
        ) : null}
        {workspace?.module_type && workspace.module_type !== "job" ? (
          <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 12 }}>
            这个界面只对 Job 工作区开放。当前模块：{workspace.module_type}.
          </p>
        ) : null}
      </SectionCard>

      <SectionCard
        title="启动招聘评审"
        description="填写你已知的岗位重点、技能要求和招聘背景，再基于当前工作区已索引材料运行 grounded 招聘任务。"
      >
        <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12, maxWidth: 760 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>任务类型</span>
            <select
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
              onChange={(event) => {
                const nextTaskType = event.target.value as JobTaskType;
                setTaskType(nextTaskType);
                if (nextTaskType !== "resume_match") {
                  setComparisonTaskIds([]);
                  setComparisonNotes("");
                }
              }}
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

          {selectedComparisonTasks.length > 0 ? (
            <div
              style={{
                backgroundColor: "#eff6ff",
                border: "1px solid #bfdbfe",
                borderRadius: 12,
                display: "grid",
                gap: 8,
                padding: 12,
              }}
            >
              <div style={{ alignItems: "center", display: "flex", gap: 8, justifyContent: "space-between" }}>
                <strong>构建候选短名单对比</strong>
                <button onClick={handleClearComparison} type="button">
                  Clear
                </button>
              </div>
              <div>
                <strong>已选候选人评审：</strong> {selectedComparisonTasks.length}
              </div>
              {comparisonRole ? (
                <div>
                  <strong>共享岗位上下文：</strong> {comparisonRole}
                </div>
              ) : null}
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {selectedComparisonTasks.map((task) => {
                  const result = parseJobTaskResult(task);
                  const input = parseJobTaskInput(task, result);
                  return (
                    <li key={task.id}>
                      {(input.candidate_label ?? result?.title ?? task.id)} ({task.id})
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}

          <label style={{ display: "grid", gap: 6 }}>
            <span>目标岗位</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
              onChange={(event) => setTargetRole(event.target.value)}
              placeholder={TASK_OPTIONS[taskType].placeholder}
              rows={4}
              value={targetRole}
            />
          </label>

          {taskType === "resume_match" && !isShortlistMode ? (
            <label style={{ display: "grid", gap: 6 }}>
              <span>候选人标识</span>
              <input
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setCandidateLabel(event.target.value)}
                placeholder="示例：候选人 A / Alex Chen"
                type="text"
                value={candidateLabel}
              />
            </label>
          ) : null}

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span>级别</span>
              <select
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setSeniority(event.target.value as SeniorityOption)}
                value={seniority}
              >
                {SENIORITY_OPTIONS.map((option) => (
                  <option key={option || "none"} value={option}>
                    {option || "未指定"}
                  </option>
                ))}
              </select>
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>招聘背景</span>
              <input
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setHiringContext(event.target.value)}
                placeholder="平台团队、API 现代化、内部工具建设等"
                type="text"
                value={hiringContext}
              />
            </label>
          </div>

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span>必备技能</span>
              <textarea
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setMustHaveSkillsText(event.target.value)}
                placeholder={"每行一个技能，或用逗号分隔\nPython\nAPI 设计\n系统稳定性"}
                rows={5}
                value={mustHaveSkillsText}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>加分技能</span>
              <textarea
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setPreferredSkillsText(event.target.value)}
                placeholder={"每行一个技能，或用逗号分隔\n分布式系统\n数据管道"}
                rows={5}
                value={preferredSkillsText}
              />
            </label>
          </div>

          {isShortlistMode ? (
            <label style={{ display: "grid", gap: 6 }}>
              <span>短名单关注点</span>
              <textarea
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}
                onChange={(event) => setComparisonNotes(event.target.value)}
                placeholder="示例：优先考虑后端 owner 能力强、面试风险更低的候选人。"
                rows={3}
                value={comparisonNotes}
              />
            </label>
          ) : null}

          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button
            disabled={isCreating || (workspace?.module_type !== undefined && workspace.module_type !== "job")}
            type="submit"
          >
            {isCreating ? "正在启动..." : isShortlistMode ? "启动短名单对比" : "启动招聘任务"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Job runs"
        description="Tasks refresh automatically every 2 seconds so you can watch hiring reviews settle into a grounded structured result."
      >
        {isLoadingTasks ? <p>正在加载招聘任务...</p> : null}
        {!isLoadingTasks && tasks.length === 0 ? <p>还没有招聘任务。先启动一个任务来生成结构化招聘流程。</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {tasks.map((task) => {
            const result = parseJobTaskResult(task);
            const input = parseJobTaskInput(task, result);
            const roleSnapshot = formatRoleSnapshot(input);
            const canUseForComparison = isSelectableComparisonTask(task, result);
            const isSelectedForComparison = comparisonTaskIdSet.has(task.id);
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
                  {result?.shortlist ? (
                    <span style={{ color: "#0369a1", fontSize: 12, fontWeight: 600 }}>短名单任务</span>
                  ) : null}
                </div>
                <div style={{ color: "#475569", marginBottom: 6 }}>
                  {result?.summary ?? extractTargetRole(task, result) ?? "未提供自定义岗位重点。"}
                </div>
                {roleSnapshot ? (
                  <div style={{ color: "#64748b", fontSize: 14, marginBottom: 6 }}>{roleSnapshot}</div>
                ) : null}
                <div>任务 ID：{task.id}</div>
                <div>更新时间：{new Date(task.updated_at).toLocaleString()}</div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <button onClick={() => setSelectedTaskId(task.id)} type="button">
                      查看结果
                    </button>
                    {canUseForComparison ? (
                      <button onClick={() => handleToggleComparisonTask(task)} type="button">
                        {isSelectedForComparison ? "移出短名单" : "加入短名单"}
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
        title="Structured hiring result"
        description="Inspect the hiring brief, grounded findings, fit assessment, shortlist guidance, and follow-up decisions from the selected job task."
      >
        {!selectedTask ? <p>请选择一个招聘任务查看结果。</p> : null}
        {selectedTask ? (
          <div style={{ display: "grid", gap: 16 }}>
            <div style={{ display: "grid", gap: 6 }}>
              <div>
                <strong>任务 ID：</strong> {selectedTask.id}
              </div>
              <div>
                <strong>状态：</strong> {renderStatus(selectedTask.status)}
              </div>
              <div>
                <strong>任务类型：</strong> {TASK_OPTIONS[selectedTask.task_type as JobTaskType]?.label ?? selectedTask.task_type}
              </div>
              {selectedInput?.target_role ? (
                <div>
                  <strong>目标岗位：</strong> {selectedInput.target_role}
                </div>
              ) : null}
              {selectedTask.status === "completed" && isSelectableComparisonTask(selectedTask, selectedResult) ? (
                <div>
                  <button onClick={() => handleToggleComparisonTask(selectedTask)} type="button">
                    {comparisonTaskIdSet.has(selectedTask.id) ? "移出短名单" : "用于短名单"}
                  </button>
                </div>
              ) : null}
            </div>

            {selectedTask.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>招聘任务错误</strong>
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
                {renderShortlist(selectedResult.shortlist, selectedComparisonCandidatesByTaskId)}
                {renderAssessment(selectedResult.assessment, selectedResult.artifacts.recommended_next_step)}
                {renderComparisonCandidates(selectedResult.comparison_candidates)}
                {renderFindings(selectedResult.findings)}

                {renderListSection({
                  title: "缺口",
                  items: selectedResult.gaps,
                  emptyText: "这次运行没有产出明确的招聘缺口。",
                })}

                {renderListSection({
                  title: "Highlights",
                  items: selectedResult.highlights,
                  emptyText: "这次运行没有产出亮点摘要。",
                })}

                {renderListSection({
                  title: "开放问题",
                  items: selectedResult.open_questions,
                  emptyText: "这次运行没有产出额外开放问题。",
                })}

                {renderListSection({
                  title: "下一步建议",
                  items: selectedResult.next_steps,
                  emptyText: "这次运行没有产出下一步建议。",
                })}

                <div>
                  <strong>关联证据</strong>
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
                          <div style={{ color: "#475569", fontSize: 14 }}>引用 ID：{evidence.ref_id}</div>
                          {typeof evidence.metadata.document_id === "string" ? (
                            <div style={{ marginTop: 8 }}>
                              <Link href={`/workspaces/${workspaceId}/documents`}>打开招聘上下文</Link>
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>这次没有返回关联证据，通常说明工作区里的招聘材料或索引上下文还不充分。</p>
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
