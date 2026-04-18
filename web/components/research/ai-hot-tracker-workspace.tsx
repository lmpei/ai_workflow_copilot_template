"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  askAiHotTrackerFollowUp,
  deleteAiFrontierResearchRecord,
  generateAiHotTrackerReport,
  isApiClientError,
  listWorkspaceAiFrontierResearchRecords,
  saveAiFrontierResearchRecord,
  updateAiFrontierResearchRecord,
} from "../../lib/api";
import type {
  AiFrontierFollowUpEntryRecord,
  AiFrontierProjectCardRecord,
  AiFrontierReferenceSourceRecord,
  AiFrontierResearchOutputRecord,
  AiFrontierResearchRecord,
  ChatSource,
  JsonObject,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";

type AiHotTrackerWorkspaceProps = {
  workspaceId: string;
};

type FocusTarget = {
  context: string;
  label: string;
};

type ReportSession = {
  answerText?: string | null;
  conversationId?: string | null;
  dirty: boolean;
  followUps: AiFrontierFollowUpEntryRecord[];
  mode: "draft" | "saved";
  output: AiFrontierResearchOutputRecord;
  question: string;
  rawSources: ChatSource[];
  recordId?: string | null;
  sourceSet: JsonObject;
  sourceTraceId?: string | null;
  title: string;
  updatedAt: string;
};

const FOLLOW_UP_ACTIONS = [
  "这是什么意思",
  "为什么重要",
  "依据是什么",
  "接下来该看什么",
] as const;

const pageSurfaceStyle = {
  background:
    "radial-gradient(circle at 8% 12%, rgba(191, 219, 254, 0.52), transparent 28%), radial-gradient(circle at 88% 8%, rgba(224, 231, 255, 0.36), transparent 24%), #f8fbff",
  height: "100svh",
  overflow: "hidden",
} as const;

const shellStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 26,
  margin: "0 auto",
  maxWidth: 1680,
  height: "100svh",
  overflow: "hidden",
  padding: "32px 52px 24px",
} as const;

