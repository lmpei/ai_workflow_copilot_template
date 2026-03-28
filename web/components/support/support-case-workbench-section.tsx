"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { getSupportCase, isApiClientError, listWorkspaceSupportCases } from "../../lib/api";
import type {
  SupportCaseContinuationDraft,
  SupportCaseEventRecord,
  SupportCaseRecord,
  SupportCaseStatus,
  SupportCaseSummaryRecord,
  SupportEvidenceStatus,
  SupportTaskType,
} from "../../lib/types";
import SectionCard from "../ui/section-card";

type SupportCaseWorkbenchSectionProps = {
  workspaceId: string;
  accessToken: string;
  onOpenTask: (taskId: string) => void;
  onContinueCase: (draft: SupportCaseContinuationDraft) => void;
};

const CASE_STATUS_LABELS: Record<SupportCaseStatus, string> = {
  open: "处理中",
  needs_customer_input: "待客户补充",
  ready_for_reply: "可直接回复",
  escalated: "已升级",
};

const EVIDENCE_STATUS_LABELS: Record<SupportEvidenceStatus, string> = {
  grounded_matches: "已命中依据",
  documents_only: "仅有文档",
  no_documents: "无文档",
};

const EVENT_KIND_LABELS: Record<string, string> = {
  case_created: "创建 case",
  follow_up: "继续跟进",
};

const TASK_TYPE_LABELS: Record<SupportTaskType, string> = {
  ticket_summary: "工单摘要",
  reply_draft: "回复草稿",
};

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

function renderCaseStatus(status: SupportCaseStatus) {
  const colorByStatus: Record<SupportCaseStatus, string> = {
    open: "#1d4ed8",
    needs_customer_input: "#92400e",
    ready_for_reply: "#166534",
    escalated: "#b91c1c",
  };
  return renderBadge(CASE_STATUS_LABELS[status], colorByStatus[status]);
}

function renderEvidenceStatus(status?: SupportEvidenceStatus | null) {
  if (!status) {
    return null;
  }
  const colorByStatus: Record<SupportEvidenceStatus, string> = {
    grounded_matches: "#166534",
    documents_only: "#92400e",
    no_documents: "#b91c1c",
  };
  return renderBadge(EVIDENCE_STATUS_LABELS[status], colorByStatus[status]);
}

function renderTaskType(taskType: SupportTaskType) {
  return renderBadge(TASK_TYPE_LABELS[taskType], "#334155");
}

