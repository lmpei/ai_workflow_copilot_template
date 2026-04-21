"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  askAiHotTrackerRunFollowUp,
  createWorkspaceAiHotTrackerRun,
  deleteAiHotTrackerRun,
  isApiClientError,
  listWorkspaceAiHotTrackerRuns,
} from "../../lib/api";
import type {
  AiHotTrackerSourceItemRecord,
  AiHotTrackerTrackingProfileRecord,
  AiHotTrackerTrackingRunRecord,
  Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";

type AiHotTrackerWorkspaceProps = {
  workspace: Workspace;
  workspaceId: string;
};

type FocusTarget = {
  context: string;
  label: string;
};

type StreamingReplyState = {
  answer: string;
  question: string;
  visible: string;
};

const FOLLOW_UP_ACTIONS = [
  "这意味着什么",
  "为什么现在要看",
  "继续跟进什么",
  "依据来自哪里",
] as const;

const CADENCE_LABEL: Record<AiHotTrackerTrackingProfileRecord["cadence"], string> = {
  manual: "手动",
  daily: "每日",
  twice_daily: "每日两次",
  weekly: "每周",
};

const CATEGORY_LABEL: Record<string, string> = {
  model_research: "模型研究",
  frameworks: "框架",
  inference_runtime: "推理运行时",
  local_runtime: "本地运行时",
  agent_frameworks: "Agent 框架",
};

const CHANGE_STATE_LABEL: Record<AiHotTrackerTrackingRunRecord["delta"]["change_state"], string> = {
  first_run: "首轮",
  meaningful_update: "有明显变化",
  steady_state: "延续观察",
  degraded: "降级输出",
};

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

function buildDefaultFocus(run: AiHotTrackerTrackingRunRecord): FocusTarget {
  return {
    context: [run.output.frontier_summary, run.output.trend_judgment].filter(Boolean).join("\n\n"),
    label: "整份简报",
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

function primaryButtonStyle(disabled = false) {
  return {
    alignItems: "center",
    backgroundColor: disabled ? "rgba(15, 23, 42, 0.52)" : "#0f172a",
    border: "none",
    borderRadius: 999,
    color: "#ffffff",
    cursor: disabled ? "not-allowed" : "pointer",
    display: "inline-flex",
    fontSize: 15,
    fontWeight: 800,
    height: 52,
    justifyContent: "center",
    minWidth: 160,
    padding: "0 26px",
  } as const;
}

function secondaryButtonStyle(disabled = false) {
  return {
    alignItems: "center",
    backgroundColor: "transparent",
    border: "1px solid rgba(148, 163, 184, 0.28)",
    borderRadius: 999,
    color: disabled ? "#94a3b8" : "#0f172a",
    cursor: disabled ? "not-allowed" : "pointer",
    display: "inline-flex",
    fontSize: 14,
    fontWeight: 800,
    height: 46,
    justifyContent: "center",
    minWidth: 138,
    padding: "0 20px",
  } as const;
}

function stateBadgeStyle(state: AiHotTrackerTrackingRunRecord["delta"]["change_state"]) {
  const palette = {
    first_run: {
      background: "rgba(37, 99, 235, 0.08)",
      color: "#1d4ed8",
    },
    meaningful_update: {
      background: "rgba(15, 23, 42, 0.08)",
      color: "#0f172a",
    },
    steady_state: {
      background: "rgba(226, 232, 240, 0.9)",
      color: "#475569",
    },
    degraded: {
      background: "rgba(185, 28, 28, 0.08)",
      color: "#b91c1c",
    },
  } satisfies Record<
    AiHotTrackerTrackingRunRecord["delta"]["change_state"],
    { background: string; color: string }
  >;

  return {
    backgroundColor: palette[state].background,
    borderRadius: 999,
    color: palette[state].color,
    display: "inline-flex",
    fontSize: 12,
    fontWeight: 800,
    letterSpacing: "0.06em",
    padding: "7px 12px",
  } as const;
}

function invisibleScrollClass() {
  return "ai-hot-tracker-scroll";
}

function SourceIconLinks({
  itemIds,
  sourceItems,
}: {
  itemIds: string[];
  sourceItems: AiHotTrackerSourceItemRecord[];
}) {
  const itemMap = useMemo(
    () => new Map(sourceItems.map((item) => [item.id, item])),
    [sourceItems],
  );
  const items = itemIds
    .map((id) => itemMap.get(id))
    .filter((item): item is AiHotTrackerSourceItemRecord => Boolean(item));

  if (!items.length) {
    return null;
  }

  return (
    <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
      {items.map((item) => (
        <a
          href={item.url}
          key={item.id}
          rel="noreferrer"
          style={{
            alignItems: "center",
            color: "#64748b",
            display: "inline-flex",
            fontSize: 12,
            fontWeight: 700,
            gap: 6,
            textDecoration: "none",
          }}
          target="_blank"
          title={item.title}
        >
          <span>{item.source_label}</span>
          <span style={{ fontSize: 14, lineHeight: 1 }}>↗</span>
        </a>
      ))}
    </div>
  );
}

function RunRow({
  active,
  confirmDelete,
  hovered,
  onCancelDelete,
  onDeleteConfirm,
  onDeleteRequest,
  onHoverChange,
  onOpen,
  run,
}: {
  active: boolean;
  confirmDelete: boolean;
  hovered: boolean;
  onCancelDelete: () => void;
  onDeleteConfirm: () => void;
  onDeleteRequest: () => void;
  onHoverChange: (hovered: boolean) => void;
  onOpen: () => void;
  run: AiHotTrackerTrackingRunRecord;
}) {
  return (
    <div
      onMouseEnter={() => onHoverChange(true)}
      onMouseLeave={() => onHoverChange(false)}
      style={{
        alignItems: "center",
        backgroundColor: active || hovered ? "rgba(148, 163, 184, 0.14)" : "transparent",
        borderBottom: "1px solid rgba(148, 163, 184, 0.18)",
        borderLeft: active ? "2px solid #0f172a" : "2px solid transparent",
        display: "grid",
        gap: 12,
        gridTemplateColumns: "minmax(0, 1fr) auto",
        padding: active ? "16px 18px 16px 16px" : "16px 18px",
        transition: "background-color 160ms ease",
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
          gap: 6,
          justifyItems: "start",
          padding: 0,
          textAlign: "left",
        }}
        type="button"
      >
        <strong style={{ fontSize: 15, fontWeight: 800, lineHeight: 1.35 }}>{run.title}</strong>
        <div style={{ alignItems: "center", color: "#64748b", display: "flex", gap: 10, fontSize: 12 }}>
          <span>{formatRecordTime(run.updated_at)}</span>
          <span>{CHANGE_STATE_LABEL[run.delta.change_state]}</span>
        </div>
      </button>

      {confirmDelete ? (
        <div style={{ alignItems: "center", display: "flex", gap: 10 }}>
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

export default function AiHotTrackerWorkspace({
  workspace,
  workspaceId,
}: AiHotTrackerWorkspaceProps) {
  const { session, isReady } = useAuthSession();
  const followUpScrollRef = useRef<HTMLDivElement | null>(null);
  const [runs, setRuns] = useState<AiHotTrackerTrackingRunRecord[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [currentFocus, setCurrentFocus] = useState<FocusTarget | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hoveredRunId, setHoveredRunId] = useState<string | null>(null);
  const [followUpInput, setFollowUpInput] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [streamingReply, setStreamingReply] = useState<StreamingReplyState | null>(null);

  const trackingProfile = useMemo(() => {
    const rawProfile = workspace.module_config_json.tracking_profile;
    if (!rawProfile || typeof rawProfile !== "object") {
      return null;
    }
    return rawProfile as AiHotTrackerTrackingProfileRecord;
  }, [workspace.module_config_json]);

  const orderedRuns = useMemo(
    () => [...runs].sort((left, right) => right.updated_at.localeCompare(left.updated_at)),
    [runs],
  );
  const activeRun = orderedRuns.find((run) => run.id === activeRunId) ?? orderedRuns[0] ?? null;

  useEffect(() => {
    if (!session) {
      setRuns([]);
      setActiveRunId(null);
      return;
    }

    let cancelled = false;

    const loadRuns = async () => {
      setIsLoadingRuns(true);
      setErrorMessage(null);
      try {
        const loaded = await listWorkspaceAiHotTrackerRuns(session.accessToken, workspaceId, 20);
        if (cancelled) {
          return;
        }
        setRuns(loaded);
        if (loaded.length) {
          setActiveRunId((current) => current ?? loaded[0].id);
        } else {
          setActiveRunId(null);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(isApiClientError(error) ? error.message : "暂时无法读取追踪记录。");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingRuns(false);
        }
      }
    };

    void loadRuns();

    return () => {
      cancelled = true;
    };
  }, [session, workspaceId]);

  useEffect(() => {
    if (!activeRun) {
      setCurrentFocus(null);
      return;
    }
    setCurrentFocus(buildDefaultFocus(activeRun));
    setPendingQuestion(null);
    setStreamingReply(null);
  }, [activeRun, activeRunId]);

  useEffect(() => {
    if (!streamingReply) {
      return;
    }

    const interval = window.setInterval(() => {
      setStreamingReply((current) => {
        if (!current) {
          return current;
        }

        if (current.visible.length >= current.answer.length) {
          setRuns((previousRuns) =>
            previousRuns.map((run) =>
              run.id === activeRunId
                ? {
                    ...run,
                    follow_ups: [
                      ...run.follow_ups,
                      {
                        answer: current.answer,
                        created_at: new Date().toISOString(),
                        question: current.question,
                      },
                    ],
                    updated_at: new Date().toISOString(),
                  }
                : run,
            ),
          );
          window.clearInterval(interval);
          return null;
        }

        return {
          ...current,
          visible: current.answer.slice(0, current.visible.length + 3),
        };
      });
    }, 14);

    return () => window.clearInterval(interval);
  }, [activeRunId, streamingReply]);

  useEffect(() => {
    const node = followUpScrollRef.current;
    if (!node) {
      return;
    }
    node.scrollTop = node.scrollHeight;
  }, [activeRun?.follow_ups.length, isAsking, pendingQuestion, streamingReply?.visible]);

  const goBack = () => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      window.history.back();
      return;
    }
    window.location.href = "/";
  };

  const runTracking = async () => {
    if (!session) {
      return;
    }

    setIsRunning(true);
    setErrorMessage(null);
    try {
      const nextRun = await createWorkspaceAiHotTrackerRun(session.accessToken, workspaceId);
      setRuns((previousRuns) =>
        [nextRun, ...previousRuns.filter((item) => item.id !== nextRun.id)].sort((left, right) =>
          right.updated_at.localeCompare(left.updated_at),
        ),
      );
      setActiveRunId(nextRun.id);
      setDrawerOpen(false);
    } catch (error) {
      setErrorMessage(
        isApiClientError(error)
          ? error.message
          : error instanceof Error
            ? error.message
            : "暂时无法启动这一轮追踪。",
      );
    } finally {
      setIsRunning(false);
    }
  };

  const deleteRun = async (runId: string) => {
    if (!session) {
      return;
    }

    try {
      await deleteAiHotTrackerRun(session.accessToken, runId);
      const nextRuns = orderedRuns.filter((run) => run.id !== runId);
      setRuns(nextRuns);
      setDeleteConfirmId(null);
      if (activeRunId === runId) {
        setActiveRunId(nextRuns[0]?.id ?? null);
      }
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "删除记录失败，请稍后再试。");
    }
  };

  const askFollowUp = async (presetQuestion?: string) => {
    if (!session || !activeRun) {
      return;
    }

    const question = (presetQuestion ?? followUpInput).trim();
    if (!question) {
      return;
    }

    setIsAsking(true);
    setErrorMessage(null);
    setPendingQuestion(question);
    setFollowUpInput("");

    try {
      const response = await askAiHotTrackerRunFollowUp(session.accessToken, activeRun.id, {
        focus_context: currentFocus?.context,
        focus_label: currentFocus?.label,
        question,
      });

      setPendingQuestion(null);
      setStreamingReply({
        answer: response.follow_up.answer,
        question: response.follow_up.question,
        visible: "",
      });
    } catch (error) {
      setPendingQuestion(null);
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

  const categories = trackingProfile?.enabled_categories ?? [];

  return (
    <div
      style={{
        background:
          "radial-gradient(circle at 10% 10%, rgba(191, 219, 254, 0.46), transparent 28%), radial-gradient(circle at 88% 8%, rgba(224, 231, 255, 0.34), transparent 24%), #f8fbff",
        height: "100svh",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "grid",
          gap: 18,
          gridTemplateRows: "auto minmax(0, 1fr)",
          height: "100svh",
          margin: "0 auto",
          maxWidth: 1720,
          overflow: "hidden",
          padding: "28px 40px 24px",
        }}
      >
        <header
          style={{
            alignItems: "center",
            display: "flex",
            justifyContent: "space-between",
            minHeight: 42,
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

          {activeRun ? (
            <button
              disabled={isRunning}
              onClick={() => void runTracking()}
              style={primaryButtonStyle(isRunning)}
              type="button"
            >
              {isRunning ? "整理中…" : "刷新这一轮"}
            </button>
          ) : null}
        </header>

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

        {!activeRun ? (
          <section
            style={{
              alignItems: "center",
              display: "grid",
              gap: 26,
              justifyItems: "center",
              minHeight: 0,
              overflow: "hidden",
              padding: "24px 0 0",
            }}
          >
            <div
              style={{
                display: "grid",
                gap: 18,
                justifyItems: "center",
                maxWidth: 860,
                textAlign: "center",
              }}
            >
              <span
                style={{
                  background: "linear-gradient(135deg, #0f172a 0%, #334155 50%, #2563eb 100%)",
                  backgroundClip: "text",
                  color: "transparent",
                  fontSize: "clamp(44px, 6vw, 78px)",
                  fontWeight: 800,
                  letterSpacing: "-0.05em",
                  lineHeight: 0.92,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                AI 热点
              </span>
              <strong
                style={{
                  color: "#0f172a",
                  fontSize: "clamp(26px, 3vw, 44px)",
                  fontWeight: 700,
                  letterSpacing: "-0.04em",
                  lineHeight: 1.08,
                }}
              >
                最先看见变化的人，最先占据优势
              </strong>
              {trackingProfile ? (
                <div
                  style={{
                    alignItems: "center",
                    color: "#64748b",
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 14,
                    justifyContent: "center",
                  }}
                >
                  <span>{trackingProfile.topic}</span>
                  <span>·</span>
                  <span>{CADENCE_LABEL[trackingProfile.cadence]}</span>
                  <span>·</span>
                  <span>{categories.map((item) => CATEGORY_LABEL[item] ?? item).join(" · ")}</span>
                </div>
              ) : null}
              <button
                disabled={isRunning}
                onClick={() => void runTracking()}
                style={{
                  ...primaryButtonStyle(isRunning),
                  boxShadow: "0 20px 40px rgba(15, 23, 42, 0.14)",
                  fontSize: 18,
                  height: 64,
                  minWidth: 196,
                }}
                type="button"
              >
                {isRunning ? "整理中…" : "立即获取"}
              </button>
            </div>

            <div
              style={{
                borderTop: "1px solid rgba(148, 163, 184, 0.18)",
                display: "grid",
                gap: 12,
                marginTop: "auto",
                maxWidth: 980,
                paddingTop: 14,
                width: "100%",
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
                  borderRadius: 24,
                  overflow: "hidden",
                }}
              >
                {isLoadingRuns ? (
                  <div style={{ color: "#64748b", padding: 18 }}>正在读取记录…</div>
                ) : (
                  <div style={{ color: "#64748b", lineHeight: 1.8, padding: 18 }}>
                    还没有任何追踪记录，先运行第一轮。
                  </div>
                )}
              </div>
            </div>
          </section>
        ) : (
          <section
            style={{
              display: "grid",
              gap: 0,
              gridTemplateColumns: "minmax(0, 1.28fr) minmax(380px, 0.72fr)",
              minHeight: 0,
              overflow: "hidden",
            }}
          >
            <section
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.82)",
                border: "1px solid rgba(148, 163, 184, 0.16)",
                borderRight: "none",
                borderRadius: "30px 0 0 30px",
                display: "grid",
                gridTemplateRows: "auto minmax(0, 1fr) auto",
                minHeight: 0,
                overflow: "hidden",
                padding: "28px 30px 20px",
              }}
            >
              <div style={{ display: "grid", gap: 18, paddingBottom: 20 }}>
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
                  <span
                    style={{
                      color: "#64748b",
                      fontSize: 12,
                      fontWeight: 800,
                      letterSpacing: "0.12em",
                      textTransform: "uppercase",
                    }}
                  >
                    AI 热点
                  </span>
                  <span style={stateBadgeStyle(activeRun.delta.change_state)}>
                    {CHANGE_STATE_LABEL[activeRun.delta.change_state]}
                  </span>
                  <span style={{ color: "#94a3b8", fontSize: 13 }}>{formatRecordTime(activeRun.generated_at)}</span>
                </div>

                <div style={{ display: "grid", gap: 12, maxWidth: 840 }}>
                  <strong
                    style={{
                      color: "#0f172a",
                      fontSize: "clamp(34px, 3.3vw, 54px)",
                      fontWeight: 800,
                      letterSpacing: "-0.05em",
                      lineHeight: 0.98,
                    }}
                  >
                    {activeRun.title}
                  </strong>
                  <p
                    style={{
                      color: "#475569",
                      fontSize: 15,
                      lineHeight: 1.76,
                      margin: 0,
                      maxWidth: 760,
                    }}
                  >
                    {activeRun.delta.summary}
                  </p>
                </div>

                <div
                  style={{
                    display: "grid",
                    gap: 16,
                    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                    maxWidth: 760,
                  }}
                >
                  <div style={{ borderLeft: "1px solid rgba(148, 163, 184, 0.22)", paddingLeft: 14 }}>
                    <div style={{ color: "#94a3b8", fontSize: 12 }}>新增</div>
                    <div style={{ color: "#0f172a", fontSize: 28, fontWeight: 800 }}>
                      {activeRun.delta.new_item_count}
                    </div>
                  </div>
                  <div style={{ borderLeft: "1px solid rgba(148, 163, 184, 0.22)", paddingLeft: 14 }}>
                    <div style={{ color: "#94a3b8", fontSize: 12 }}>延续</div>
                    <div style={{ color: "#0f172a", fontSize: 28, fontWeight: 800 }}>
                      {activeRun.delta.continuing_item_count}
                    </div>
                  </div>
                  <div style={{ borderLeft: "1px solid rgba(148, 163, 184, 0.22)", paddingLeft: 14 }}>
                    <div style={{ color: "#94a3b8", fontSize: 12 }}>降温</div>
                    <div style={{ color: "#0f172a", fontSize: 28, fontWeight: 800 }}>
                      {activeRun.delta.cooled_down_item_count}
                    </div>
                  </div>
                </div>
              </div>

              <div
                className={invisibleScrollClass()}
                style={{
                  display: "grid",
                  gap: 26,
                  minHeight: 0,
                  overflowY: "auto",
                  paddingRight: 12,
                }}
              >
                <section style={{ display: "grid", gap: 12 }}>
                  <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.12em" }}>
                    本轮结论
                  </span>
                  <button
                    onClick={() =>
                      setCurrentFocus({
                        context: activeRun.output.frontier_summary,
                        label: "本轮结论",
                      })
                    }
                    style={{
                      backgroundColor:
                        currentFocus?.label === "本轮结论" ? "rgba(15, 23, 42, 0.04)" : "transparent",
                      border: "none",
                      borderRadius: 18,
                      color: "#0f172a",
                      cursor: "pointer",
                      fontSize: 22,
                      fontWeight: 700,
                      lineHeight: 1.7,
                      padding: "10px 12px 10px 0",
                      textAlign: "left",
                    }}
                    type="button"
                  >
                    {activeRun.output.frontier_summary}
                  </button>
                </section>

                <section
                  style={{
                    borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                    display: "grid",
                    gap: 12,
                    paddingTop: 22,
                  }}
                >
                  <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.12em" }}>
                    变化判断
                  </span>
                  <button
                    onClick={() =>
                      setCurrentFocus({
                        context: activeRun.output.trend_judgment,
                        label: "变化判断",
                      })
                    }
                    style={{
                      backgroundColor:
                        currentFocus?.label === "变化判断" ? "rgba(15, 23, 42, 0.04)" : "transparent",
                      border: "none",
                      borderRadius: 18,
                      cursor: "pointer",
                      display: "grid",
                      gap: 10,
                      padding: "12px 14px 12px 0",
                      textAlign: "left",
                    }}
                    type="button"
                  >
                    {activeRun.output.trend_judgment
                      .split(/\n+/)
                      .map((paragraph) => paragraph.trim())
                      .filter(Boolean)
                      .map((paragraph, index) => (
                        <p
                          key={`${paragraph.slice(0, 20)}-${index}`}
                          style={{
                            color: index === 0 ? "#0f172a" : "#475569",
                            fontSize: index === 0 ? 19 : 15,
                            fontWeight: index === 0 ? 700 : 500,
                            lineHeight: 1.8,
                            margin: 0,
                          }}
                        >
                          {paragraph}
                        </p>
                      ))}
                  </button>
                </section>

                {!!activeRun.output.events.length && (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.12em" }}>
                      正在发生
                    </span>
                    <div style={{ display: "grid", gap: 18 }}>
                      {activeRun.output.events.map((event, index) => (
                        <button
                          key={`${event.title}-${index}`}
                          onClick={() =>
                            setCurrentFocus({
                              context: [event.summary, event.significance].filter(Boolean).join("\n\n"),
                              label: event.title,
                            })
                          }
                          style={{
                            backgroundColor:
                              currentFocus?.label === event.title ? "rgba(15, 23, 42, 0.04)" : "transparent",
                            border: "none",
                            borderRadius: 18,
                            cursor: "pointer",
                            display: "grid",
                            gap: 10,
                            gridTemplateColumns: "18px minmax(0, 1fr)",
                            padding: "8px 14px 8px 0",
                            textAlign: "left",
                          }}
                          type="button"
                        >
                          <span
                            style={{
                              alignItems: "center",
                              display: "grid",
                              justifyItems: "center",
                              paddingTop: 9,
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
                          </span>
                          <div style={{ display: "grid", gap: 8 }}>
                            <strong style={{ color: "#0f172a", fontSize: 19, lineHeight: 1.45 }}>
                              {event.title}
                            </strong>
                            <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.8, margin: 0 }}>{event.summary}</p>
                            <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.74, margin: 0 }}>
                              {event.significance}
                            </p>
                            <SourceIconLinks itemIds={event.source_item_ids} sourceItems={activeRun.source_items} />
                          </div>
                        </button>
                      ))}
                    </div>
                  </section>
                )}

                {!!activeRun.output.project_cards.length && (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.12em" }}>
                      值得继续看
                    </span>
                    <div style={{ display: "grid", gap: 20 }}>
                      {activeRun.output.project_cards.map((card, index) => (
                        <button
                          key={`${card.title}-${index}`}
                          onClick={() =>
                            setCurrentFocus({
                              context: [card.summary, card.why_it_matters].filter(Boolean).join("\n\n"),
                              label: card.title,
                            })
                          }
                          style={{
                            backgroundColor:
                              currentFocus?.label === card.title ? "rgba(15, 23, 42, 0.04)" : "transparent",
                            border: "none",
                            borderRadius: 18,
                            cursor: "pointer",
                            display: "grid",
                            gap: 10,
                            padding: "12px 14px 12px 0",
                            textAlign: "left",
                          }}
                          type="button"
                        >
                          <div style={{ alignItems: "baseline", display: "flex", gap: 10, justifyContent: "space-between" }}>
                            <strong style={{ color: "#0f172a", fontSize: 22, lineHeight: 1.3 }}>{card.title}</strong>
                            <span style={{ color: "#64748b", fontSize: 12 }}>{card.source_label}</span>
                          </div>
                          <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.8, margin: 0 }}>{card.summary}</p>
                          <p style={{ color: "#475569", fontSize: 15, lineHeight: 1.8, margin: 0 }}>{card.why_it_matters}</p>
                          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 12 }}>
                            {card.tags.map((tag) => (
                              <span
                                key={`${card.title}-${tag}`}
                                style={{ color: "#64748b", fontSize: 12, fontWeight: 700 }}
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                          <SourceIconLinks itemIds={card.source_item_ids} sourceItems={activeRun.source_items} />
                        </button>
                      ))}
                    </div>
                  </section>
                )}

                {!!activeRun.output.reference_sources.length && (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.12em" }}>
                      来源
                    </span>
                    <div style={{ display: "grid", gap: 10 }}>
                      {activeRun.output.reference_sources.map((source, index) => (
                        <a
                          href={source.url}
                          key={`${source.label}-${index}`}
                          rel="noreferrer"
                          style={{
                            alignItems: "center",
                            borderBottom:
                              index === activeRun.output.reference_sources.length - 1
                                ? "none"
                                : "1px solid rgba(148, 163, 184, 0.14)",
                            color: "#0f172a",
                            display: "flex",
                            fontSize: 14,
                            fontWeight: 700,
                            gap: 8,
                            justifyContent: "space-between",
                            paddingBottom:
                              index === activeRun.output.reference_sources.length - 1 ? 0 : 10,
                            textDecoration: "none",
                          }}
                          target="_blank"
                        >
                          <span>{source.label}</span>
                          <span style={{ color: "#64748b" }}>↗</span>
                        </a>
                      ))}
                    </div>
                  </section>
                )}
              </div>

              <div
                style={{
                  alignItems: "center",
                  borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                  display: "flex",
                  justifyContent: "space-between",
                  paddingTop: 14,
                }}
              >
                <div style={{ color: "#64748b", fontSize: 13 }}>
                  {trackingProfile
                    ? `${trackingProfile.topic} · ${CADENCE_LABEL[trackingProfile.cadence]}`
                    : "持续追踪工作区"}
                </div>
                <button
                  disabled={isRunning}
                  onClick={() => void runTracking()}
                  style={primaryButtonStyle(isRunning)}
                  type="button"
                >
                  {isRunning ? "整理中…" : "获取新一轮"}
                </button>
              </div>
            </section>

            <aside
              style={{
                backgroundColor: "rgba(250, 252, 255, 0.94)",
                border: "1px solid rgba(148, 163, 184, 0.16)",
                borderRadius: "0 30px 30px 0",
                borderLeft: "1px solid rgba(148, 163, 184, 0.16)",
                display: "grid",
                gridTemplateRows: "auto auto minmax(0, 1fr) auto",
                minHeight: 0,
                overflow: "hidden",
                padding: "24px 20px 18px",
              }}
            >
              <div style={{ display: "grid", gap: 6 }}>
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
                <strong style={{ color: "#0f172a", fontSize: 18, lineHeight: 1.35 }}>
                  {currentFocus?.label ?? "整份简报"}
                </strong>
                <span style={{ color: "#64748b", fontSize: 13, lineHeight: 1.7 }}>
                  回答只围绕当前报告和它的来源，不会漂移成泛聊天。
                </span>
              </div>

              <div
                style={{
                  borderBottom: "1px solid rgba(148, 163, 184, 0.16)",
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 8,
                  paddingBottom: 12,
                  paddingTop: 14,
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

              <div
                className={invisibleScrollClass()}
                ref={followUpScrollRef}
                style={{
                  display: "grid",
                  gap: 14,
                  minHeight: 0,
                  overflowY: "auto",
                  paddingBottom: 18,
                  paddingRight: 6,
                  paddingTop: 18,
                }}
              >
                {activeRun.follow_ups.map((entry, index) => (
                  <div key={`${entry.question}-${index}`} style={{ display: "grid", gap: 10 }}>
                    <div style={{ display: "flex", justifyContent: "flex-end" }}>
                      <div
                        style={{
                          backgroundColor: "#0f172a",
                          borderRadius: "20px 20px 6px 20px",
                          color: "#f8fbff",
                          lineHeight: 1.7,
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
                ))}

                {pendingQuestion ? (
                  <div style={{ display: "grid", gap: 10 }}>
                    <div style={{ display: "flex", justifyContent: "flex-end" }}>
                      <div
                        style={{
                          backgroundColor: "#0f172a",
                          borderRadius: "20px 20px 6px 20px",
                          color: "#f8fbff",
                          lineHeight: 1.7,
                          maxWidth: "88%",
                          padding: "11px 13px",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {pendingQuestion}
                      </div>
                    </div>
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
                  </div>
                ) : null}

                {streamingReply ? (
                  <div style={{ display: "grid", gap: 10 }}>
                    <div style={{ display: "flex", justifyContent: "flex-end" }}>
                      <div
                        style={{
                          backgroundColor: "#0f172a",
                          borderRadius: "20px 20px 6px 20px",
                          color: "#f8fbff",
                          lineHeight: 1.7,
                          maxWidth: "88%",
                          padding: "11px 13px",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {streamingReply.question}
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
                        {streamingReply.visible}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>

              <div
                style={{
                  borderTop: "1px solid rgba(148, 163, 184, 0.16)",
                  display: "grid",
                  gap: 10,
                  paddingTop: 16,
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
                    disabled={isAsking || !!pendingQuestion || !followUpInput.trim()}
                    onClick={() => void askFollowUp()}
                    style={primaryButtonStyle(isAsking || !!pendingQuestion || !followUpInput.trim())}
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
          <aside
            onClick={(event) => event.stopPropagation()}
            style={{
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
              transform: drawerOpen ? "translateX(0)" : "translateX(-108%)",
              transition: "transform 220ms ease",
              width: 356,
            }}
          >
            <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
              <div style={{ display: "grid", gap: 4 }}>
                <strong style={{ color: "#0f172a", fontSize: 22 }}>所有记录</strong>
                <span style={{ color: "#64748b", fontSize: 12 }}>
                  {orderedRuns.length ? `${orderedRuns.length} 条追踪记录` : "还没有追踪记录"}
                </span>
              </div>
              <button aria-label="关闭" onClick={() => setDrawerOpen(false)} style={iconButtonStyle(false)} type="button">
                ×
              </button>
            </div>

            <div
              className={invisibleScrollClass()}
              style={{
                border: "1px solid rgba(148, 163, 184, 0.18)",
                borderRadius: 24,
                minHeight: 0,
                overflowY: "auto",
              }}
            >
              {isLoadingRuns ? (
                <div style={{ color: "#64748b", padding: 18 }}>正在读取记录…</div>
              ) : orderedRuns.length ? (
                orderedRuns.map((run) => (
                  <RunRow
                    active={activeRun?.id === run.id}
                    confirmDelete={deleteConfirmId === run.id}
                    hovered={hoveredRunId === run.id}
                    key={run.id}
                    onCancelDelete={() => setDeleteConfirmId(null)}
                    onDeleteConfirm={() => void deleteRun(run.id)}
                    onDeleteRequest={() => setDeleteConfirmId(run.id)}
                    onHoverChange={(hovered) => setHoveredRunId(hovered ? run.id : null)}
                    onOpen={() => {
                      setActiveRunId(run.id);
                      setDrawerOpen(false);
                      setDeleteConfirmId(null);
                    }}
                    run={run}
                  />
                ))
              ) : (
                <div style={{ color: "#64748b", lineHeight: 1.8, padding: 18 }}>运行后的追踪记录会出现在这里。</div>
              )}
            </div>
          </aside>
        </div>

        <style jsx global>{`
          .${invisibleScrollClass()} {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }

          .${invisibleScrollClass()}::-webkit-scrollbar {
            display: none;
            height: 0;
            width: 0;
          }
        `}</style>
      </div>
    </div>
  );
}
