
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
  JobHiringPacketLink,
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

type SeniorityOption = "" | "intern" | "junior" | "mid" | "senior" | "staff" | "principal";

const TASK_OPTIONS: Record<JobTaskType, { label: string; description: string; placeholder: string }> = {
  jd_summary: {
    label: "岗位摘要",
    description: "梳理目标岗位的核心要求、缺口和下一步评审建议。",
    placeholder: "示例：高级平台工程师，负责 Python API、服务稳定性和跨团队协作。",
  },
  resume_match: {
    label: "候选人匹配",
    description: "对单个候选人做 grounded 评审，或把多个已完成评审任务汇总成短名单。",
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

function parsePacketLink(result: JobTaskResult | null): JobHiringPacketLink | null {
  const metadata = result?.metadata;
  if (!isJsonObject(metadata) || !isJsonObject(metadata.job_hiring_packet)) {
    return null;
  }
  const link = metadata.job_hiring_packet;
  if (typeof link.packet_id !== "string" || typeof link.event_id !== "string" || typeof link.packet_status !== "string") {
    return null;
  }
  return link as JobHiringPacketLink;
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
    <span style={{ backgroundColor: `${color}14`, borderRadius: 999, color, display: "inline-block", fontSize: 12, fontWeight: 600, padding: "4px 10px" }}>
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

function formatRoleSnapshot(input: JobTaskInput): string {
  const parts: string[] = [];
  if (input.candidate_label) {
    parts.push(`候选人：${input.candidate_label}`);
  }
  if (input.seniority) {
    parts.push(`级别：${input.seniority}`);
  }
  if (input.must_have_skills.length > 0) {
    parts.push(`必备技能：${input.must_have_skills.slice(0, 3).join("、")}`);
  }
  if (input.comparison_task_ids.length > 0) {
    parts.push(`对比任务：${input.comparison_task_ids.length}`);
  }
  return parts.join(" | ");
}

function isSelectableComparisonTask(task: TaskRecord, result: JobTaskResult | null): boolean {
  if (task.status !== "completed" || task.task_type !== "resume_match" || result === null) {
    return false;
  }
  return result.input.comparison_task_ids.length === 0 && !result.shortlist;
}

function renderShortlist(shortlist?: JobShortlistResult) {
  if (!shortlist) {
    return null;
  }
  return (
    <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, display: "grid", gap: 12, padding: 16 }}>
      <strong>短名单结果</strong>
      <div>{shortlist.shortlist_summary}</div>
      {shortlist.comparison_notes ? <div><strong>对比备注：</strong>{shortlist.comparison_notes}</div> : null}
      <div style={{ display: "grid", gap: 12 }}>
        {shortlist.entries.map((entry) => (
          <div key={`${entry.task_id}-${entry.rank}`} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 12 }}>
            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
              <strong>#{entry.rank} {entry.candidate_label}</strong>
              {renderEvidenceStatus(entry.evidence_status)}
              {renderFitSignal(entry.fit_signal)}
            </div>
            <div style={{ marginTop: 8 }}><strong>建议：</strong>{entry.recommendation}</div>
            <div style={{ marginTop: 8 }}><strong>理由：</strong>{entry.rationale}</div>
            <div style={{ marginTop: 8 }}><strong>风险</strong>{renderStringList(entry.risks, "当前没有额外风险说明。")}</div>
            <div style={{ marginTop: 8 }}><strong>面试关注点</strong>{renderStringList(entry.interview_focus, "当前没有额外面试关注点。")}</div>
          </div>
        ))}
      </div>
      <div><strong>共享风险</strong>{renderStringList(shortlist.risks, "当前没有共享风险。")}</div>
      <div><strong>共享面试关注点</strong>{renderStringList(shortlist.interview_focus, "当前没有共享面试关注点。")}</div>
      <div><strong>Grounding 缺口</strong>{renderStringList(shortlist.gaps, "当前没有额外 grounding 缺口。")}</div>
    </div>
  );
}