function renderList(items: string[], emptyText: string) {
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

function buildContinuationDraft(supportCase: SupportCaseRecord): SupportCaseContinuationDraft | null {
  const continueFromTaskId = supportCase.action_loop.continue_from_task_id;
  if (!continueFromTaskId) {
    return null;
  }

  return {
    request_id: Date.now(),
    case_id: supportCase.id,
    case_title: supportCase.title,
    case_status: supportCase.status,
    continue_from_task_id: continueFromTaskId,
    suggested_task_type: supportCase.action_loop.suggested_task_type,
    status_guidance: supportCase.action_loop.status_guidance,
    suggested_follow_up_prompt: supportCase.action_loop.suggested_follow_up_prompt,
    customer_issue: supportCase.latest_case_brief.issue_summary,
    product_area: supportCase.latest_case_brief.product_area,
    severity: supportCase.latest_case_brief.severity,
    desired_outcome: supportCase.latest_case_brief.desired_outcome,
    reproduction_steps: supportCase.latest_case_brief.reproduction_steps,
  };
}

function renderEventCard(event: SupportCaseEventRecord, onOpenTask: (taskId: string) => void) {
  return (
    <li
      key={event.id}
      style={{
        border: "1px solid #cbd5e1",
        borderRadius: 12,
        display: "grid",
        gap: 8,
        padding: 12,
      }}
    >
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
        <strong>{event.title}</strong>
        {renderCaseStatus(event.case_status)}
        {renderEvidenceStatus(event.evidence_status)}
      </div>
      <div style={{ color: "#475569" }}>{event.summary}</div>
      <div style={{ color: "#64748b", fontSize: 13 }}>
        {new Date(event.created_at).toLocaleString()} · {EVENT_KIND_LABELS[event.event_kind] ?? event.event_kind}
      </div>
      {event.follow_up_notes ? (
        <div>
          <strong>跟进备注：</strong> {event.follow_up_notes}
        </div>
      ) : null}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        <button onClick={() => onOpenTask(event.task_id)} type="button">
          打开对应任务
        </button>
      </div>
    </li>
  );
}

export default function SupportCaseWorkbenchSection({
  workspaceId,
  accessToken,
  onOpenTask,
  onContinueCase,
}: SupportCaseWorkbenchSectionProps) {
  const [cases, setCases] = useState<SupportCaseSummaryRecord[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<SupportCaseRecord | null>(null);
  const [isLoadingCases, setIsLoadingCases] = useState(false);
  const [isLoadingSelectedCase, setIsLoadingSelectedCase] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadCases = useCallback(
    async (silent = false) => {
      if (!silent) {
        setIsLoadingCases(true);
      }
      try {
        const loadedCases = await listWorkspaceSupportCases(accessToken, workspaceId);
        setCases(loadedCases);
        setSelectedCaseId((currentSelectedCaseId) => {
          if (currentSelectedCaseId && loadedCases.some((item) => item.id === currentSelectedCaseId)) {
            return currentSelectedCaseId;
          }
          return loadedCases[0]?.id ?? null;
        });
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载 Support case 工作台");
      } finally {
        if (!silent) {
          setIsLoadingCases(false);
        }
      }
    },
    [accessToken, workspaceId],
  );

  const loadSelectedCase = useCallback(async () => {
    if (!selectedCaseId) {
      setSelectedCase(null);
      return;
    }

    setIsLoadingSelectedCase(true);
    try {
      setSelectedCase(await getSupportCase(accessToken, selectedCaseId));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载 Support case 详情");
    } finally {
      setIsLoadingSelectedCase(false);
    }
  }, [accessToken, selectedCaseId]);

  useEffect(() => {
    void loadCases();
  }, [loadCases]);

  useEffect(() => {
    void loadSelectedCase();
  }, [loadSelectedCase]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadCases(true);
      if (selectedCaseId) {
        void loadSelectedCase();
      }
    }, 4000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [loadCases, loadSelectedCase, selectedCaseId]);

  const selectedSummary = useMemo(
    () => cases.find((item) => item.id === selectedCaseId) ?? null,
    [cases, selectedCaseId],
  );

  return (
    <SectionCard
      title="Support case 工作台"
      description="这里沉淀的是持久化的 Support case。现在你不仅能看 case 历史，还能直接从 case 继续跟进。"
    >
      {errorMessage ? <p style={{ color: "#b91c1c", marginTop: 0 }}>{errorMessage}</p> : null}
      {isLoadingCases ? <p>正在加载 Support case 工作台...</p> : null}
      {!isLoadingCases && cases.length === 0 ? (
        <p>还没有持久化的 Support case。先运行一次 Support 任务，工作台就会自动生成对应 case。</p>
      ) : null}
      {cases.length > 0 ? (
        <div
          style={{
            display: "grid",
            gap: 16,
            gridTemplateColumns: "minmax(280px, 340px) minmax(0, 1fr)",
          }}
        >
          <div style={{ display: "grid", gap: 12 }}>
            {cases.map((supportCase) => (
              <div
                key={supportCase.id}
                style={{
                  border: supportCase.id === selectedCaseId ? "1px solid #0f172a" : "1px solid #cbd5e1",
                  borderRadius: 14,
                  display: "grid",
                  gap: 8,
                  padding: 14,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <strong>{supportCase.title}</strong>
                  {renderCaseStatus(supportCase.status)}
                  {renderEvidenceStatus(supportCase.latest_evidence_status)}
                </div>
                <div style={{ color: "#475569" }}>{supportCase.latest_summary}</div>
                <div style={{ color: "#334155", fontSize: 13 }}>
                  <strong>当前推进建议：</strong> {supportCase.action_loop.status_guidance}
                </div>
                <div style={{ color: "#334155", fontSize: 13 }}>
                  <strong>建议下一步：</strong> {TASK_TYPE_LABELS[supportCase.action_loop.suggested_task_type]}
                </div>
                <div style={{ color: "#334155", fontSize: 13 }}>
                  <strong>最新负责人：</strong> {supportCase.latest_recommended_owner ?? "待确定"}
                </div>
                <div style={{ color: "#64748b", fontSize: 12 }}>
                  事件数 {supportCase.event_count} · 更新于 {new Date(supportCase.updated_at).toLocaleString()}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button onClick={() => setSelectedCaseId(supportCase.id)} type="button">
                    打开 case
                  </button>
                  <button
                    disabled={!supportCase.action_loop.can_continue}
                    onClick={() => {
                      const draft = selectedCase && selectedCase.id === supportCase.id
                        ? buildContinuationDraft(selectedCase)
                        : null;
                      if (draft) {
                        onContinueCase(draft);
                        return;
                      }
                      void getSupportCase(accessToken, supportCase.id)
                        .then((fullCase) => {
                          const nextDraft = buildContinuationDraft(fullCase);
                          if (nextDraft) {
                            onContinueCase(nextDraft);
                          }
                        })
                        .catch(() => undefined);
                    }}
                    type="button"
                  >
                    继续这个 case
                  </button>
                  {supportCase.latest_task_id ? (
                    <button onClick={() => onOpenTask(supportCase.latest_task_id!)} type="button">
                      打开最新任务
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div>
            {!selectedSummary && !isLoadingSelectedCase ? <p>请选择一个 Support case 查看详情。</p> : null}
            {isLoadingSelectedCase && selectedCaseId ? <p>正在加载 case 详情...</p> : null}
            {selectedCase ? (
              <div style={{ display: "grid", gap: 16 }}>
                <div
                  style={{
                    backgroundColor: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: 16,
                    display: "grid",
                    gap: 10,
                    padding: 16,
                  }}
                >
                  <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <h3 style={{ margin: 0 }}>{selectedCase.title}</h3>
                    {renderCaseStatus(selectedCase.status)}
                    {renderEvidenceStatus(selectedCase.latest_evidence_status)}
                  </div>
                  <div>
                    <strong>Case ID：</strong> {selectedCase.id}
                  </div>
                  <div>
                    <strong>最新摘要：</strong> {selectedCase.latest_summary}
                  </div>
                  <div>
                    <strong>问题摘要：</strong> {selectedCase.latest_case_brief.issue_summary}
                  </div>
                  {selectedCase.latest_case_brief.product_area ? (
                    <div>
                      <strong>产品范围：</strong> {selectedCase.latest_case_brief.product_area}
                    </div>
                  ) : null}
                  <div>
                    <strong>建议负责人：</strong> {selectedCase.latest_triage.recommended_owner}
                  </div>
                  <div>
                    <strong>是否升级：</strong> {selectedCase.latest_triage.should_escalate ? "是" : "否"}
                  </div>
                  <div>
                    <strong>是否需人工复核：</strong> {selectedCase.latest_triage.needs_manual_review ? "是" : "否"}
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {renderTaskType(selectedCase.action_loop.suggested_task_type)}
                    {selectedCase.latest_task_id ? (
                      <button onClick={() => onOpenTask(selectedCase.latest_task_id!)} type="button">
                        打开最新任务结果
                      </button>
                    ) : null}
                    <button
                      disabled={!selectedCase.action_loop.can_continue}
                      onClick={() => {
                        const draft = buildContinuationDraft(selectedCase);
                        if (draft) {
                          onContinueCase(draft);
                        }
                      }}
                      type="button"
                    >
                      从这个 case 继续跟进
                    </button>
                  </div>
                </div>

                <div
                  style={{
                    border: "1px solid #cbd5e1",
                    borderRadius: 14,
                    display: "grid",
                    gap: 12,
                    padding: 14,
                  }}
                >
                  <strong>状态推进说明</strong>
                  <div>
                    <strong>当前状态：</strong> {CASE_STATUS_LABELS[selectedCase.status]}
                  </div>
                  <div>
                    <strong>为什么现在是这个状态：</strong> {selectedCase.action_loop.status_guidance}
                  </div>
                  <div>
                    <strong>建议下一步动作：</strong> {TASK_TYPE_LABELS[selectedCase.action_loop.suggested_task_type]}
                  </div>
                  {selectedCase.action_loop.suggested_follow_up_prompt ? (
                    <div>
                      <strong>建议在跟进备注里补充：</strong> {selectedCase.action_loop.suggested_follow_up_prompt}
                    </div>
                  ) : null}
                </div>

                <div
                  style={{
                    border: "1px solid #cbd5e1",
                    borderRadius: 14,
                    display: "grid",
                    gap: 12,
                    padding: 14,
                  }}
                >
                  <strong>当前升级交接包</strong>
                  <div>
                    <strong>升级原因：</strong> {selectedCase.latest_escalation_packet.escalation_reason}
                  </div>
                  <div>
                    <strong>交接说明：</strong> {selectedCase.latest_escalation_packet.handoff_note}
                  </div>
                  <div>
                    <strong>未解决问题</strong>
                    {renderList(selectedCase.latest_open_questions, "当前没有额外待补充的问题。")}
                  </div>
                  <div>
                    <strong>下一步建议</strong>
                    {renderList(selectedCase.latest_next_steps, "当前没有额外下一步建议。")}
                  </div>
                </div>

                <div>
                  <strong>Case 时间线</strong>
                  {selectedCase.events.length > 0 ? (
                    <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
                      {selectedCase.events.map((event) => renderEventCard(event, onOpenTask))}
                    </ul>
                  ) : (
                    <p>这个 case 还没有记录任何事件。</p>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
