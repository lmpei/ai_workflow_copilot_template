"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createWorkspaceTask,
  getWorkspace,
  isApiClientError,
  listWorkspaceTasks,
} from "../../lib/api";
import type {
  JobComparisonCandidate,
  JobEvidenceStatus,
  JobFitSignal,
  JobHiringPacketContinuationDraft,
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

type JobAssistantActionPanelProps = {
  workspaceId: string;
  continuationDraft?: JobHiringPacketContinuationDraft | null;
  requestedTaskType?: JobTaskType | null;
  onContinuationHandled?: () => void;
};

type SeniorityOption = "" | "intern" | "junior" | "mid" | "senior" | "staff" | "principal";

type ContinuationContext = {
  title: string;
  guidance: string;
  comparisonMode: boolean;
  suggestedNotePrompt?: string | null;
};

const TASK_OPTIONS: Record<JobTaskType, { label: string; description: string; placeholder: string }> = {
  jd_summary: {
    label: "岗位摘要",
    description: "梳理目标岗位的核心要求、缺口和下一步招聘建议。",
    placeholder: "示例：高级平台工程师，负责 Python API、服务稳定性和跨团队协作。",
  },
  resume_match: {
    label: "候选人评审 / 短名单",
    description: "先做单候选人的 grounded 评审，再把多个已完成评审汇总成短名单。",
    placeholder: "示例：评审高级后端候选人，重点关注 Python、API 设计和平台迁移经验。",
  },
};

const SENIORITY_OPTIONS: Array<{ value: SeniorityOption; label: string }> = [
  { value: "", label: "未指定" },
  { value: "intern", label: "实习" },
  { value: "junior", label: "初级" },
  { value: "mid", label: "中级" },
  { value: "senior", label: "高级" },
  { value: "staff", label: "资深" },
  { value: "principal", label: "首席" },
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

function parseSkillList(value: string): string[] {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter((item, index, items) => item.length > 0 && items.indexOf(item) === index);
}

function formatSkillList(items: string[]): string {
  return items.join("\n");
}

function parseJobTaskResult(task: TaskRecord): JobTaskResult | null {
  const result = task.output_json.result;
  if (!isJsonObject(result) || result.module_type !== "job") {
    return null;
  }
  return result as JobTaskResult;
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
    (entryTaskType): entryTaskType is JobTaskType => entryTaskType === "jd_summary" || entryTaskType === "resume_match",
  );
  return supported.length > 0 ? supported : ["jd_summary", "resume_match"];
}

function sortTasks(tasks: TaskRecord[]): TaskRecord[] {
  return [...tasks].sort((left, right) => right.created_at.localeCompare(left.created_at));
}

function renderBadge(label: string, color: string) {
  return (
    <span
      style={{
        backgroundColor: `${color}14`,
        borderRadius: 999,
        color,
        display: "inline-block",
        fontSize: 12,
        fontWeight: 600,
        padding: "4px 10px",
      }}
    >
      {label}
    </span>
  );
}

function renderStatus(status: TaskRecord["status"]) {
  const labels: Record<TaskRecord["status"], [string, string]> = {
    pending: ["待处理", "#92400e"],
    running: ["运行中", "#1d4ed8"],
    completed: ["已完成", "#166534"],
    failed: ["失败", "#b91c1c"],
  };
  return renderBadge(labels[status][0], labels[status][1]);
}

function renderEvidenceStatus(status: JobEvidenceStatus) {
  const labels: Record<JobEvidenceStatus, [string, string]> = {
    grounded_matches: ["已命中依据", "#166534"],
    documents_only: ["仅有文档", "#92400e"],
    no_documents: ["无文档", "#b91c1c"],
  };
  return renderBadge(labels[status][0], labels[status][1]);
}

function renderFitSignal(status: JobFitSignal) {
  const labels: Record<JobFitSignal, [string, string]> = {
    grounded_match_found: ["已发现 grounded 匹配", "#166534"],
    role_requirements_grounded: ["岗位要求已对齐", "#0369a1"],
    insufficient_grounding: ["依据不足", "#92400e"],
    no_documents_available: ["缺少材料", "#b91c1c"],
  };
  return renderBadge(labels[status][0], labels[status][1]);
}

function renderStringList(items: string[], emptyText: string) {
  if (items.length === 0) {
    return <p style={{ color: "#64748b", margin: 0 }}>{emptyText}</p>;
  }
  return (
    <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function isSelectableComparisonTask(task: TaskRecord, result: JobTaskResult | null): boolean {
  if (task.status !== "completed" || task.task_type !== "resume_match" || result === null) {
    return false;
  }
  return result.input.comparison_task_ids.length === 0 && !result.shortlist;
}

function renderComparisonCandidates(candidates: JobComparisonCandidate[]) {
  if (candidates.length === 0) {
    return <p style={{ color: "#64748b", margin: 0 }}>当前没有比较候选人。</p>;
  }
  return (
    <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: 0, padding: 0 }}>
      {candidates.map((candidate) => (
        <li
          key={candidate.task_id}
          style={{
            border: "1px solid #cbd5e1",
            borderRadius: 12,
            display: "grid",
            gap: 8,
            padding: 12,
          }}
        >
          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
            <strong>{candidate.candidate_label}</strong>
            {renderEvidenceStatus(candidate.evidence_status)}
            {renderFitSignal(candidate.fit_signal)}
          </div>
          <p style={{ color: "#475569", margin: 0 }}>{candidate.summary}</p>
        </li>
      ))}
    </ul>
  );
}

function renderShortlist(shortlist?: JobShortlistResult) {
  if (!shortlist) {
    return <p style={{ color: "#64748b", margin: 0 }}>当前还没有短名单结果。</p>;
  }
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div>{shortlist.shortlist_summary}</div>
      {shortlist.comparison_notes ? (
        <div>
          <strong>对比备注：</strong> {shortlist.comparison_notes}
        </div>
      ) : null}
      <div style={{ display: "grid", gap: 10 }}>
        {shortlist.entries.map((entry) => (
          <div
            key={`${entry.task_id}-${entry.rank}`}
            style={{
              border: "1px solid #cbd5e1",
              borderRadius: 12,
              display: "grid",
              gap: 8,
              padding: 12,
            }}
          >
            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
              <strong>#{entry.rank} {entry.candidate_label}</strong>
              {renderEvidenceStatus(entry.evidence_status)}
              {renderFitSignal(entry.fit_signal)}
            </div>
            <div>
              <strong>建议：</strong> {entry.recommendation}
            </div>
            <div>
              <strong>理由：</strong> {entry.rationale}
            </div>
          </div>
        ))}
      </div>
      <div>
        <strong>共享风险</strong>
        {renderStringList(shortlist.risks, "当前没有共享风险。")}
      </div>
    </div>
  );
}

