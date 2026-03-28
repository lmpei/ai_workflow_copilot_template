"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { getJobHiringPacket, isApiClientError, listWorkspaceJobHiringPackets } from "../../lib/api";
import type {
  JobEvidenceStatus,
  JobFitSignal,
  JobHiringPacketEventRecord,
  JobHiringPacketRecord,
  JobHiringPacketStatus,
  JobHiringPacketSummaryRecord,
} from "../../lib/types";
import SectionCard from "../ui/section-card";

type JobHiringWorkbenchSectionProps = {
  workspaceId: string;
  accessToken: string;
  onOpenTask: (taskId: string) => void;
};

const PACKET_STATUS_LABELS: Record<JobHiringPacketStatus, string> = {
  collecting_materials: "补材料中",
  needs_alignment: "待对齐",
  review_ready: "可评审",
  shortlist_ready: "短名单已就绪",
};

const EVIDENCE_STATUS_LABELS: Record<JobEvidenceStatus, string> = {
  grounded_matches: "已命中依据",
  documents_only: "仅有文档",
  no_documents: "无文档",
};

const FIT_SIGNAL_LABELS: Record<JobFitSignal, string> = {
  grounded_match_found: "已发现 grounded 匹配",
  role_requirements_grounded: "岗位要求已对齐",
  insufficient_grounding: "依据不足",
  no_documents_available: "缺少材料",
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

function renderPacketStatus(status: JobHiringPacketStatus) {
  const colorByStatus: Record<JobHiringPacketStatus, string> = {
    collecting_materials: "#b91c1c",
    needs_alignment: "#92400e",
    review_ready: "#0369a1",
    shortlist_ready: "#166534",
  };
  return renderBadge(PACKET_STATUS_LABELS[status], colorByStatus[status]);
}

function renderEvidenceStatus(status?: JobEvidenceStatus | null) {
  if (!status) {
    return null;
  }
  const colorByStatus: Record<JobEvidenceStatus, string> = {
    grounded_matches: "#166534",
    documents_only: "#92400e",
    no_documents: "#b91c1c",
  };
  return renderBadge(EVIDENCE_STATUS_LABELS[status], colorByStatus[status]);
}

function renderFitSignal(status?: JobFitSignal | null) {
  if (!status) {
    return null;
  }
  const colorByStatus: Record<JobFitSignal, string> = {
    grounded_match_found: "#166534",
    role_requirements_grounded: "#0369a1",
    insufficient_grounding: "#92400e",
    no_documents_available: "#b91c1c",
  };
  return renderBadge(FIT_SIGNAL_LABELS[status], colorByStatus[status]);
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

function renderEventCard(event: JobHiringPacketEventRecord, onOpenTask: (taskId: string) => void) {
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
        {renderPacketStatus(event.packet_status)}
        {renderEvidenceStatus(event.evidence_status)}
        {renderFitSignal(event.fit_signal)}
      </div>
      <div style={{ color: "#475569" }}>{event.summary}</div>
      <div style={{ color: "#64748b", fontSize: 13 }}>
        {new Date(event.created_at).toLocaleString()} · {event.event_kind}
      </div>
      {event.candidate_label ? (
        <div>
          <strong>候选人：</strong> {event.candidate_label}
        </div>
      ) : null}
      {event.comparison_task_ids.length > 0 ? (
        <div>
          <strong>对比任务数：</strong> {event.comparison_task_ids.length}
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

export default function JobHiringWorkbenchSection({
  workspaceId,
  accessToken,
  onOpenTask,
}: JobHiringWorkbenchSectionProps) {
  const [packets, setPackets] = useState<JobHiringPacketSummaryRecord[]>([]);
  const [selectedPacketId, setSelectedPacketId] = useState<string | null>(null);
  const [selectedPacket, setSelectedPacket] = useState<JobHiringPacketRecord | null>(null);
  const [isLoadingPackets, setIsLoadingPackets] = useState(false);
  const [isLoadingPacket, setIsLoadingPacket] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadPackets = useCallback(
    async (silent = false) => {
      if (!silent) {
        setIsLoadingPackets(true);
      }
      try {
        const loadedPackets = await listWorkspaceJobHiringPackets(accessToken, workspaceId);
        setPackets(loadedPackets);
        setSelectedPacketId((currentSelectedPacketId) => {
          if (currentSelectedPacketId && loadedPackets.some((item) => item.id === currentSelectedPacketId)) {
            return currentSelectedPacketId;
          }
          return loadedPackets[0]?.id ?? null;
        });
      } catch (error) {
        setErrorMessage(isApiClientError(error) ? error.message : "无法加载 Job hiring workbench");
      } finally {
        if (!silent) {
          setIsLoadingPackets(false);
        }
      }
    },
    [accessToken, workspaceId],
  );

  const loadSelectedPacket = useCallback(async () => {
    if (!selectedPacketId) {
      setSelectedPacket(null);
      return;
    }

    setIsLoadingPacket(true);
    try {
      setSelectedPacket(await getJobHiringPacket(accessToken, selectedPacketId));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载 Job hiring packet 详情");
    } finally {
      setIsLoadingPacket(false);
    }
  }, [accessToken, selectedPacketId]);

  useEffect(() => {
    void loadPackets();
  }, [loadPackets]);

  useEffect(() => {
    void loadSelectedPacket();
  }, [loadSelectedPacket]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadPackets(true);
      if (selectedPacketId) {
        void loadSelectedPacket();
      }
    }, 4000);

    return () => window.clearInterval(intervalId);
  }, [loadPackets, loadSelectedPacket, selectedPacketId]);

  const selectedSummary = useMemo(
    () => packets.find((item) => item.id === selectedPacketId) ?? null,
    [packets, selectedPacketId],
  );

  return (
    <SectionCard
      title="Job hiring 工作台"
      description="这里沉淀的是持久化的招聘 packet。候选人评审、短名单结果和比较历史不会只留在一次性 task 输出里。"
    >
      {errorMessage ? <p style={{ color: "#b91c1c", marginTop: 0 }}>{errorMessage}</p> : null}
      {isLoadingPackets ? <p>正在加载 Job hiring 工作台...</p> : null}
      {!isLoadingPackets && packets.length === 0 ? (
        <p>还没有持久化的 Job hiring packet。先运行一次 Job 任务，工作台就会自动生成对应 packet。</p>
      ) : null}
      {packets.length > 0 ? (
        <div
          style={{
            display: "grid",
            gap: 16,
            gridTemplateColumns: "minmax(280px, 340px) minmax(0, 1fr)",
          }}
        >
          <div style={{ display: "grid", gap: 12 }}>
            {packets.map((packet) => (
              <div
                key={packet.id}
                style={{
                  border: packet.id === selectedPacketId ? "1px solid #0f172a" : "1px solid #cbd5e1",
                  borderRadius: 14,
                  display: "grid",
                  gap: 8,
                  padding: 14,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <strong>{packet.title}</strong>
                  {renderPacketStatus(packet.status)}
                  {renderEvidenceStatus(packet.latest_evidence_status)}
                </div>
                <div style={{ color: "#475569" }}>{packet.latest_summary}</div>
                <div style={{ color: "#334155", fontSize: 13 }}>
                  <strong>候选池：</strong> {packet.latest_candidate_labels.length > 0 ? packet.latest_candidate_labels.join("，") : "暂未沉淀候选人"}
                </div>
                <div style={{ color: "#64748b", fontSize: 12 }}>
                  比较历史 {packet.comparison_history_count} · 事件数 {packet.event_count} · 更新于 {new Date(packet.updated_at).toLocaleString()}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button onClick={() => setSelectedPacketId(packet.id)} type="button">
                    打开 packet
                  </button>
                  {packet.latest_task_id ? (
                    <button onClick={() => onOpenTask(packet.latest_task_id!)} type="button">
                      打开最新任务
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div>
            {!selectedSummary && !isLoadingPacket ? <p>请选择一个 Job hiring packet 查看详情。</p> : null}
            {isLoadingPacket && selectedPacketId ? <p>正在加载 packet 详情...</p> : null}
            {selectedPacket ? (
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
                    <h3 style={{ margin: 0 }}>{selectedPacket.title}</h3>
                    {renderPacketStatus(selectedPacket.status)}
                    {renderEvidenceStatus(selectedPacket.latest_evidence_status)}
                    {renderFitSignal(selectedPacket.latest_fit_signal)}
                  </div>
                  <div>
                    <strong>Packet ID：</strong> {selectedPacket.id}
                  </div>
                  {selectedPacket.target_role ? (
                    <div>
                      <strong>目标岗位：</strong> {selectedPacket.target_role}
                    </div>
                  ) : null}
                  {selectedPacket.seniority ? (
                    <div>
                      <strong>级别：</strong> {selectedPacket.seniority}
                    </div>
                  ) : null}
                  <div>
                    <strong>最新摘要：</strong> {selectedPacket.latest_summary}
                  </div>
                  <div>
                    <strong>最近建议结论：</strong> {selectedPacket.latest_recommended_outcome ?? "待判断"}
                  </div>
                  <div>
                    <strong>候选池：</strong> {selectedPacket.latest_candidate_labels.length > 0 ? selectedPacket.latest_candidate_labels.join("，") : "暂未沉淀候选人"}
                  </div>
                  {selectedPacket.latest_task_id ? (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      <button onClick={() => onOpenTask(selectedPacket.latest_task_id!)} type="button">
                        打开最新任务结果
                      </button>
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
                  <strong>当前招聘快照</strong>
                  <div>
                    <strong>岗位摘要：</strong> {selectedPacket.latest_review_brief.role_summary}
                  </div>
                  <div>
                    <strong>必须技能：</strong> {selectedPacket.latest_review_brief.must_have_skills.length > 0 ? selectedPacket.latest_review_brief.must_have_skills.join("，") : "暂未指定"}
                  </div>
                  <div>
                    <strong>加分技能：</strong> {selectedPacket.latest_review_brief.preferred_skills.length > 0 ? selectedPacket.latest_review_brief.preferred_skills.join("，") : "暂未指定"}
                  </div>
                  <div>
                    <strong>比较历史数：</strong> {selectedPacket.comparison_history_count}
                  </div>
                  <div>
                    <strong>下一步建议</strong>
                    {renderStringList(selectedPacket.latest_next_steps, "当前没有额外下一步建议。")}
                  </div>
                </div>

                {selectedPacket.latest_shortlist ? (
                  <div
                    style={{
                      border: "1px solid #cbd5e1",
                      borderRadius: 14,
                      display: "grid",
                      gap: 12,
                      padding: 14,
                    }}
                  >
                    <strong>当前短名单</strong>
                    <div>{selectedPacket.latest_shortlist.shortlist_summary}</div>
                    {selectedPacket.latest_shortlist.entries.map((entry) => (
                      <div
                        key={`${entry.task_id}-${entry.rank}`}
                        style={{
                          border: "1px solid #e2e8f0",
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
                ) : null}

                <div>
                  <strong>Packet 时间线</strong>
                  {selectedPacket.events.length > 0 ? (
                    <ul style={{ display: "grid", gap: 12, listStyle: "none", margin: "12px 0 0", padding: 0 }}>
                      {selectedPacket.events.map((event) => renderEventCard(event, onOpenTask))}
                    </ul>
                  ) : (
                    <p>这个 hiring packet 还没有记录任何事件。</p>
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

