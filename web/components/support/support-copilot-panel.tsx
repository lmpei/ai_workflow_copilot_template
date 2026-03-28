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
  SupportEscalationPacket,
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
    label: "工单摘要",
    description: "总结案例，提炼有依据的发现，并给出分诊建议。",
    placeholder: "示例：客户点击邮件链接后仍无法重置密码。",
  },
  reply_draft: {
    label: "回复草稿",
    description: "基于当前工作区知识库，生成一版面向客户的回复草稿。",
    placeholder: "示例：客户询问过期的密码重置链接该如何处理。",
  },
};

const SEVERITY_OPTIONS: Array<{
  value: "" | SupportSeverity;
  label: string;
}> = [
  { value: "", label: "未指定" },
  { value: "low", label: "低" },
  { value: "medium", label: "中" },
  { value: "high", label: "高" },
  { value: "critical", label: "紧急" },
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
    parent_task_id: normalizeOptionalString(source.parent_task_id),
    follow_up_notes: normalizeOptionalString(source.follow_up_notes),
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

function renderEvidenceStatusBadge(evidenceStatus: SupportEvidenceStatus) {
  const styles: Record<SupportEvidenceStatus, { label: string; color: string }> = {
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

function renderArtifactStats(artifacts: SupportArtifacts) {
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
      <div>
        <strong>依据状态：</strong> {renderEvidenceStatusBadge(artifacts.evidence_status)}
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
    segments.push(`严重级别：${input.severity}`);
  }
  if (input.desired_outcome) {
    segments.push(`目标：${input.desired_outcome}`);
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
        <p>这次案例没有产出有依据的发现。</p>
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
        <strong>案例摘要</strong>
        {renderEvidenceStatusBadge(caseBrief.evidence_status)}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>问题摘要：</strong> {caseBrief.issue_summary}
        </div>
        {caseBrief.product_area ? (
          <div>
            <strong>产品范围：</strong> {caseBrief.product_area}
          </div>
        ) : null}
        {caseBrief.severity ? (
          <div>
            <strong>严重级别：</strong> {caseBrief.severity}
          </div>
        ) : null}
        {caseBrief.desired_outcome ? (
          <div>
            <strong>期望结果：</strong> {caseBrief.desired_outcome}
          </div>
        ) : null}
        <div>
          <strong>复现步骤：</strong>
          {caseBrief.reproduction_steps.length > 0 ? (
            <ol style={{ marginBottom: 0, marginTop: 8, paddingLeft: 20 }}>
              {caseBrief.reproduction_steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          ) : (
            <p style={{ marginBottom: 0, marginTop: 8 }}>这次任务没有记录复现步骤。</p>
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
      <strong>回复草稿</strong>
      <div style={{ marginTop: 12 }}>
        <div>
          <strong>主题：</strong> {replyDraft.subject_line}
        </div>
        <p style={{ marginBottom: 12, marginTop: 12, whiteSpace: "pre-wrap" }}>{replyDraft.body}</p>
        <div style={{ color: "#475569" }}>
          <strong>置信说明：</strong> {replyDraft.confidence_note}
        </div>
      </div>
    </div>
  );
}

function renderEscalationPacket(escalationPacket: SupportEscalationPacket | undefined) {
  if (!escalationPacket) {
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
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
        <strong>升级交接包</strong>
        {renderEvidenceStatusBadge(escalationPacket.evidence_status)}
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>建议负责人：</strong> {escalationPacket.recommended_owner}
        </div>
        <div>
          <strong>是否需要人工复核：</strong> {escalationPacket.needs_manual_review ? "是" : "否"}
        </div>
        <div>
          <strong>是否升级：</strong> {escalationPacket.should_escalate ? "是" : "否"}
        </div>
        <div>
          <strong>升级原因：</strong> {escalationPacket.escalation_reason}
        </div>
        <div>
          <strong>案例总结：</strong> {escalationPacket.case_summary}
        </div>
        {escalationPacket.follow_up_notes ? (
          <div>
            <strong>跟进重点：</strong> {escalationPacket.follow_up_notes}
          </div>
        ) : null}
        <div>
          <strong>交接说明：</strong> {escalationPacket.handoff_note}
        </div>
        {escalationPacket.evidence_ref_ids.length > 0 ? (
          <div>
            <strong>证据引用：</strong> {escalationPacket.evidence_ref_ids.join(", ")}
          </div>
        ) : null}
      </div>

      {escalationPacket.findings.length > 0 ? (
        <div style={{ marginTop: 16 }}>
          <strong>证据关联发现</strong>
          <ul style={{ marginBottom: 0, marginTop: 8, paddingLeft: 20 }}>
            {escalationPacket.findings.map((finding) => (
              <li key={`${finding.title}-${finding.summary}`}>
                <strong>{finding.title}:</strong> {finding.summary}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {renderListSection({
        title: "未解决问题",
        items: escalationPacket.unresolved_questions,
        emptyText: "交接包里没有额外未解决问题。",
      })}

      {renderListSection({
        title: "建议下一步",
        items: escalationPacket.recommended_next_steps,
        emptyText: "交接包里没有额外下一步建议。",
      })}
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
  const [parentTaskId, setParentTaskId] = useState<string | null>(null);
  const [followUpNotes, setFollowUpNotes] = useState("");
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
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载支持任务");
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
  const parentTask = useMemo(
    () => tasks.find((task) => task.id === parentTaskId) ?? null,
    [parentTaskId, tasks],
  );
  const parentResult = useMemo(
    () => (parentTask ? parseSupportTaskResult(parentTask) : null),
    [parentTask],
  );
  const parentInput = useMemo(
    () => (parentTask ? parseSupportTaskInput(parentTask, parentResult) : null),
    [parentResult, parentTask],
  );

  const handleContinueFromTask = useCallback((task: TaskRecord) => {
    const result = parseSupportTaskResult(task);
    const input = parseSupportTaskInput(task, result);

    setParentTaskId(task.id);
    setTaskType(task.task_type as SupportTaskType);
    setCustomerIssue(input.customer_issue ?? "");
    setProductArea(input.product_area ?? "");
    setSeverity(input.severity ?? "");
    setDesiredOutcome(input.desired_outcome ?? "");
    setReproductionStepsText(formatReproductionSteps(input.reproduction_steps));
    setFollowUpNotes("");
    setSelectedTaskId(task.id);
  }, []);

  const handleClearFollowUp = useCallback(() => {
    setParentTaskId(null);
    setFollowUpNotes("");
  }, []);

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
    const normalizedFollowUpNotes = followUpNotes.trim();

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
    if (parentTaskId) {
      input.parent_task_id = parentTaskId;
    }
    if (normalizedFollowUpNotes) {
      input.follow_up_notes = normalizedFollowUpNotes;
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
      setParentTaskId(null);
      setFollowUpNotes("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法启动支持任务");
    } finally {
      setIsCreating(false);
    }
  };

  if (!isReady) {
    return <SectionCard title="Support Copilot">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能运行支持任务并查看 grounded 输出。" />;
  }

  return (
    <>
      <SectionCard
        title="Support Copilot"
        description="启动 grounded 支持案例流程，查看证据质量，并判断案例应由一线继续处理还是升级。"
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
                : "知识库、回复草稿、任务、评测"}
            </div>
          </div>
        ) : null}
        {workspace?.module_type && workspace.module_type !== "support" ? (
          <p style={{ color: "#b91c1c", marginBottom: 0, marginTop: 12 }}>
            这个面板只对 Support 工作区开放。当前模块： {workspace.module_type}.
          </p>
        ) : null}
      </SectionCard>

      <SectionCard
        title="启动支持案例"
        description="填写案例信息、明确你已掌握的上下文，再基于当前工作区知识库运行 grounded 支持任务。"
      >
        <form onSubmit={handleCreateTask} style={{ display: "grid", gap: 12, maxWidth: 760 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span>任务类型</span>
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

          {parentTask ? (
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
                <strong>继续跟进支持案例</strong>
                <button onClick={handleClearFollowUp} type="button">
                  清除
                </button>
              </div>
              <div>
                <strong>父任务：</strong> {parentTask.id}
              </div>
              <div>
                <strong>上一轮结果：</strong> {parentResult?.summary ?? "已完成的支持任务"}
              </div>
              {parentInput?.customer_issue ? (
                <div>
                  <strong>继承的问题：</strong> {parentInput.customer_issue}
                </div>
              ) : null}
            </div>
          ) : null}

          <label style={{ display: "grid", gap: 6 }}>
            <span>客户问题</span>
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
              <span>产品范围</span>
              <input
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
                onChange={(event) => setProductArea(event.target.value)}
                placeholder="认证、计费、管理后台等"
                type="text"
                value={productArea}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>严重级别</span>
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
            <span>期望结果</span>
            <input
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
              onChange={(event) => setDesiredOutcome(event.target.value)}
              placeholder="示例：恢复登录能力，同时避免客户走完整账号找回流程。"
              type="text"
              value={desiredOutcome}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span>复现步骤</span>
            <textarea
              disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
              onChange={(event) => setReproductionStepsText(event.target.value)}
              placeholder={"每行一个步骤\n1. 打开重置邮件\n2. 点击链接\n3. 页面提示已过期"}
              rows={5}
              value={reproductionStepsText}
            />
          </label>

          {parentTask ? (
            <label style={{ display: "grid", gap: 6 }}>
              <span>跟进备注</span>
              <textarea
                disabled={workspace?.module_type !== undefined && workspace.module_type !== "support"}
                onChange={(event) => setFollowUpNotes(event.target.value)}
                placeholder="示例：确认是否可以安全重发重置链接，以及影响范围是否已经扩大。"
                rows={3}
                value={followUpNotes}
              />
            </label>
          ) : null}

          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          <button
            disabled={
              isCreating || (workspace?.module_type !== undefined && workspace.module_type !== "support")
            }
            type="submit"
          >
            {isCreating ? "正在启动..." : "启动支持任务"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="支持任务记录"
        description="任务每 2 秒自动刷新一次，便于你观察案例分析如何收敛成 grounded 分诊结论。"
      >
        {isLoadingTasks ? <p>正在加载支持任务...</p> : null}
        {!isLoadingTasks && tasks.length === 0 ? <p>还没有支持任务。先启动一个任务来生成结构化案例流程。</p> : null}
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
                  {result?.summary ?? extractCustomerIssue(task, result) ?? "没有提供客户问题。"}
                </div>
                {issueSnapshot ? (
                  <div style={{ color: "#64748b", fontSize: 14, marginBottom: 6 }}>{issueSnapshot}</div>
                ) : null}
                <div>任务 ID：{task.id}</div>
                <div>更新时间：{new Date(task.updated_at).toLocaleString()}</div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <button onClick={() => setSelectedTaskId(task.id)} type="button">
                      查看结果
                    </button>
                    {task.status === "completed" ? (
                      <button onClick={() => handleContinueFromTask(task)} type="button">
                        继续跟进案例
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
        title="结构化案例结果"
        description="查看所选支持任务生成的案例摘要、有依据的发现、分诊决策和面向客户的回复草稿。"
      >
        {!selectedTask ? <p>请选择一个支持任务查看结果。</p> : null}
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
                <strong>任务类型：</strong> {TASK_OPTIONS[selectedTask.task_type as SupportTaskType]?.label ?? selectedTask.task_type}
              </div>
              {selectedResult?.lineage ? (
                <div>
                  <strong>延续自：</strong> {selectedResult.lineage.parent_title} ({selectedResult.lineage.parent_task_id})
                </div>
              ) : null}
              {selectedInput?.customer_issue ? (
                <div>
                  <strong>客户问题：</strong> {selectedInput.customer_issue}
                </div>
              ) : null}
              {selectedTask.status === "completed" ? (
                <div>
                  <button onClick={() => handleContinueFromTask(selectedTask)} type="button">
                    继续这个案例
                  </button>
                </div>
              ) : null}
            </div>

            {selectedTask.error_message ? (
              <div>
                <strong style={{ color: "#b91c1c" }}>支持任务错误</strong>
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
                {renderEscalationPacket(selectedResult.escalation_packet)}

                <div
                  style={{
                    border: "1px solid #cbd5e1",
                    borderRadius: 12,
                    padding: 16,
                  }}
                >
                  <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
                    <strong>分诊决策</strong>
                    {renderEvidenceStatusBadge(selectedResult.triage.evidence_status)}
                  </div>
                  <div style={{ display: "grid", gap: 8 }}>
                    <div>
                      <strong>建议负责人：</strong> {selectedResult.triage.recommended_owner}
                    </div>
                    <div>
                      <strong>是否需要人工复核：</strong> {selectedResult.triage.needs_manual_review ? "是" : "否"}
                    </div>
                    <div>
                      <strong>是否升级：</strong> {selectedResult.triage.should_escalate ? "是" : "否"}
                    </div>
                    <div>
                      <strong>判断依据：</strong> {selectedResult.triage.rationale}
                    </div>
                  </div>
                </div>

                {renderFindings(selectedResult.findings)}
                {renderReplyDraft(selectedResult.reply_draft)}

                {renderListSection({
                  title: "亮点摘要",
                  items: selectedResult.highlights,
                  emptyText: "这次运行没有生成亮点摘要。",
                })}

                {renderListSection({
                  title: "开放问题",
                  items: selectedResult.open_questions,
                  emptyText: "这次运行没有生成额外开放问题。",
                })}

                {renderListSection({
                  title: "下一步建议",
                  items: selectedResult.next_steps,
                  emptyText: "这次运行没有生成下一步建议。",
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
                              <Link href={`/workspaces/${workspaceId}/documents`}>打开知识库上下文</Link>
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>这次没有返回关联证据，通常说明工作区里的支持上下文或索引资料还不充分。</p>
                  )}
                </div>
              </>
            ) : (
              <p>
                这个任务还没有生成完成的结构化支持结果。如果它仍在运行，
                等待下一次自动刷新即可。
              </p>
            )}
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}