export default function JobAssistantActionPanel({
  workspaceId,
  continuationDraft,
  requestedTaskType,
  onContinuationHandled,
}: JobAssistantActionPanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<JobTaskType>("resume_match");
  const [targetRole, setTargetRole] = useState("");
  const [candidateLabel, setCandidateLabel] = useState("");
  const [seniority, setSeniority] = useState<SeniorityOption>("");
  const [mustHaveSkillsText, setMustHaveSkillsText] = useState("");
  const [preferredSkillsText, setPreferredSkillsText] = useState("");
  const [hiringContext, setHiringContext] = useState("");
  const [comparisonTaskIds, setComparisonTaskIds] = useState<string[]>([]);
  const [comparisonNotes, setComparisonNotes] = useState("");
  const [continuationContext, setContinuationContext] = useState<ContinuationContext | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const availableTaskTypes = useMemo(() => parseEntryTaskTypes(workspace), [workspace]);

  useEffect(() => {
    if (!availableTaskTypes.includes(taskType)) {
      setTaskType(availableTaskTypes[0] ?? "resume_match");
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

  const loadTasks = useCallback(async (silent = false) => {
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
      setSelectedTaskId((current) => (current && loadedTasks.some((task) => task.id === current) ? current : loadedTasks[0]?.id ?? null));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载 Job 任务");
    } finally {
      if (!silent) {
        setIsLoadingTasks(false);
      }
    }
  }, [session, workspaceId]);

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
    return () => window.clearInterval(intervalId);
  }, [loadTasks, session]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return undefined;
    }
    const syncSelectedTaskFromHash = () => {
      const hash = window.location.hash;
      if (!hash.startsWith("#job-task-")) {
        return;
      }
      const nextTaskId = hash.slice("#job-task-".length);
      if (tasks.some((task) => task.id === nextTaskId)) {
        setSelectedTaskId(nextTaskId);
      }
    };
    syncSelectedTaskFromHash();
    window.addEventListener("hashchange", syncSelectedTaskFromHash);
    return () => window.removeEventListener("hashchange", syncSelectedTaskFromHash);
  }, [tasks]);

  useEffect(() => {
    if (!continuationDraft) {
      return;
    }
    setTaskType(continuationDraft.suggested_task_type);
    setTargetRole(continuationDraft.target_role ?? "");
    setCandidateLabel("");
    setSeniority((continuationDraft.seniority as SeniorityOption | undefined) ?? "");
    setMustHaveSkillsText(formatSkillList(continuationDraft.must_have_skills));
    setPreferredSkillsText(formatSkillList(continuationDraft.preferred_skills));
    setHiringContext(continuationDraft.hiring_context ?? "");
    setComparisonTaskIds(continuationDraft.comparison_mode ? continuationDraft.comparison_task_ids : []);
    setComparisonNotes(continuationDraft.comparison_notes ?? continuationDraft.suggested_note_prompt ?? "");
    setContinuationContext({
      title: `正在从 packet「${continuationDraft.packet_title}」继续招聘工作`,
      guidance: continuationDraft.status_guidance,
      comparisonMode: continuationDraft.comparison_mode,
      suggestedNotePrompt: continuationDraft.suggested_note_prompt,
    });
    setErrorMessage(null);
    onContinuationHandled?.();
  }, [continuationDraft, onContinuationHandled]);

  useEffect(() => {
    if (!requestedTaskType || requestedTaskType === taskType) {
      return;
    }

    setTaskType(requestedTaskType);
    setErrorMessage(null);

    if (requestedTaskType !== "resume_match") {
      setComparisonTaskIds([]);
      setComparisonNotes("");
    }
  }, [requestedTaskType, taskType]);

  const comparisonTaskIdSet = useMemo(() => new Set(comparisonTaskIds), [comparisonTaskIds]);
  const comparisonCandidates = useMemo(
    () => tasks.filter((task) => isSelectableComparisonTask(task, parseJobTaskResult(task))),
    [tasks],
  );
  const selectedComparisonTasks = useMemo(
    () => comparisonCandidates.filter((task) => comparisonTaskIdSet.has(task.id)),
    [comparisonCandidates, comparisonTaskIdSet],
  );
  const comparisonRole = useMemo(
    () =>
      selectedComparisonTasks
        .map((task) => parseJobTaskInput(task, parseJobTaskResult(task)).target_role)
        .find(Boolean) ?? null,
    [selectedComparisonTasks],
  );
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
  const isShortlistMode = taskType === "resume_match" && comparisonTaskIds.length > 0;

  const handleToggleComparisonTask = useCallback(
    (task: TaskRecord) => {
      const result = parseJobTaskResult(task);
      if (!isSelectableComparisonTask(task, result)) {
        return;
      }
      const nextRole = parseJobTaskInput(task, result).target_role;
      setErrorMessage(null);
      setTaskType("resume_match");
      setComparisonTaskIds((currentIds) => {
        if (currentIds.includes(task.id)) {
          return currentIds.filter((taskId) => taskId !== task.id);
        }
        if (comparisonRole && nextRole && comparisonRole !== nextRole) {
          setErrorMessage("一次短名单比较只能组合到同一目标岗位的候选人评审任务。");
          return currentIds;
        }
        if (!targetRole && nextRole) {
          setTargetRole(nextRole);
        }
        return [...currentIds, task.id];
      });
    },
    [comparisonRole, targetRole],
  );

  const handleCreateTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) {
      return;
    }

    const input: JsonObject = {
      must_have_skills: parseSkillList(mustHaveSkillsText),
      preferred_skills: parseSkillList(preferredSkillsText),
      comparison_task_ids: taskType === "resume_match" ? comparisonTaskIds : [],
    };
    const normalizedTargetRole = targetRole.trim();
    const normalizedCandidateLabel = candidateLabel.trim();
    const normalizedHiringContext = hiringContext.trim();
    const normalizedComparisonNotes = comparisonNotes.trim();

    if (normalizedTargetRole) {
      input.target_role = normalizedTargetRole;
    }
    if (taskType === "resume_match" && !isShortlistMode && normalizedCandidateLabel) {
      input.candidate_label = normalizedCandidateLabel;
    }
    if (seniority) {
      input.seniority = seniority;
    }
    if (normalizedHiringContext) {
      input.hiring_context = normalizedHiringContext;
    }
    if (taskType === "resume_match" && normalizedComparisonNotes) {
      input.comparison_notes = normalizedComparisonNotes;
    }

    setIsCreating(true);
    setErrorMessage(null);
    try {
      const createdTask = await createWorkspaceTask(session.accessToken, workspaceId, { task_type: taskType, input });
      setTasks((currentTasks) => sortTasks([createdTask, ...currentTasks]));
      setSelectedTaskId(createdTask.id);
      if (typeof window !== "undefined") {
        window.location.hash = `job-task-${createdTask.id}`;
      }
      setCandidateLabel("");
      setComparisonTaskIds([]);
      setComparisonNotes("");
      setContinuationContext(null);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法启动 Job 任务");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Job 动作">正在加载会话...</SectionCard>;
  }
  if (!session) {
    return <AuthRequired description="登录后才能运行 Job 任务并查看结构化招聘结果。" />;
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <SectionCard title="Job 动作" description="继续已有 hiring packet，或围绕岗位和候选人启动新的 grounded Job 任务。">
        {isLoadingWorkspace ? <p>正在加载工作区配置...</p> : null}
        {workspace ? (
          <div style={{ display: "grid", gap: 8 }}>
            <div>
              <strong>工作区：</strong> {workspace.name}
            </div>
            <div>
              <strong>模块：</strong> {workspace.module_type}
            </div>
          </div>
        ) : null}
      </SectionCard>

      <SectionCard title="启动或继续 Job 任务" description="单候选人评审和 shortlist 刷新都从这里进入。">
        <div style={{ display: "grid", gap: 12, maxWidth: 760 }}>
          <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span>任务类型</span>
              <select
                value={taskType}
                onChange={(event) => {
                  const nextTaskType = event.target.value as JobTaskType;
                  setTaskType(nextTaskType);
                  if (nextTaskType !== "resume_match") {
                    setComparisonTaskIds([]);
                    setComparisonNotes("");
                  }
                }}
              >
                {availableTaskTypes.map((availableTaskType) => (
                  <option key={availableTaskType} value={availableTaskType}>
                    {TASK_OPTIONS[availableTaskType].label}
                  </option>
                ))}
              </select>
            </label>
            <p style={{ color: "#475569", margin: 0 }}>{TASK_OPTIONS[taskType].description}</p>

            {continuationContext ? (
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
                <strong>{continuationContext.title}</strong>
                <div>
                  <strong>当前推进建议：</strong> {continuationContext.guidance}
                </div>
                <div>
                  <strong>本次模式：</strong> {continuationContext.comparisonMode ? "直接刷新短名单" : "继续补充单候选人评审"}
                </div>
                {continuationContext.suggestedNotePrompt ? (
                  <div>
                    <strong>建议备注：</strong> {continuationContext.suggestedNotePrompt}
                  </div>
                ) : null}
              </div>
            ) : null}

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
                <div>
                  <strong>当前短名单比较集合：</strong> {selectedComparisonTasks.length} 条任务
                </div>
                {comparisonRole ? (
                  <div>
                    <strong>统一目标岗位：</strong> {comparisonRole}
                  </div>
                ) : null}
              </div>
            ) : null}

            <label style={{ display: "grid", gap: 6 }}>
              <span>目标岗位</span>
              <textarea
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
                placeholder={TASK_OPTIONS[taskType].placeholder}
                rows={4}
              />
            </label>

            {taskType === "resume_match" && !isShortlistMode ? (
              <label style={{ display: "grid", gap: 6 }}>
                <span>候选人标签</span>
                <input
                  type="text"
                  value={candidateLabel}
                  onChange={(event) => setCandidateLabel(event.target.value)}
                  placeholder="例如：候选人 A / Alex Chen"
                />
              </label>
            ) : null}

            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
              <label style={{ display: "grid", gap: 6 }}>
                <span>级别</span>
                <select value={seniority} onChange={(event) => setSeniority(event.target.value as SeniorityOption)}>
                  {SENIORITY_OPTIONS.map((option) => (
                    <option key={option.label} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "grid", gap: 6 }}>
                <span>招聘背景</span>
                <input
                  type="text"
                  value={hiringContext}
                  onChange={(event) => setHiringContext(event.target.value)}
                  placeholder="例如：当前缺一位能接住 API 稳定性与平台迁移的人"
                />
              </label>
            </div>

            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
              <label style={{ display: "grid", gap: 6 }}>
                <span>必须技能</span>
                <textarea
                  value={mustHaveSkillsText}
                  onChange={(event) => setMustHaveSkillsText(event.target.value)}
                  placeholder={"每行一个，或用逗号分隔\nPython\nAPI 设计\n服务稳定性"}
                  rows={5}
                />
              </label>
              <label style={{ display: "grid", gap: 6 }}>
                <span>加分技能</span>
                <textarea
                  value={preferredSkillsText}
                  onChange={(event) => setPreferredSkillsText(event.target.value)}
                  placeholder={"每行一个，或用逗号分隔\n分布式系统\n跨团队协作\n面试设计"}
                  rows={5}
                />
              </label>
            </div>

            {taskType === "resume_match" ? (
              <label style={{ display: "grid", gap: 6 }}>
                <span>{isShortlistMode ? "对比备注" : "评审备注（可选）"}</span>
                <textarea
                  value={comparisonNotes}
                  onChange={(event) => setComparisonNotes(event.target.value)}
                  placeholder={
                    isShortlistMode
                      ? "例如：优先关注 grounded 的后端 ownership、到岗速度和补材料风险。"
                      : "例如：这次重点看候选人的 API ownership 与平台稳定性经验。"
                  }
                  rows={3}
                />
              </label>
            ) : null}

            {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
            <button type="submit" disabled={isCreating}>
              {isCreating ? "正在启动..." : isShortlistMode ? "生成候选人短名单" : `启动${TASK_OPTIONS[taskType].label}`}
            </button>
          </form>
        </div>
      </SectionCard>

      <SectionCard title="最近 Job 任务" description="只保留继续招聘工作真正需要的最近任务和比较入口。">
        {isLoadingTasks ? <p>正在加载 Job 任务...</p> : null}
        {!isLoadingTasks && tasks.length === 0 ? <p>还没有 Job 任务。先启动一次岗位摘要或候选人评审。</p> : null}
        <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: 0, padding: 0 }}>
          {tasks.slice(0, 8).map((task) => {
            const result = parseJobTaskResult(task);
            const input = parseJobTaskInput(task, result);
            const selectableComparisonTask = isSelectableComparisonTask(task, result);
            const selectedForComparison = comparisonTaskIdSet.has(task.id);
            return (
              <li
                key={task.id}
                style={{
                  border: task.id === selectedTaskId ? "1px solid #0f172a" : "1px solid #cbd5e1",
                  borderRadius: 14,
                  display: "grid",
                  gap: 8,
                  padding: 12,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <strong>{TASK_OPTIONS[task.task_type as JobTaskType]?.label ?? task.task_type}</strong>
                  {renderStatus(task.status)}
                  {result ? renderEvidenceStatus(result.artifacts.evidence_status) : null}
                  {result ? renderFitSignal(result.artifacts.fit_signal) : null}
                </div>
                <div style={{ color: "#475569" }}>{result?.summary ?? input.target_role ?? "等待结构化 Job 结果生成"}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button type="button" onClick={() => setSelectedTaskId(task.id)}>
                    查看结果
                  </button>
                  {selectableComparisonTask ? (
                    <button type="button" onClick={() => handleToggleComparisonTask(task)}>
                      {selectedForComparison ? "移出短名单比较" : "加入短名单比较"}
                    </button>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ul>
      </SectionCard>

      <SectionCard title="结构化招聘结果" description="这里只保留当前任务最重要的岗位、判断、短名单和下一步。">
        {!selectedTask ? <p>请选择一个 Job 任务查看结果。</p> : null}
        {selectedTask && selectedResult ? (
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
            </div>

            <div>
              <h3 style={{ marginBottom: 8, marginTop: 0 }}>{selectedResult.title}</h3>
              <p style={{ margin: 0 }}>{selectedResult.summary}</p>
            </div>

            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
              {renderEvidenceStatus(selectedResult.artifacts.evidence_status)}
              {renderFitSignal(selectedResult.artifacts.fit_signal)}
            </div>

            <div style={{ display: "grid", gap: 8 }}>
              <div>
                <strong>岗位摘要：</strong> {selectedResult.review_brief.role_summary}
              </div>
              {selectedResult.review_brief.candidate_label ? (
                <div>
                  <strong>候选人：</strong> {selectedResult.review_brief.candidate_label}
                </div>
              ) : null}
              <div>
                <strong>必须技能</strong>
                {renderStringList(selectedResult.review_brief.must_have_skills, "当前没有必须技能列表。")}
              </div>
              <div>
                <strong>加分技能</strong>
                {renderStringList(selectedResult.review_brief.preferred_skills, "当前没有加分技能列表。")}
              </div>
            </div>

            <div style={{ display: "grid", gap: 8 }}>
              <div>
                <strong>推荐结论：</strong> {selectedResult.assessment.recommended_outcome}
              </div>
              <div>
                <strong>判断依据：</strong> {selectedResult.assessment.rationale}
              </div>
              <div>
                <strong>置信说明：</strong> {selectedResult.assessment.confidence_note}
              </div>
            </div>

            <div>
              <strong>比较候选人</strong>
              <div style={{ marginTop: 8 }}>{renderComparisonCandidates(selectedResult.comparison_candidates)}</div>
            </div>

            <div>
              <strong>短名单结果</strong>
              <div style={{ marginTop: 8 }}>{renderShortlist(selectedResult.shortlist)}</div>
            </div>

            <div>
              <strong>缺口</strong>
              {renderStringList(selectedResult.gaps, "当前没有额外缺口。")}
            </div>

            <div>
              <strong>下一步建议</strong>
              {renderStringList(selectedResult.next_steps, "当前没有额外下一步建议。")}
            </div>
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}