function renderComparisonCandidates(candidates: JobComparisonCandidate[]) {
  if (candidates.length === 0) {
    return null;
  }
  return (
    <div>
      <strong>参与对比的候选人</strong>
      <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
        {candidates.map((candidate) => (
          <li key={candidate.task_id} style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}>
            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
              <strong>{candidate.candidate_label}</strong>
              {renderEvidenceStatus(candidate.evidence_status)}
              {renderFitSignal(candidate.fit_signal)}
            </div>
            <p style={{ color: "#475569", marginBottom: 0 }}>{candidate.summary}</p>
            {candidate.target_role ? <div style={{ marginTop: 8 }}><strong>目标岗位：</strong>{candidate.target_role}</div> : null}
            {candidate.highlights.length > 0 ? <div style={{ marginTop: 8 }}><strong>亮点：</strong>{candidate.highlights.join(" | ")}</div> : null}
            {candidate.evidence_ref_ids.length > 0 ? <div style={{ color: "#64748b", fontSize: 13, marginTop: 8 }}>证据引用：{candidate.evidence_ref_ids.join("、")}</div> : null}
            <div style={{ color: "#64748b", fontSize: 13, marginTop: 8 }}>来源任务：{candidate.task_id}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function JobAssistantPanel({ workspaceId }: JobAssistantPanelProps) {
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
      setSelectedTaskId((current) => current && loadedTasks.some((task) => task.id === current) ? current : (loadedTasks[0]?.id ?? null));
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

  const comparisonTaskIdSet = useMemo(() => new Set(comparisonTaskIds), [comparisonTaskIds]);
  const comparisonCandidates = useMemo(() => tasks.filter((task) => isSelectableComparisonTask(task, parseJobTaskResult(task))), [tasks]);
  const selectedComparisonTasks = useMemo(() => comparisonCandidates.filter((task) => comparisonTaskIdSet.has(task.id)), [comparisonCandidates, comparisonTaskIdSet]);
  const comparisonRole = useMemo(() => selectedComparisonTasks.map((task) => parseJobTaskInput(task, parseJobTaskResult(task)).target_role).find(Boolean) ?? null, [selectedComparisonTasks]);

  const selectedTask = useMemo(() => tasks.find((task) => task.id === selectedTaskId) ?? null, [selectedTaskId, tasks]);
  const selectedResult = useMemo(() => selectedTask ? parseJobTaskResult(selectedTask) : null, [selectedTask]);
  const selectedInput = useMemo(() => selectedTask ? parseJobTaskInput(selectedTask, selectedResult) : null, [selectedResult, selectedTask]);
  const packetLink = useMemo(() => parsePacketLink(selectedResult), [selectedResult]);
  const isShortlistMode = taskType === "resume_match" && comparisonTaskIds.length > 0;

  const handleToggleComparisonTask = useCallback((task: TaskRecord) => {
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
        setErrorMessage("一次短名单比较只能组合同一目标岗位的候选人评审任务。");
        return currentIds;
      }
      if (!targetRole && nextRole) {
        setTargetRole(nextRole);
      }
      return [...currentIds, task.id];
    });
  }, [comparisonRole, targetRole]);

  const handleCreateTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) {
      return;
    }
    const input: JsonObject = {
      must_have_skills: parseSkillList(mustHaveSkillsText),
      preferred_skills: parseSkillList(preferredSkillsText),
      comparison_task_ids: comparisonTaskIds,
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
      if (typeof window !== "undefined") {
        window.location.hash = `job-task-${createdTask.id}`;
      }
      setTargetRole("");
      setCandidateLabel("");
      setSeniority("");
      setMustHaveSkillsText("");
      setPreferredSkillsText("");
      setHiringContext("");
      setComparisonTaskIds([]);
      setComparisonNotes("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法启动 Job 任务");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Job Assistant">正在加载会话...</SectionCard>;
  }
  if (!session) {
    return <AuthRequired description="登录后才能运行 Job 任务并查看结构化招聘结果。" />;
  }

  return (
    <>
      <SectionCard title="Job Assistant" description="围绕岗位、候选人评审和短名单比较运行 grounded 招聘任务，并同步到持久化 hiring workbench。">
        {isLoadingWorkspace ? <p>正在加载工作区配置...</p> : null}
        {workspace ? <div style={{ display: "grid", gap: 8 }}><div><strong>工作区：</strong>{workspace.name}</div><div><strong>模块：</strong>{workspace.module_type}</div></div> : null}
        {workspace?.module_type && workspace.module_type !== "job" ? <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 12 }}>这个面板只对 Job 工作区开放。当前模块：{workspace.module_type}。</p> : null}
      </SectionCard>

      <SectionCard title="启动 Job 任务" description="先做单候选人 grounded 评审，再把多个已完成评审任务汇总成短名单。">
        <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12, maxWidth: 760 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>任务类型</span>
            <select value={taskType} onChange={(event) => { const nextTaskType = event.target.value as JobTaskType; setTaskType(nextTaskType); if (nextTaskType !== "resume_match") { setComparisonTaskIds([]); setComparisonNotes(""); } }} disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}>
              {availableTaskTypes.map((availableTaskType) => <option key={availableTaskType} value={availableTaskType}>{TASK_OPTIONS[availableTaskType].label}</option>)}
            </select>
          </label>
          <p style={{ color: "#475569", margin: 0 }}>{TASK_OPTIONS[taskType].description}</p>

          {selectedComparisonTasks.length > 0 ? <div style={{ backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 12, display: "grid", gap: 8, padding: 12 }}><div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}><strong>当前短名单比较集合</strong><button onClick={() => { setComparisonTaskIds([]); setComparisonNotes(""); setErrorMessage(null); }} type="button">清空</button></div><div><strong>已选任务：</strong>{selectedComparisonTasks.length}</div>{comparisonRole ? <div><strong>统一目标岗位：</strong>{comparisonRole}</div> : null}<ul style={{ margin: 0, paddingLeft: 20 }}>{selectedComparisonTasks.map((task) => { const result = parseJobTaskResult(task); const input = parseJobTaskInput(task, result); return <li key={task.id}>{input.candidate_label ?? result?.title ?? task.id} ({task.id})</li>; })}</ul></div> : null}

          <label style={{ display: "grid", gap: 6 }}><span>目标岗位</span><textarea value={targetRole} onChange={(event) => setTargetRole(event.target.value)} placeholder={TASK_OPTIONS[taskType].placeholder} rows={4} disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"} /></label>
          {taskType === "resume_match" && !isShortlistMode ? <label style={{ display: "grid", gap: 6 }}><span>候选人标签</span><input type="text" value={candidateLabel} onChange={(event) => setCandidateLabel(event.target.value)} placeholder="例如：候选人 A / Alex Chen" disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"} /></label> : null}

          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 6 }}><span>级别</span><select value={seniority} onChange={(event) => setSeniority(event.target.value as SeniorityOption)} disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"}>{SENIORITY_OPTIONS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}</select></label>
            <label style={{ display: "grid", gap: 6 }}><span>招聘背景</span><input type="text" value={hiringContext} onChange={(event) => setHiringContext(event.target.value)} placeholder="例如：当前缺一位能接住 API 稳定性与平台迁移的负责人" disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"} /></label>
          </div>
          <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 6 }}><span>必须技能</span><textarea value={mustHaveSkillsText} onChange={(event) => setMustHaveSkillsText(event.target.value)} placeholder={"每行一个，或用逗号分隔\nPython\nAPI 设计\n服务稳定性"} rows={5} disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"} /></label>
            <label style={{ display: "grid", gap: 6 }}><span>加分技能</span><textarea value={preferredSkillsText} onChange={(event) => setPreferredSkillsText(event.target.value)} placeholder={"每行一个，或用逗号分隔\n分布式系统\n跨团队协作\n招聘面试设计"} rows={5} disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"} /></label>
          </div>

          {isShortlistMode ? <label style={{ display: "grid", gap: 6 }}><span>对比备注</span><textarea value={comparisonNotes} onChange={(event) => setComparisonNotes(event.target.value)} placeholder="例如：优先关注 grounded 后端 ownership、短期入职可接手度和补材料风险。" rows={3} disabled={workspace?.module_type !== undefined && workspace.module_type !== "job"} /></label> : null}
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button type="submit" disabled={isCreating || (workspace?.module_type !== undefined && workspace.module_type !== "job")}>{isCreating ? "正在启动..." : isShortlistMode ? "生成候选人短名单" : "启动 Job 任务"}</button>
        </form>
      </SectionCard>

      <SectionCard title="Job 任务记录" description="任务列表每 2 秒自动刷新一次，方便你观察单候选评审如何沉淀进 hiring packet，再汇总成短名单。">
        {isLoadingTasks ? <p>正在加载 Job 任务...</p> : null}
        {!isLoadingTasks && tasks.length === 0 ? <p>还没有 Job 任务。先启动一个任务来生成结构化招聘结果。</p> : null}
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {tasks.map((task) => {
            const result = parseJobTaskResult(task);
            const input = parseJobTaskInput(task, result);
            const selectableComparisonTask = isSelectableComparisonTask(task, result);
            const selectedForComparison = comparisonTaskIdSet.has(task.id);
            return (
              <li key={task.id} style={{ border: task.id === selectedTaskId ? "1px solid #0f172a" : "1px solid #cbd5e1", borderRadius: 12, display: "grid", gap: 8, marginBottom: 12, padding: 12 }}>
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <strong>{TASK_OPTIONS[task.task_type as JobTaskType]?.label ?? task.task_type}</strong>
                  {renderStatus(task.status)}
                  {result ? renderEvidenceStatus(result.artifacts.evidence_status) : null}
                  {result ? renderFitSignal(result.artifacts.fit_signal) : null}
                  {result?.shortlist ? <span style={{ color: "#0369a1", fontSize: 12, fontWeight: 600 }}>短名单结果</span> : null}
                </div>
                <div style={{ color: "#475569" }}>{result?.summary ?? input.target_role ?? "等待结构化 Job 结果生成"}</div>
                <div style={{ color: "#64748b", fontSize: 13 }}>{formatRoleSnapshot(input)}</div>
                <div style={{ color: "#64748b", fontSize: 13 }}>任务 ID：{task.id} · 更新时间：{new Date(task.updated_at).toLocaleString()}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button type="button" onClick={() => { setSelectedTaskId(task.id); if (typeof window !== "undefined") { window.location.hash = `job-task-${task.id}`; } }}>查看结果</button>
                  {selectableComparisonTask ? <button type="button" onClick={() => handleToggleComparisonTask(task)}>{selectedForComparison ? "移出短名单比较" : "加入短名单比较"}</button> : null}
                </div>
              </li>
            );
          })}
        </ul>
      </SectionCard>

      <SectionCard title="结构化招聘结果" description="查看所选 Job 任务的岗位摘要、grounded findings、匹配判断、短名单结果以及与 hiring packet 的关联。">
        {!selectedTask ? <p>请选择一个 Job 任务查看结果。</p> : null}
        {selectedTask ? <div style={{ display: "grid", gap: 16 }}>
          <div style={{ display: "grid", gap: 6 }}>
            <div><strong>任务 ID：</strong>{selectedTask.id}</div>
            <div><strong>状态：</strong>{renderStatus(selectedTask.status)}</div>
            <div><strong>任务类型：</strong>{TASK_OPTIONS[selectedTask.task_type as JobTaskType]?.label ?? selectedTask.task_type}</div>
            {selectedInput?.target_role ? <div><strong>目标岗位：</strong>{selectedInput.target_role}</div> : null}
            {packetLink ? <div><strong>关联 hiring packet：</strong>{packetLink.packet_id} ({packetLink.packet_status})</div> : null}
          </div>
          {selectedTask.error_message ? <div><strong style={{ color: "#b91c1c" }}>任务错误</strong><p style={{ color: "#b91c1c", marginBottom: 0 }}>{selectedTask.error_message}</p></div> : null}
          {selectedResult ? <>
            <div><h3 style={{ marginBottom: 8, marginTop: 0 }}>{selectedResult.title}</h3><p style={{ margin: 0 }}>{selectedResult.summary}</p></div>
            <div style={{ display: "grid", gap: 12 }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, minWidth: 120, padding: 12 }}><div style={{ color: "#475569", fontSize: 12 }}>文档</div><div style={{ fontSize: 24, fontWeight: 700 }}>{selectedResult.artifacts.document_count}</div></div>
                <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, minWidth: 120, padding: 12 }}><div style={{ color: "#475569", fontSize: 12 }}>命中片段</div><div style={{ fontSize: 24, fontWeight: 700 }}>{selectedResult.artifacts.match_count}</div></div>
                <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, minWidth: 120, padding: 12 }}><div style={{ color: "#475569", fontSize: 12 }}>工具调用</div><div style={{ fontSize: 24, fontWeight: 700 }}>{selectedResult.artifacts.tool_call_ids.length}</div></div>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>{renderEvidenceStatus(selectedResult.artifacts.evidence_status)}{renderFitSignal(selectedResult.artifacts.fit_signal)}</div>
              <div><strong>建议下一步：</strong>{selectedResult.artifacts.recommended_next_step}</div>
            </div>
            <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, display: "grid", gap: 8, padding: 16 }}>
              <div style={{ alignItems: "center", display: "flex", gap: 8 }}><strong>评审摘要</strong>{renderEvidenceStatus(selectedResult.review_brief.evidence_status)}</div>
              <div><strong>岗位摘要：</strong>{selectedResult.review_brief.role_summary}</div>
              {selectedResult.review_brief.candidate_label ? <div><strong>候选人：</strong>{selectedResult.review_brief.candidate_label}</div> : null}
              {selectedResult.review_brief.seniority ? <div><strong>级别：</strong>{selectedResult.review_brief.seniority}</div> : null}
              <div><strong>必须技能：</strong>{selectedResult.review_brief.must_have_skills.length > 0 ? selectedResult.review_brief.must_have_skills.join("、") : "未指定"}</div>
              <div><strong>加分技能：</strong>{selectedResult.review_brief.preferred_skills.length > 0 ? selectedResult.review_brief.preferred_skills.join("、") : "未指定"}</div>
              {selectedResult.review_brief.hiring_context ? <div><strong>招聘背景：</strong>{selectedResult.review_brief.hiring_context}</div> : null}
              {selectedResult.review_brief.comparison_task_count > 0 ? <div><strong>对比任务数：</strong>{selectedResult.review_brief.comparison_task_count}</div> : null}
            </div>
            <div style={{ border: "1px solid #cbd5e1", borderRadius: 12, display: "grid", gap: 8, padding: 16 }}>
              <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}><strong>匹配判断</strong>{renderEvidenceStatus(selectedResult.assessment.evidence_status)}{renderFitSignal(selectedResult.assessment.fit_signal)}</div>
              <div><strong>建议结论：</strong>{selectedResult.assessment.recommended_outcome}</div>
              <div><strong>置信说明：</strong>{selectedResult.assessment.confidence_note}</div>
              <div><strong>判断理由：</strong>{selectedResult.assessment.rationale}</div>
            </div>
            {renderShortlist(selectedResult.shortlist)}
            {renderComparisonCandidates(selectedResult.comparison_candidates)}
            <div><strong>有依据的发现</strong>{selectedResult.findings.length > 0 ? <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>{selectedResult.findings.map((finding) => <li key={`${finding.title}-${finding.summary}`} style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}><div style={{ fontWeight: 600 }}>{finding.title}</div><p style={{ color: "#475569", marginBottom: 0 }}>{finding.summary}</p>{finding.evidence_ref_ids.length > 0 ? <div style={{ color: "#64748b", fontSize: 13, marginTop: 8 }}>证据引用：{finding.evidence_ref_ids.join("、")}</div> : null}</li>)}</ul> : <p>这次任务没有额外的 grounded 发现。</p>}</div>
            <div><strong>缺口</strong>{renderStringList(selectedResult.gaps, "当前没有额外缺口。")}</div>
            <div><strong>亮点</strong>{renderStringList(selectedResult.highlights, "当前没有额外亮点。")}</div>
            <div><strong>开放问题</strong>{renderStringList(selectedResult.open_questions, "当前没有额外开放问题。")}</div>
            <div><strong>下一步建议</strong>{renderStringList(selectedResult.next_steps, "当前没有额外下一步建议。")}</div>
            <div><strong>证据</strong>{selectedResult.evidence.length > 0 ? <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>{selectedResult.evidence.map((evidence) => <li key={evidence.ref_id} style={{ border: "1px solid #cbd5e1", borderRadius: 12, padding: 12 }}><div style={{ fontWeight: 600 }}>{evidence.title ?? evidence.kind}</div>{evidence.snippet ? <p style={{ color: "#475569", marginBottom: 8, marginTop: 8 }}>{evidence.snippet}</p> : null}<div style={{ color: "#64748b", fontSize: 13 }}>证据 ID：{evidence.ref_id}</div></li>)}</ul> : <p>当前没有额外证据项。</p>}</div>
          </> : <p>这个任务还没有产出完整的结构化 Job 结果。如果它仍在运行，等待下一轮刷新即可。</p>}
        </div> : null}
      </SectionCard>
    </>
  );
}