function formatRecordTime(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function buildReportTitle(output: AiFrontierResearchOutputRecord, at: string) {
  const firstEvent = output.events[0]?.title?.trim();
  if (firstEvent) {
    return firstEvent.slice(0, 80);
  }

  const firstProject = output.project_cards[0]?.title?.trim();
  if (firstProject) {
    return firstProject.slice(0, 80);
  }

  const firstTheme = output.themes[0]?.label?.trim();
  if (firstTheme) {
    return `${firstTheme} 追踪`.slice(0, 80);
  }

  return `AI 热点追踪 ${formatRecordTime(at)}`;
}

function recordToSession(record: AiFrontierResearchRecord): ReportSession {
  return {
    answerText: record.answer_text ?? null,
    conversationId: record.conversation_id ?? null,
    dirty: false,
    followUps: record.follow_ups ?? [],
    mode: "saved",
    output: record.output,
    question: record.question,
    rawSources: [],
    recordId: record.id,
    sourceSet: record.source_set ?? {},
    sourceTraceId: record.source_trace_id ?? null,
    title: record.title,
    updatedAt: record.updated_at,
  };
}

function buildDefaultFocus(session: ReportSession): FocusTarget {
  return {
    context: [session.output.frontier_summary, session.output.trend_judgment]
      .filter(Boolean)
      .join("\n\n"),
    label: "当前报告",
  };
}

function iconButtonStyle(active = false) {
  return {
    alignItems: "center",
    backgroundColor: active ? "rgba(15, 23, 42, 0.08)" : "transparent",
    border: "1px solid rgba(148, 163, 184, 0.22)",
    borderRadius: 999,
    color: "#0f172a",
    cursor: "pointer",
    display: "inline-flex",
    height: 40,
    justifyContent: "center",
    transition: "background-color 180ms ease, border-color 180ms ease",
    width: 40,
  } as const;
}

function moduleButtonStyle(kind: "primary" | "secondary") {
  return {
    backgroundColor: kind === "primary" ? "#0f172a" : "transparent",
    border: kind === "primary" ? "none" : "1px solid rgba(148, 163, 184, 0.32)",
    borderRadius: 999,
    boxSizing: "border-box",
    color: kind === "primary" ? "#ffffff" : "#0f172a",
    cursor: "pointer",
    display: "inline-flex",
    fontSize: 15,
    fontWeight: 800,
    height: 52,
    justifyContent: "center",
    minWidth: kind === "primary" ? 160 : 152,
    padding: kind === "primary" ? "0 26px" : "0 22px",
  } as const;
}

function rowStyle(isHovered: boolean) {
  return {
    alignItems: "center",
    backgroundColor: isHovered ? "rgba(148, 163, 184, 0.16)" : "transparent",
    borderBottom: "1px solid rgba(148, 163, 184, 0.18)",
    color: "#0f172a",
    cursor: "pointer",
    display: "grid",
    gap: 6,
    gridTemplateColumns: "minmax(0, 1fr) auto auto",
    padding: "16px 18px",
    transition: "background-color 160ms ease",
  } as const;
}

function drawerSurfaceStyle(open: boolean) {
  return {
    backgroundColor: "rgba(248, 251, 255, 0.98)",
    borderRight: "1px solid rgba(148, 163, 184, 0.18)",
    boxShadow: "18px 0 40px rgba(15, 23, 42, 0.08)",
    display: "grid",
    gap: 18,
    height: "100%",
    left: 0,
    maxWidth: "calc(100vw - 28px)",
    padding: "28px 18px 22px",
    position: "absolute",
    top: 0,
    transform: open ? "translateX(0)" : "translateX(-108%)",
    transition: "transform 220ms ease",
    width: 356,
  } as const;
}
function ReportBlock({
  active,
  children,
  onSelect,
}: {
  active: boolean;
  children: React.ReactNode;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      style={{
        backgroundColor: active ? "rgba(15, 23, 42, 0.04)" : "transparent",
        border: "none",
        borderRadius: 20,
        cursor: "pointer",
        display: "grid",
        gap: 10,
        padding: "12px 14px",
        textAlign: "left",
        transition: "background-color 160ms ease",
        width: "100%",
      }}
      type="button"
    >
      {children}
    </button>
  );
}

function SourceList({ items }: { items: AiFrontierReferenceSourceRecord[] }) {
  if (!items.length) {
    return null;
  }

  return (
    <div style={{ display: "grid", gap: 10 }}>
      {items.map((item, index) => (
        <a
          href={item.url}
          key={`${item.label}-${index}`}
          rel="noreferrer"
          style={{
            alignItems: "baseline",
            borderBottom: index === items.length - 1 ? "none" : "1px solid rgba(148, 163, 184, 0.18)",
            color: "#0f172a",
            display: "flex",
            gap: 10,
            justifyContent: "space-between",
            paddingBottom: index === items.length - 1 ? 0 : 10,
            textDecoration: "none",
          }}
          target="_blank"
        >
          <span style={{ fontWeight: 700 }}>{item.label}</span>
          <span style={{ color: "#64748b", fontSize: 12 }}>{item.source_kind}</span>
        </a>
      ))}
    </div>
  );
}

function ProjectItems({
  cards,
  onSelect,
  selectedLabel,
}: {
  cards: AiFrontierProjectCardRecord[];
  onSelect: (focus: FocusTarget) => void;
  selectedLabel: string;
}) {
  if (!cards.length) {
    return null;
  }

  return (
    <div style={{ display: "grid", gap: 14 }}>
      {cards.map((card, index) => {
        const focus = {
          context: [card.summary, card.why_it_matters, card.tags.join("、")].filter(Boolean).join("\n"),
          label: card.title,
        };
        const links = [
          card.official_url ? { href: card.official_url, label: "官网" } : null,
          card.repo_url ? { href: card.repo_url, label: "仓库" } : null,
          card.docs_url ? { href: card.docs_url, label: "文档" } : null,
        ].filter(Boolean) as Array<{ href: string; label: string }>;

        return (
          <ReportBlock
            active={selectedLabel === focus.label}
            key={`${card.title}-${index}`}
            onSelect={() => onSelect(focus)}
          >
            <div style={{ display: "grid", gap: 6 }}>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>{card.title}</strong>
              <span style={{ color: "#64748b", fontSize: 12 }}>{card.source_label}</span>
            </div>
            <p style={{ color: "#334155", lineHeight: 1.85, margin: 0 }}>{card.summary}</p>
            <p style={{ color: "#475569", lineHeight: 1.85, margin: 0 }}>{card.why_it_matters}</p>
            {links.length ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 14 }}>
                {links.map((link) => (
                  <a
                    href={link.href}
                    key={`${card.title}-${link.label}`}
                    rel="noreferrer"
                    style={{ color: "#0f172a", fontSize: 13, fontWeight: 800, textDecoration: "none" }}
                    target="_blank"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            ) : null}
          </ReportBlock>
        );
      })}
    </div>
  );
}

function RecordRow({
  active,
  confirmDelete,
  hovered,
  onDeleteConfirm,
  onDeleteRequest,
  onHoverChange,
  onOpen,
  onCancelDelete,
  record,
}: {
  active: boolean;
  confirmDelete: boolean;
  hovered: boolean;
  onCancelDelete: () => void;
  onDeleteConfirm: () => void;
  onDeleteRequest: () => void;
  onHoverChange: (hovered: boolean) => void;
  onOpen: () => void;
  record: AiFrontierResearchRecord;
}) {
  return (
    <div
      onMouseEnter={() => onHoverChange(true)}
      onMouseLeave={() => onHoverChange(false)}
      style={{
        ...rowStyle(active || hovered),
        borderLeft: active ? "2px solid #0f172a" : "2px solid transparent",
        paddingLeft: active ? 16 : 18,
      }}
    >
      <button
        onClick={onOpen}
        style={{
          backgroundColor: "transparent",
          border: "none",
          color: "#0f172a",
          cursor: "pointer",
          display: "grid",
          gap: 4,
          justifyItems: "start",
          padding: 0,
          textAlign: "left",
        }}
        type="button"
      >
        <strong style={{ fontSize: 15, fontWeight: 800 }}>{record.title}</strong>
        <span style={{ color: "#64748b", fontSize: 12 }}>{formatRecordTime(record.updated_at)}</span>
      </button>

      {confirmDelete ? (
        <div style={{ alignItems: "center", display: "flex", gap: 8, justifySelf: "end" }}>
          <button
            onClick={onCancelDelete}
            style={{
              backgroundColor: "transparent",
              border: "none",
              color: "#64748b",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 700,
              padding: 0,
            }}
            type="button"
          >
            取消
          </button>
          <button
            onClick={onDeleteConfirm}
            style={{
              backgroundColor: "transparent",
              border: "none",
              color: "#b91c1c",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 800,
              padding: 0,
            }}
            type="button"
          >
            删除
          </button>
        </div>
      ) : (
        <button
          aria-label="删除记录"
          onClick={onDeleteRequest}
          style={{
            backgroundColor: "transparent",
            border: "none",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: 16,
            fontWeight: 800,
            justifySelf: "end",
            lineHeight: 1,
            padding: 0,
          }}
          type="button"
        >
          🗑
        </button>
      )}
    </div>
  );
}
export default function AiHotTrackerWorkspace({ workspaceId }: AiHotTrackerWorkspaceProps) {
  const { session, isReady } = useAuthSession();
  const followUpScrollRef = useRef<HTMLDivElement | null>(null);
  const [records, setRecords] = useState<AiFrontierResearchRecord[]>([]);
  const [currentReport, setCurrentReport] = useState<ReportSession | null>(null);
  const [currentFocus, setCurrentFocus] = useState<FocusTarget | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [followUpInput, setFollowUpInput] = useState("");
  const [hoveredRecordId, setHoveredRecordId] = useState<string | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [isLoadingRecords, setIsLoadingRecords] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!session) {
      setRecords([]);
      return;
    }

    let cancelled = false;

    const loadRecords = async () => {
      setIsLoadingRecords(true);
      setErrorMessage(null);
      try {
        const loaded = await listWorkspaceAiFrontierResearchRecords(session.accessToken, workspaceId, 20);
        if (!cancelled) {
          setRecords([...loaded].sort((left, right) => right.updated_at.localeCompare(left.updated_at)));
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "暂时无法读取已保存的记录。");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingRecords(false);
        }
      }
    };

    void loadRecords();

    return () => {
      cancelled = true;
    };
  }, [session, workspaceId]);

  useEffect(() => {
    if (!currentReport) {
      setCurrentFocus(null);
      return;
    }

    setCurrentFocus(buildDefaultFocus(currentReport));
  }, [currentReport]);

  useEffect(() => {
    const node = followUpScrollRef.current;
    if (!node) {
      return;
    }

    node.scrollTop = node.scrollHeight;
  }, [currentReport?.followUps, isAsking]);

  const orderedRecords = useMemo(
    () => [...records].sort((left, right) => right.updated_at.localeCompare(left.updated_at)),
    [records],
  );
  const recentRecords = orderedRecords.slice(0, 3);
  const needsSave = Boolean(currentReport && (currentReport.mode === "draft" || currentReport.dirty));
  const displayTitle =
    currentReport && currentReport.title.startsWith("当前分析焦点")
      ? buildReportTitle(currentReport.output, currentReport.updatedAt)
      : currentReport?.title ?? "";
  const summaryText = currentReport?.output.frontier_summary.trim() ?? "";
  const trendParagraphs =
    currentReport?.output.trend_judgment
      .split(/\n+/)
      .map((item) => item.trim())
      .filter(Boolean) ?? [];
  const judgmentLead = trendParagraphs[0] ?? "";
  const judgmentNotes = trendParagraphs.slice(1);
  const goBack = () => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      window.history.back();
      return;
    }

    window.location.href = "/";
  };

  const ensureSafeReplace = () => {
    if (!needsSave) {
      return true;
    }

    return window.confirm("当前结果还没有保存。继续会覆盖当前内容。");
  };

  const openRecord = (record: AiFrontierResearchRecord) => {
    if (!ensureSafeReplace()) {
      return;
    }

    const nextSession = recordToSession(record);
    setCurrentReport(nextSession);
    setCurrentFocus(buildDefaultFocus(nextSession));
    setDrawerOpen(false);
    setDeleteConfirmId(null);
    setErrorMessage(null);
  };

  const runTracking = async () => {
    if (!session) {
      return;
    }
    if (!ensureSafeReplace()) {
      return;
    }

    setIsRunning(true);
    setErrorMessage(null);

    try {
      const response = await generateAiHotTrackerReport(session.accessToken, workspaceId);

      const nextReport: ReportSession = {
        answerText: null,
        conversationId: null,
        dirty: false,
        followUps: [],
        mode: "draft",
        output: response.output,
        question: response.question,
        rawSources: [],
        recordId: null,
        sourceSet: response.source_set,
        sourceTraceId: undefined,
        title: response.title || buildReportTitle(response.output, response.generated_at),
        updatedAt: response.generated_at,
      };

      setCurrentReport(nextReport);
      setCurrentFocus(buildDefaultFocus(nextReport));
      setDrawerOpen(false);
    } catch (error) {
      setErrorMessage(
        isApiClientError(error)
          ? error.message
          : error instanceof Error
            ? error.message
            : "暂时无法生成本轮热点，请稍后再试。",
      );
    } finally {
      setIsRunning(false);
    }
  };

  const saveReport = async () => {
    if (!session || !currentReport) {
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);

    try {
      const payload = {
        answer_text: currentReport.answerText ?? null,
        conversation_id: currentReport.conversationId ?? undefined,
        follow_ups: currentReport.followUps,
        output: currentReport.output,
        question: currentReport.question,
        source_set: currentReport.sourceSet,
        source_trace_id: currentReport.sourceTraceId ?? undefined,
        title: currentReport.title,
      };

      const record =
        currentReport.mode === "saved" && currentReport.recordId
          ? await updateAiFrontierResearchRecord(session.accessToken, currentReport.recordId, payload)
          : await saveAiFrontierResearchRecord(session.accessToken, workspaceId, payload);

      const nextRecords = [record, ...records.filter((item) => item.id !== record.id)].sort((left, right) =>
        right.updated_at.localeCompare(left.updated_at),
      );

      setRecords(nextRecords);
      setCurrentReport(recordToSession(record));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "保存失败，请稍后再试。");
    } finally {
      setIsSaving(false);
    }
  };

  const deleteRecord = async (recordId: string) => {
    if (!session) {
      return;
    }

    try {
      await deleteAiFrontierResearchRecord(session.accessToken, recordId);
      const nextRecords = records.filter((record) => record.id !== recordId);
      setRecords(nextRecords);
      setDeleteConfirmId(null);

      if (currentReport?.recordId === recordId) {
        setCurrentReport(null);
        setCurrentFocus(null);
      }
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "删除失败，请稍后再试。");
    }
  };

  const askFollowUp = async (presetQuestion?: string) => {
    if (!session || !currentReport) {
      return;
    }

    const userQuestion = (presetQuestion ?? followUpInput).trim();
    if (!userQuestion) {
      return;
    }

    setIsAsking(true);
    setErrorMessage(null);

    try {
      const scopedQuestion =
        currentFocus && currentFocus.label !== "当前报告"
          ? `围绕「${currentFocus.label}」：${userQuestion}`
          : userQuestion;

      const response = await askAiHotTrackerFollowUp(session.accessToken, workspaceId, {
        follow_up_question: scopedQuestion,
        prior_follow_ups: currentReport.followUps,
        report_answer: currentReport.answerText ?? null,
        report_output: currentReport.output,
        report_question: currentReport.question,
        source_set: currentReport.sourceSet,
      });

      setCurrentReport((previous) =>
        previous
          ? {
              ...previous,
              dirty: previous.mode === "saved" ? true : previous.dirty,
              followUps: [...previous.followUps, response.follow_up],
              updatedAt: new Date().toISOString(),
            }
          : previous,
      );
      setFollowUpInput("");
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "这次追问没有成功，请稍后再试。");
    } finally {
      setIsAsking(false);
    }
  };

  if (!isReady) {
    return <div style={{ padding: 40 }}>正在进入 AI 热点追踪…</div>;
  }

  if (!session) {
    return <AuthRequired description="登录后才可以进入 AI 热点追踪。" />;
  }

  return (
    <div style={pageSurfaceStyle}>
      <div style={shellStyle}>
        {currentReport ? (
          <header
            style={{
              alignItems: "center",
              display: "flex",
              justifyContent: "space-between",
              minHeight: 40,
            }}
          >
            <div style={{ alignItems: "center", display: "flex", gap: 14 }}>
              <button
                onClick={goBack}
                style={{
                  backgroundColor: "transparent",
                  border: "none",
                  color: "#475569",
                  cursor: "pointer",
                  fontSize: 14,
                  fontWeight: 700,
                  padding: 0,
                }}
                type="button"
              >
                返回
              </button>
              <button
                aria-label="所有记录"
                onClick={() => setDrawerOpen(true)}
                style={iconButtonStyle(drawerOpen)}
                title="所有记录"
                type="button"
              >
                <span style={{ display: "grid", gap: 3, width: 14 }}>
                  <span style={{ backgroundColor: "#0f172a", borderRadius: 999, height: 2, width: "100%" }} />
                  <span style={{ backgroundColor: "#0f172a", borderRadius: 999, height: 2, width: "100%" }} />
                  <span style={{ backgroundColor: "#0f172a", borderRadius: 999, height: 2, width: "100%" }} />
                </span>
              </button>
              <strong style={{ color: "#0f172a", fontSize: 16, letterSpacing: "0.08em" }}>AI 热点追踪</strong>
            </div>
          </header>
        ) : null}

        {errorMessage ? (
          <div
            style={{
              backgroundColor: "rgba(185, 28, 28, 0.06)",
              border: "1px solid rgba(185, 28, 28, 0.14)",
              borderRadius: 18,
              color: "#991b1b",
              padding: "14px 16px",
            }}
          >
            {errorMessage}
          </div>
        ) : null}
        {!currentReport ? (
          <section
            style={{
              alignContent: recentRecords.length ? "start" : "center",
              display: "grid",
              flex: 1,
              gap: 34,
              justifyItems: "center",
              minHeight: 0,
              overflow: "hidden",
              padding: recentRecords.length ? "28px 0 8px" : "0",
            }}
          >
            <div
              style={{
                display: "grid",
                gap: 28,
                justifyItems: "center",
                justifySelf: "center",
                maxWidth: 920,
                paddingInline: 24,
                paddingTop: recentRecords.length ? 24 : 0,
                textAlign: "center",
                width: "min(100%, 920px)",
              }}
            >
              <div style={{ display: "grid", gap: 14, justifyItems: "center" }}>
                <span
                  style={{
                    background: "linear-gradient(135deg, #0f172a 0%, #334155 48%, #2563eb 100%)",
                    backgroundClip: "text",
                    color: "transparent",
                    fontSize: "clamp(44px, 6vw, 72px)",
                    fontWeight: 800,
                    letterSpacing: "-0.04em",
                    lineHeight: 0.92,
                    textShadow: "0 10px 26px rgba(37, 99, 235, 0.08)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  AI热点
                </span>
                <strong
                  style={{
                    color: "#0f172a",
                    fontSize: "clamp(24px, 3.2vw, 40px)",
                    fontWeight: 700,
                    lineHeight: 1.08,
                    letterSpacing: "-0.03em",
                    maxWidth: 760,
                  }}
                >
                  最先看见变化的人，最先占据优势
                </strong>
              </div>

              <button
                disabled={isRunning}
                onClick={runTracking}
                style={{
                  ...moduleButtonStyle("primary"),
                  boxShadow: "0 20px 40px rgba(15, 23, 42, 0.14)",
                  fontSize: 18,
                  height: 64,
                  minWidth: 192,
                  marginTop: 6,
                }}
                type="button"
              >
                {isRunning ? "整理中…" : "获取热点"}
              </button>
            </div>

            {recentRecords.length ? (
              <section
                style={{
                  alignSelf: "end",
                  borderTop: "1px solid rgba(148, 163, 184, 0.18)",
                  display: "grid",
                  gap: 12,
                  minHeight: 0,
                  overflow: "hidden",
                  paddingTop: 14,
                }}
              >
                <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
                  <strong style={{ color: "#0f172a", fontSize: 15 }}>最近记录</strong>
                  <button
                    onClick={() => setDrawerOpen(true)}
                    style={{
                      backgroundColor: "transparent",
                      border: "none",
                      color: "#64748b",
                      cursor: "pointer",
                      fontSize: 13,
                      fontWeight: 700,
                      padding: 0,
                    }}
                    type="button"
                  >
                    所有记录
                  </button>
                </div>

                <div
                  style={{
                    border: "1px solid rgba(148, 163, 184, 0.18)",
                    borderRadius: 28,
                    overflow: "hidden",
                  }}
                >
                  {recentRecords.map((record) => (
                    <RecordRow
                      active={false}
                      confirmDelete={deleteConfirmId === record.id}
                      hovered={hoveredRecordId === record.id}
                      key={record.id}
                      onCancelDelete={() => setDeleteConfirmId(null)}
                      onDeleteConfirm={() => void deleteRecord(record.id)}
                      onDeleteRequest={() => setDeleteConfirmId(record.id)}
                      onHoverChange={(hovered) => setHoveredRecordId(hovered ? record.id : null)}
                      onOpen={() => openRecord(record)}
                      record={record}
                    />
                  ))}
                </div>
              </section>
            ) : null}
          </section>
        ) : (
          <section
            style={{
              alignItems: "stretch",
              display: "grid",
              flex: 1,
              gap: 20,
              gridTemplateColumns: "minmax(0, 1.42fr) minmax(380px, 0.86fr)",
              height: "100%",
              minHeight: 0,
              overflow: "hidden",
              paddingTop: 6,
            }}
          >
            <section
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.88)",
                border: "1px solid rgba(148, 163, 184, 0.16)",
                borderRadius: 28,
                display: "grid",
                gridTemplateRows: "minmax(0, 1fr) auto",
                height: "100%",
                minHeight: 0,
                overflow: "hidden",
                padding: "24px 26px 16px",
              }}
            >
              <div
                className="ai-hot-tracker-report-scroll"
                style={{
                  display: "grid",
                  gap: 24,
                  minHeight: 0,
                  overflowY: "auto",
                  paddingRight: 6,
                }}
              >
                <div style={{ display: "grid", gap: 16, maxWidth: 760 }}>
                  <strong style={{ color: "#0f172a", fontSize: "clamp(34px, 3.5vw, 52px)", lineHeight: 0.98 }}>
                    {displayTitle}
                  </strong>
                  <ReportBlock
                    active={currentFocus?.label === "摘要" || currentFocus?.label === "当前报告"}
                    onSelect={() =>
                      setCurrentFocus({
                        context: currentReport.output.frontier_summary,
                        label: "摘要",
                      })
                    }
                  >
                    <p style={{ color: "#0f172a", fontSize: 21, fontWeight: 700, lineHeight: 1.62, margin: 0 }}>
                      {summaryText}
                    </p>
                  </ReportBlock>
                  {currentReport.output.themes.length ? (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {currentReport.output.themes.map((theme) => (
                        <button
                          key={theme.label}
                          onClick={() =>
                            setCurrentFocus({
                              context: [theme.label, theme.summary].filter(Boolean).join("\n"),
                              label: theme.label,
                            })
                          }
                          style={{
                            backgroundColor:
                              currentFocus?.label === theme.label ? "rgba(15, 23, 42, 0.08)" : "rgba(226, 232, 240, 0.52)",
                            border: "none",
                            borderRadius: 999,
                            color: "#0f172a",
                            cursor: "pointer",
                            fontSize: 12,
                            fontWeight: 800,
                            padding: "9px 12px",
                          }}
                          type="button"
                        >
                          {theme.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>

                {judgmentLead ? (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.1em" }}>判断</span>
                    <ReportBlock
                      active={currentFocus?.label === "判断"}
                      onSelect={() =>
                        setCurrentFocus({
                          context: currentReport.output.trend_judgment,
                          label: "判断",
                        })
                      }
                    >
                      <div
                        style={{
                          borderLeft: "3px solid rgba(15, 23, 42, 0.32)",
                          display: "grid",
                          gap: judgmentNotes.length ? 10 : 0,
                          paddingLeft: 18,
                        }}
                      >
                        <p style={{ color: "#0f172a", fontSize: 21, fontWeight: 700, lineHeight: 1.68, margin: 0 }}>
                          {judgmentLead}
                        </p>
                        {judgmentNotes.length ? (
                          <div style={{ display: "grid", gap: 10 }}>
                            {judgmentNotes.map((note, index) => (
                              <p
                                key={`${note.slice(0, 16)}-${index}`}
                                style={{ color: "#475569", fontSize: 15, lineHeight: 1.78, margin: 0 }}
                              >
                                {note}
                              </p>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    </ReportBlock>
                  </section>
                ) : null}
                {currentReport.output.events.length ? (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.1em" }}>本轮变化</span>
                    <div style={{ display: "grid", gap: 12 }}>
                      {currentReport.output.events.map((event, index) => {
                        const focus = {
                          context: [event.summary, event.significance].filter(Boolean).join("\n"),
                          label: event.title,
                        };
                        return (
                          <ReportBlock
                            active={currentFocus?.label === focus.label}
                            key={`${event.title}-${index}`}
                            onSelect={() => setCurrentFocus(focus)}
                          >
                            <div
                              style={{
                                display: "grid",
                                gap: 8,
                                gridTemplateColumns: "18px minmax(0, 1fr)",
                              }}
                            >
                              <div
                                style={{
                                  alignItems: "center",
                                  display: "grid",
                                  justifyItems: "center",
                                  paddingTop: 6,
                                }}
                              >
                                <span
                                  style={{
                                    backgroundColor: "#0f172a",
                                    borderRadius: 999,
                                    display: "block",
                                    height: 8,
                                    width: 8,
                                  }}
                                />
                              </div>
                              <div style={{ display: "grid", gap: 6 }}>
                                <strong style={{ color: "#0f172a", fontSize: 19, lineHeight: 1.35 }}>{event.title}</strong>
                                <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.74, margin: 0 }}>{event.summary}</p>
                                <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.72, margin: 0 }}>{event.significance}</p>
                              </div>
                            </div>
                          </ReportBlock>
                        );
                      })}
                    </div>
                  </section>
                ) : null}

                {currentReport.output.project_cards.length ? (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.1em" }}>项目与框架</span>
                    <ProjectItems
                      cards={currentReport.output.project_cards}
                      onSelect={setCurrentFocus}
                      selectedLabel={currentFocus?.label ?? ""}
                    />
                  </section>
                ) : null}

                {currentReport.output.reference_sources.length ? (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.1em" }}>原始链接</span>
                    <SourceList items={currentReport.output.reference_sources} />
                  </section>
                ) : null}
              </div>

              <div
                style={{
                  alignItems: "center",
                  backdropFilter: "blur(14px)",
                  backgroundColor: "rgba(248, 251, 255, 0.88)",
                  borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                  bottom: 0,
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: "auto",
                  paddingTop: 14,
                }}
              >
                <div style={{ color: "#64748b", fontSize: 13 }}>
                  {currentReport.mode === "saved" && !currentReport.dirty ? "这份报告已保存" : "这份报告默认不会自动保存"}
                </div>

                <div style={{ alignItems: "center", display: "flex", gap: 12 }}>
                  {needsSave ? (
                    <button
                      disabled={isSaving}
                      onClick={() => void saveReport()}
                      style={moduleButtonStyle("secondary")}
                      type="button"
                    >
                      {isSaving ? "保存中…" : "保存"}
                    </button>
                  ) : null}
                  <button
                    disabled={isRunning}
                    onClick={() => void runTracking()}
                    style={moduleButtonStyle("primary")}
                    type="button"
                  >
                    {isRunning ? "整理中…" : "获取新一轮"}
                  </button>
                </div>
              </div>
            </section>

            <aside
              style={{
                backdropFilter: "blur(18px)",
                backgroundColor: "rgba(255, 255, 255, 0.88)",
                border: "1px solid rgba(148, 163, 184, 0.16)",
                borderRadius: 28,
                boxSizing: "border-box",
                display: "grid",
                gap: 14,
                gridTemplateRows: "auto auto minmax(0, 1fr) auto",
                height: "100%",
                minWidth: 0,
                overflow: "hidden",
                padding: "22px 18px 16px",
                width: "100%",
              }}
            >
              <div style={{ display: "grid", gap: 2 }}>
                <span
                  style={{
                    color: "#64748b",
                    fontSize: 12,
                    fontWeight: 800,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                  }}
                >
                  追问
                </span>
              </div>

              <div
                className="ai-hot-tracker-follow-up-scroll"
                style={{
                  display: "grid",
                  gap: 14,
                  minHeight: 0,
                  overflowY: "auto",
                  paddingBottom: 6,
                  paddingRight: 4,
                }}
              >
                <div
                  style={{
                    borderBottom: "1px solid rgba(148, 163, 184, 0.16)",
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 8,
                    paddingBottom: 10,
                  }}
                >
                  {FOLLOW_UP_ACTIONS.map((item) => (
                    <button
                      disabled={isAsking}
                      key={item}
                      onClick={() => void askFollowUp(item)}
                      style={{
                        backgroundColor: "rgba(241, 245, 249, 0.9)",
                        border: "1px solid rgba(148, 163, 184, 0.16)",
                        borderRadius: 999,
                        color: "#0f172a",
                        cursor: "pointer",
                        fontSize: 11,
                        fontWeight: 800,
                        padding: "7px 10px",
                      }}
                      type="button"
                    >
                      {item}
                    </button>
                  ))}
                </div>

                <div ref={followUpScrollRef} style={{ display: "grid", gap: 14, minHeight: 0 }}>
                {currentReport.followUps.length ? (
                  currentReport.followUps.map((entry, index) => (
                    <div key={`${entry.question}-${index}`} style={{ display: "grid", gap: 10 }}>
                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <div
                          style={{
                            backgroundColor: "#0f172a",
                            borderRadius: "20px 20px 6px 20px",
                            color: "#f8fbff",
                            lineHeight: 1.66,
                            maxWidth: "88%",
                            padding: "11px 13px",
                            whiteSpace: "pre-wrap",
                          }}
                        >
                          {entry.question}
                        </div>
                      </div>
                      <div style={{ display: "flex", justifyContent: "flex-start" }}>
                        <div
                          style={{
                            backgroundColor: "rgba(241, 245, 249, 0.92)",
                            border: "1px solid rgba(148, 163, 184, 0.14)",
                            borderRadius: "20px 20px 20px 6px",
                            color: "#334155",
                            lineHeight: 1.74,
                            maxWidth: "92%",
                            padding: "11px 13px",
                            whiteSpace: "pre-wrap",
                          }}
                        >
                          {entry.answer}
                        </div>
                      </div>
                    </div>
                  ))
                ) : null}

                {isAsking ? (
                  <div style={{ display: "flex", justifyContent: "flex-start" }}>
                    <div
                      style={{
                        backgroundColor: "rgba(241, 245, 249, 0.92)",
                        border: "1px solid rgba(148, 163, 184, 0.14)",
                        borderRadius: "20px 20px 20px 6px",
                        color: "#64748b",
                        lineHeight: 1.8,
                        maxWidth: "78%",
                        padding: "12px 14px",
                      }}
                    >
                      正在整理回答…
                    </div>
                  </div>
                ) : null}
                </div>
              </div>

              <div
                style={{
                  borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                  display: "grid",
                  gap: 10,
                  paddingBottom: 2,
                  paddingTop: 14,
                }}
              >
                <textarea
                  onChange={(event) => setFollowUpInput(event.target.value)}
                  placeholder="继续追问"
                  rows={3}
                  style={{
                    backgroundColor: "rgba(248, 250, 252, 0.92)",
                    border: "1px solid rgba(148, 163, 184, 0.18)",
                    borderRadius: 18,
                    boxSizing: "border-box",
                    color: "#0f172a",
                    fontFamily: "inherit",
                    fontSize: 15,
                    lineHeight: 1.8,
                    maxWidth: "100%",
                    padding: "14px 16px",
                    resize: "none",
                    width: "100%",
                  }}
                  value={followUpInput}
                />
                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <button
                    disabled={isAsking || !followUpInput.trim()}
                    onClick={() => void askFollowUp()}
                    style={moduleButtonStyle("primary")}
                    type="button"
                  >
                    {isAsking ? "追问中…" : "发送"}
                  </button>
                </div>
              </div>
            </aside>
          </section>
        )}

        <div
          onClick={() => setDrawerOpen(false)}
          style={{
            backgroundColor: drawerOpen ? "rgba(15, 23, 42, 0.14)" : "transparent",
            inset: 0,
            pointerEvents: drawerOpen ? "auto" : "none",
            position: "fixed",
            transition: "background-color 200ms ease",
            zIndex: 60,
          }}
        >
          <aside onClick={(event) => event.stopPropagation()} style={drawerSurfaceStyle(drawerOpen)}>
            <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
              <div style={{ display: "grid", gap: 4 }}>
                <strong style={{ color: "#0f172a", fontSize: 22 }}>所有记录</strong>
                <span style={{ color: "#64748b", fontSize: 12 }}>
                  {orderedRecords.length ? `${orderedRecords.length} 条已保存记录` : "还没有保存任何记录"}
                </span>
              </div>
              <button aria-label="关闭" onClick={() => setDrawerOpen(false)} style={iconButtonStyle(false)} type="button">
                ×
              </button>
            </div>

            <div
              style={{
                border: "1px solid rgba(148, 163, 184, 0.18)",
                borderRadius: 24,
                overflow: "hidden",
              }}
            >
              {isLoadingRecords ? (
                <div style={{ color: "#64748b", padding: 18 }}>正在读取记录…</div>
              ) : orderedRecords.length ? (
                orderedRecords.map((record) => (
                  <RecordRow
                    active={currentReport?.recordId === record.id}
                    confirmDelete={deleteConfirmId === record.id}
                    hovered={hoveredRecordId === record.id}
                    key={record.id}
                    onCancelDelete={() => setDeleteConfirmId(null)}
                    onDeleteConfirm={() => void deleteRecord(record.id)}
                    onDeleteRequest={() => setDeleteConfirmId(record.id)}
                    onHoverChange={(hovered) => setHoveredRecordId(hovered ? record.id : null)}
                    onOpen={() => openRecord(record)}
                    record={record}
                  />
                ))
              ) : (
                <div style={{ color: "#64748b", lineHeight: 1.8, padding: 18 }}>保存之后的报告会出现在这里。</div>
              )}
            </div>
          </aside>
        </div>
        <style jsx global>{`
          .ai-hot-tracker-report-scroll,
          .ai-hot-tracker-follow-up-scroll {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }

          .ai-hot-tracker-report-scroll::-webkit-scrollbar,
          .ai-hot-tracker-follow-up-scroll::-webkit-scrollbar {
            display: none;
            height: 0;
            width: 0;
          }
        `}</style>
      </div>
    </div>
  );
}
