"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import {
  usePathname,
  useRouter,
  useSearchParams,
} from "next/navigation";

import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import {
  askAiHotTrackerRunFollowUp,
  getAiHotTrackerReplayEvaluation,
  createWorkspaceAiHotTrackerRun,
  deleteAiHotTrackerRun,
  getAiHotTrackerRunEvaluation,
  getWorkspaceAiHotTrackerState,
  isApiClientError,
  listWorkspaceAiHotTrackerRuns,
  updateWorkspace,
} from "../../lib/api";
import type {
  AiFrontierFollowUpEntryRecord,
  AiHotTrackerAgentRoleTraceRecord,
  AiHotTrackerBriefSignalRecord,
  AiHotTrackerJudgmentFindingRecord,
  AiHotTrackerReplayEvaluationRecord,
  AiHotTrackerRunEvaluationRecord,
  AiHotTrackerSignalClusterRecord,
  AiHotTrackerSignalMemoryRecord,
  AiHotTrackerSourceFailureRecord,
  AiHotTrackerSourceItemRecord,
  AiHotTrackerTrackingProfileRecord,
  AiHotTrackerTrackingRunRecord,
  AiHotTrackerTrackingStateRecord,
  Workspace,
} from "../../lib/types";

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

type ProfileDraft = Pick<
  AiHotTrackerTrackingProfileRecord,
  "cadence" | "enabled_categories" | "alert_threshold"
>;

const HIDDEN_SCROLL_CLASS = "ai-hot-tracker-scroll";

const FOLLOW_UP_PRESETS = [
  "这意味着什么？",
  "为什么现在重要？",
  "更适合谁关注？",
  "接下来还要继续看什么？",
] as const;

const CATEGORY_LABEL: Record<string, string> = {
  models: "模型",
  products: "产品",
  developer_tools: "工具",
  research: "论文",
  business: "商业",
  open_source: "开源",
};

const CADENCE_LABEL: Record<AiHotTrackerTrackingProfileRecord["cadence"], string> = {
  manual: "仅手动",
  daily: "每天",
  twice_daily: "每天两次",
  weekly: "每周",
};

const CHANGE_STATE_LABEL: Record<
  AiHotTrackerTrackingRunRecord["delta"]["change_state"],
  string
> = {
  first_run: "首轮判断",
  meaningful_update: "出现明显变化",
  steady_state: "持续观察中",
  degraded: "信息不完整",
  failed: "本轮失败",
};

const PRIORITY_LABEL: Record<
  AiHotTrackerTrackingRunRecord["delta"]["priority_level"],
  string
> = {
  high: "高优先级",
  medium: "中优先级",
  low: "低优先级",
};

const CONFIDENCE_LABEL: Record<AiHotTrackerBriefSignalRecord["confidence"], string> = {
  high: "判断把握高",
  medium: "判断把握中等",
  low: "判断把握有限",
};

const SOURCE_FAMILY_MARK: Record<AiHotTrackerSourceItemRecord["source_family"], string> = {
  official: "官",
  media: "媒",
  research: "研",
  open_source: "源",
};

const defaultTrackingProfile: AiHotTrackerTrackingProfileRecord = {
  alert_threshold: 1,
  cadence: "daily",
  enabled_categories: [
    "models",
    "products",
    "developer_tools",
    "research",
    "business",
    "open_source",
  ],
  max_items_per_run: 24,
  scope: "从高可信来源持续追踪全球 AI 变化，筛选真正值得关注的信号。",
  source_strategy: "allowlist_curated",
  topic: "AI 模型、产品、工具、论文、开源与商业变化",
};

function formatTime(value?: string | null, options?: Intl.DateTimeFormatOptions) {
  if (!value) {
    return "--";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    ...options,
  });
}

function mergeTrackingProfile(
  workspaceSnapshot: Workspace,
  nextDraft: ProfileDraft,
): Workspace["module_config_json"] {
  const current = workspaceSnapshot.module_config_json ?? {};
  return {
    ...current,
    tracking_profile: {
      ...(typeof current.tracking_profile === "object" && current.tracking_profile
        ? current.tracking_profile
        : {}),
      ...nextDraft,
    },
  };
}

function getTrackingProfile(workspaceSnapshot: Workspace) {
  const rawValue = workspaceSnapshot.module_config_json?.tracking_profile;
  if (!rawValue || typeof rawValue !== "object") {
    return defaultTrackingProfile;
  }

  return {
    ...defaultTrackingProfile,
    ...rawValue,
  } as AiHotTrackerTrackingProfileRecord;
}

function buildDefaultFocus(run: AiHotTrackerTrackingRunRecord): FocusTarget {
  const signalLines = run.output.signals
    .map((signal) => `${signal.title}\n${signal.summary}\n${signal.why_now}`)
    .join("\n\n");
  const keepWatchingLines = run.output.keep_watching
    .map((item) => `${item.title}\n${item.reason}`)
    .join("\n\n");

  return {
    context: [run.output.summary, signalLines, keepWatchingLines]
      .filter(Boolean)
      .join("\n\n"),
    label: "整份简报",
  };
}

function changeStateBadgeStyle(
  state: AiHotTrackerTrackingRunRecord["delta"]["change_state"],
): CSSProperties {
  const palette = {
    first_run: { background: "rgba(37, 99, 235, 0.1)", color: "#1d4ed8" },
    meaningful_update: { background: "rgba(15, 23, 42, 0.08)", color: "#0f172a" },
    steady_state: { background: "rgba(226, 232, 240, 0.92)", color: "#475569" },
    degraded: { background: "rgba(245, 158, 11, 0.14)", color: "#b45309" },
    failed: { background: "rgba(185, 28, 28, 0.1)", color: "#b91c1c" },
  } satisfies Record<
    AiHotTrackerTrackingRunRecord["delta"]["change_state"],
    { background: string; color: string }
  >;

  return {
    alignItems: "center",
    backgroundColor: palette[state].background,
    borderRadius: 999,
    color: palette[state].color,
    display: "inline-flex",
    fontSize: 12,
    fontWeight: 800,
    letterSpacing: "0.08em",
    padding: "7px 12px",
    whiteSpace: "nowrap",
  };
}

function priorityBadgeStyle(
  priority: AiHotTrackerTrackingRunRecord["delta"]["priority_level"],
): CSSProperties {
  const palette = {
    high: { background: "rgba(185, 28, 28, 0.08)", color: "#b91c1c" },
    medium: { background: "rgba(15, 23, 42, 0.08)", color: "#334155" },
    low: { background: "rgba(226, 232, 240, 0.9)", color: "#64748b" },
  } satisfies Record<
    AiHotTrackerTrackingRunRecord["delta"]["priority_level"],
    { background: string; color: string }
  >;

  return {
    alignItems: "center",
    backgroundColor: palette[priority].background,
    borderRadius: 999,
    color: palette[priority].color,
    display: "inline-flex",
    fontSize: 12,
    fontWeight: 800,
    letterSpacing: "0.08em",
    padding: "7px 12px",
    whiteSpace: "nowrap",
  };
}

function iconButtonStyle(active = false): CSSProperties {
  return {
    alignItems: "center",
    backgroundColor: active ? "rgba(15, 23, 42, 0.08)" : "rgba(255, 255, 255, 0.72)",
    backdropFilter: "blur(16px)",
    border: "1px solid rgba(148, 163, 184, 0.18)",
    borderRadius: 999,
    color: "#0f172a",
    cursor: "pointer",
    display: "inline-flex",
    height: 42,
    justifyContent: "center",
    transition: "background-color 180ms ease, border-color 180ms ease",
    width: 42,
  };
}

function primaryButtonStyle(disabled = false): CSSProperties {
  return {
    alignItems: "center",
    backgroundColor: disabled ? "rgba(15, 23, 42, 0.45)" : "#0f172a",
    border: "none",
    borderRadius: 999,
    color: "#ffffff",
    cursor: disabled ? "not-allowed" : "pointer",
    display: "inline-flex",
    fontSize: 14,
    fontWeight: 800,
    height: 50,
    justifyContent: "center",
    minWidth: 144,
    padding: "0 24px",
    transition: "transform 180ms ease, opacity 180ms ease",
  };
}

function ghostButtonStyle(disabled = false): CSSProperties {
  return {
    alignItems: "center",
    backgroundColor: "rgba(255, 255, 255, 0.7)",
    backdropFilter: "blur(12px)",
    border: "1px solid rgba(148, 163, 184, 0.18)",
    borderRadius: 999,
    color: disabled ? "#94a3b8" : "#0f172a",
    cursor: disabled ? "not-allowed" : "pointer",
    display: "inline-flex",
    fontSize: 14,
    fontWeight: 800,
    height: 46,
    justifyContent: "center",
    minWidth: 120,
    padding: "0 20px",
  };
}

function surfaceStyle(): CSSProperties {
  return {
    backgroundColor: "rgba(249, 251, 255, 0.88)",
    border: "1px solid rgba(148, 163, 184, 0.16)",
    borderRadius: 30,
    boxShadow: "0 18px 50px rgba(15, 23, 42, 0.06)",
    overflow: "hidden",
  };
}

function SourceAnchorRow({
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
    .map((itemId) => itemMap.get(itemId))
    .filter((item): item is AiHotTrackerSourceItemRecord => Boolean(item));

  if (!items.length) {
    return null;
  }

  return (
    <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
      {items.map((item) => (
        <a
          href={item.url}
          key={item.id}
          rel="noreferrer"
          style={{
            alignItems: "center",
            color: "#64748b",
            display: "inline-flex",
            gap: 8,
            textDecoration: "none",
          }}
          target="_blank"
          title={`${item.source_label} · ${item.title}`}
        >
          <span
            style={{
              alignItems: "center",
              backgroundColor: "rgba(15, 23, 42, 0.07)",
              borderRadius: 999,
              color: "#0f172a",
              display: "inline-flex",
              fontSize: 11,
              fontWeight: 800,
              height: 22,
              justifyContent: "center",
              width: 22,
            }}
          >
            {SOURCE_FAMILY_MARK[item.source_family]}
          </span>
          <span style={{ fontSize: 12, fontWeight: 700 }}>{item.source_label}</span>
        </a>
      ))}
    </div>
  );
}

function HistoryRow({
  active,
  confirmDelete,
  onCancelDelete,
  onDeleteConfirm,
  onDeleteRequest,
  onOpen,
  run,
}: {
  active: boolean;
  confirmDelete: boolean;
  onCancelDelete: () => void;
  onDeleteConfirm: () => void;
  onDeleteRequest: () => void;
  onOpen: () => void;
  run: AiHotTrackerTrackingRunRecord;
}) {
  return (
    <div
      style={{
        alignItems: "center",
        backgroundColor: active ? "rgba(15, 23, 42, 0.06)" : "transparent",
        borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
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
        <div
          style={{
            alignItems: "center",
            color: "#64748b",
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            fontSize: 12,
          }}
        >
          <span>{formatTime(run.updated_at)}</span>
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

function RuntimeMeta({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div style={{ display: "grid", gap: 6 }}>
      <span
        style={{
          color: "#94a3b8",
          fontSize: 11,
          fontWeight: 800,
          letterSpacing: "0.12em",
        }}
      >
        {label}
      </span>
      <span style={{ color: "#0f172a", fontSize: 14, lineHeight: 1.5 }}>{value}</span>
    </div>
  );
}

function EvaluationSection({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section
      style={{
        borderTop: "1px solid rgba(148, 163, 184, 0.14)",
        display: "grid",
        gap: 12,
        paddingTop: 18,
      }}
    >
      <div style={{ display: "grid", gap: 4 }}>
        <strong style={{ color: "#0f172a", fontSize: 17 }}>{title}</strong>
        {subtitle ? (
          <span style={{ color: "#64748b", fontSize: 13, lineHeight: 1.7 }}>{subtitle}</span>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function SignalItem({
  active,
  onFocus,
  signal,
  sourceItems,
}: {
  active: boolean;
  onFocus: () => void;
  signal: AiHotTrackerBriefSignalRecord;
  sourceItems: AiHotTrackerSourceItemRecord[];
}) {
  return (
    <button
      onClick={onFocus}
      style={{
        backgroundColor: active ? "rgba(15, 23, 42, 0.04)" : "transparent",
        border: "none",
        borderRadius: 20,
        cursor: "pointer",
        display: "grid",
        gap: 12,
        padding: "18px 18px 18px 0",
        textAlign: "left",
      }}
      type="button"
    >
      <div
        style={{
          alignItems: "baseline",
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          justifyContent: "space-between",
        }}
      >
        <strong
          style={{
            color: "#0f172a",
            fontSize: 20,
            fontWeight: 800,
            lineHeight: 1.35,
            maxWidth: "82%",
          }}
        >
          {signal.title}
        </strong>
        <span style={priorityBadgeStyle(signal.priority_level)}>{PRIORITY_LABEL[signal.priority_level]}</span>
      </div>
      <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.82, margin: 0 }}>{signal.summary}</p>
      <p style={{ color: "#0f172a", fontSize: 14, fontWeight: 700, lineHeight: 1.8, margin: 0 }}>
        为什么现在看：{signal.why_now}
      </p>
      <p style={{ color: "#475569", fontSize: 14, lineHeight: 1.8, margin: 0 }}>
        影响：{signal.impact}
      </p>
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
        {signal.audience.map((audience) => (
          <span
            key={`${signal.title}-${audience}`}
            style={{
              color: "#64748b",
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            {audience}
          </span>
        ))}
        <span
          style={{
            color: "#94a3b8",
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          {CONFIDENCE_LABEL[signal.confidence]}
        </span>
      </div>
      <SourceAnchorRow itemIds={signal.source_item_ids} sourceItems={sourceItems} />
    </button>
  );
}

function KeepWatchingItem({
  active,
  item,
  onFocus,
  sourceItems,
}: {
  active: boolean;
  item: AiHotTrackerTrackingRunRecord["output"]["keep_watching"][number];
  onFocus: () => void;
  sourceItems: AiHotTrackerSourceItemRecord[];
}) {
  return (
    <button
      onClick={onFocus}
      style={{
        backgroundColor: active ? "rgba(15, 23, 42, 0.04)" : "transparent",
        border: "none",
        borderRadius: 18,
        cursor: "pointer",
        display: "grid",
        gap: 8,
        padding: "14px 16px 14px 0",
        textAlign: "left",
      }}
      type="button"
    >
      <strong style={{ color: "#0f172a", fontSize: 17, lineHeight: 1.4 }}>{item.title}</strong>
      <p style={{ color: "#475569", fontSize: 14, lineHeight: 1.8, margin: 0 }}>{item.reason}</p>
      <SourceAnchorRow itemIds={item.source_item_ids} sourceItems={sourceItems} />
    </button>
  );
}

function renderRoleLabel(role: AiHotTrackerAgentRoleTraceRecord["role"]) {
  const labelMap: Record<AiHotTrackerAgentRoleTraceRecord["role"], string> = {
    scout: "Scout",
    resolver: "Resolver",
    analyst: "Analyst",
    editor: "Editor",
    evaluator: "Evaluator",
    follow_up: "Follow-up",
  };

  return labelMap[role];
}

function findingBadgeStyle(status: AiHotTrackerJudgmentFindingRecord["status"]): CSSProperties {
  const palette = {
    pass: { background: "rgba(22, 163, 74, 0.10)", color: "#15803d" },
    warn: { background: "rgba(245, 158, 11, 0.12)", color: "#b45309" },
    fail: { background: "rgba(185, 28, 28, 0.10)", color: "#b91c1c" },
  } satisfies Record<
    AiHotTrackerJudgmentFindingRecord["status"],
    { background: string; color: string }
  >;

  return {
    alignItems: "center",
    backgroundColor: palette[status].background,
    borderRadius: 999,
    color: palette[status].color,
    display: "inline-flex",
    fontSize: 11,
    fontWeight: 800,
    letterSpacing: "0.08em",
    padding: "6px 10px",
    whiteSpace: "nowrap",
  };
}

function renderFindingStatusLabel(status: AiHotTrackerJudgmentFindingRecord["status"]) {
  const labelMap: Record<AiHotTrackerJudgmentFindingRecord["status"], string> = {
    pass: "通过",
    warn: "注意",
    fail: "失败",
  };

  return labelMap[status];
}

function buildFollowUpGroundingSummary(entry: AiFrontierFollowUpEntryRecord) {
  const parts: string[] = [];
  if (entry.grounding_source_item_ids?.length) {
    parts.push(`来源 ${entry.grounding_source_item_ids.length} 条`);
  }
  if (entry.grounding_event_ids?.length) {
    parts.push(`事件 ${entry.grounding_event_ids.length} 个`);
  }
  if (entry.grounding_blindspots?.length) {
    parts.push(`盲点 ${entry.grounding_blindspots.length} 条`);
  }
  if (entry.grounding_notes?.length) {
    parts.push(entry.grounding_notes.join(" · "));
  }
  return parts.length ? parts.join(" · ") : null;
}

export default function AiHotTrackerWorkspace({
  workspace,
  workspaceId,
}: AiHotTrackerWorkspaceProps) {
  const { isReady, session } = useAuthSession();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const followUpScrollRef = useRef<HTMLDivElement | null>(null);
  const [workspaceSnapshot, setWorkspaceSnapshot] = useState(workspace);
  const [runs, setRuns] = useState<AiHotTrackerTrackingRunRecord[]>([]);
  const [stateRecord, setStateRecord] = useState<AiHotTrackerTrackingStateRecord | null>(null);
  const [evaluation, setEvaluation] = useState<AiHotTrackerRunEvaluationRecord | null>(null);
  const [replayEvaluation, setReplayEvaluation] = useState<AiHotTrackerReplayEvaluationRecord | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [followUpInput, setFollowUpInput] = useState("");
  const [currentFocus, setCurrentFocus] = useState<FocusTarget | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [streamingReply, setStreamingReply] = useState<StreamingReplyState | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isLoadingState, setIsLoadingState] = useState(false);
  const [isLoadingEvaluation, setIsLoadingEvaluation] = useState(false);
  const [isLoadingReplayEvaluation, setIsLoadingReplayEvaluation] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileDraft, setProfileDraft] = useState<ProfileDraft>({
    alert_threshold: defaultTrackingProfile.alert_threshold,
    cadence: defaultTrackingProfile.cadence,
    enabled_categories: defaultTrackingProfile.enabled_categories,
  });

  const evaluationMode = searchParams.get("view") === "evaluation";
  const trackingProfile = useMemo(
    () => getTrackingProfile(workspaceSnapshot),
    [workspaceSnapshot],
  );
  const orderedRuns = useMemo(
    () => [...runs].sort((left, right) => right.updated_at.localeCompare(left.updated_at)),
    [runs],
  );
  const activeRun = useMemo(
    () => orderedRuns.find((run) => run.id === activeRunId) ?? orderedRuns[0] ?? null,
    [activeRunId, orderedRuns],
  );

  useEffect(() => {
    setWorkspaceSnapshot(workspace);
  }, [workspace]);

  useEffect(() => {
    setProfileDraft({
      alert_threshold: trackingProfile.alert_threshold,
      cadence: trackingProfile.cadence,
      enabled_categories: trackingProfile.enabled_categories,
    });
  }, [trackingProfile]);

  useEffect(() => {
    if (!session) {
      setRuns([]);
      setStateRecord(null);
      setActiveRunId(null);
      return;
    }

    let cancelled = false;

    const loadRunsAndState = async () => {
      setIsLoadingRuns(true);
      setIsLoadingState(true);
      setErrorMessage(null);

      try {
        const [loadedRuns, loadedState] = await Promise.all([
          listWorkspaceAiHotTrackerRuns(session.accessToken, workspaceId, 20),
          getWorkspaceAiHotTrackerState(session.accessToken, workspaceId),
        ]);
        if (cancelled) {
          return;
        }

        setRuns(loadedRuns);
        setStateRecord(loadedState);
        setActiveRunId((current) => current ?? loadedRuns[0]?.id ?? loadedState.latest_saved_run_id ?? null);
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            isApiClientError(error) ? error.message : "暂时无法读取热点追踪工作区。",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingRuns(false);
          setIsLoadingState(false);
        }
      }
    };

    void loadRunsAndState();

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
  }, [activeRun]);

  useEffect(() => {
    if (!session || !evaluationMode || !activeRun) {
      setEvaluation(null);
      return;
    }

    let cancelled = false;

    const loadEvaluation = async () => {
      setIsLoadingEvaluation(true);
      try {
        const nextEvaluation = await getAiHotTrackerRunEvaluation(session.accessToken, activeRun.id);
        if (!cancelled) {
          setEvaluation(nextEvaluation);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            isApiClientError(error) ? error.message : "暂时无法读取内部评测视图。",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingEvaluation(false);
        }
      }
    };

    void loadEvaluation();

    return () => {
      cancelled = true;
    };
  }, [activeRun, evaluationMode, session]);

  useEffect(() => {
    if (!session || !evaluationMode) {
      setReplayEvaluation(null);
      return;
    }

    let cancelled = false;

    const loadReplayEvaluation = async () => {
      setIsLoadingReplayEvaluation(true);
      try {
        const nextReplayEvaluation = await getAiHotTrackerReplayEvaluation(session.accessToken);
        if (!cancelled) {
          setReplayEvaluation(nextReplayEvaluation);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            isApiClientError(error) ? error.message : "暂时无法读取 replay 校准视图。",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingReplayEvaluation(false);
        }
      }
    };

    void loadReplayEvaluation();

    return () => {
      cancelled = true;
    };
  }, [evaluationMode, session]);

  useEffect(() => {
    if (!streamingReply) {
      return;
    }

    const timer = window.setInterval(() => {
      setStreamingReply((current) => {
        if (!current) {
          return current;
        }

        if (current.visible.length >= current.answer.length) {
          window.clearInterval(timer);
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
          return null;
        }

        return {
          ...current,
          visible: current.answer.slice(0, current.visible.length + 3),
        };
      });
    }, 14);

    return () => window.clearInterval(timer);
  }, [activeRunId, streamingReply]);

  useEffect(() => {
    const node = followUpScrollRef.current;
    if (!node) {
      return;
    }

    node.scrollTop = node.scrollHeight;
  }, [activeRun?.follow_ups.length, pendingQuestion, streamingReply?.visible]);

  function setEvaluationMode(nextValue: boolean) {
    const nextParams = new URLSearchParams(searchParams.toString());
    if (nextValue) {
      nextParams.set("view", "evaluation");
    } else {
      nextParams.delete("view");
    }

    const suffix = nextParams.toString();
    router.replace(suffix ? `${pathname}?${suffix}` : pathname);
  }

  async function refreshRuntimeState() {
    if (!session) {
      return;
    }

    setIsLoadingState(true);
    try {
      const nextState = await getWorkspaceAiHotTrackerState(session.accessToken, workspaceId);
      setStateRecord(nextState);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "暂时无法刷新运行状态。");
    } finally {
      setIsLoadingState(false);
    }
  }

  async function handleRunTracking() {
    if (!session) {
      return;
    }

    setIsRunning(true);
    setErrorMessage(null);

    try {
      const nextRun = await createWorkspaceAiHotTrackerRun(session.accessToken, workspaceId);
      setRuns((previousRuns) =>
        [nextRun, ...previousRuns.filter((run) => run.id !== nextRun.id)].sort((left, right) =>
          right.updated_at.localeCompare(left.updated_at),
        ),
      );
      setActiveRunId(nextRun.id);
      setHistoryOpen(false);
      await refreshRuntimeState();
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "这一轮热点获取没有成功。",
      );
    } finally {
      setIsRunning(false);
    }
  }

  async function handleDeleteRun(runId: string) {
    if (!session) {
      return;
    }

    try {
      await deleteAiHotTrackerRun(session.accessToken, runId);
      const remaining = orderedRuns.filter((run) => run.id !== runId);
      setRuns(remaining);
      setDeleteConfirmId(null);
      if (activeRunId === runId) {
        setActiveRunId(remaining[0]?.id ?? null);
      }
      await refreshRuntimeState();
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "删除这条记录时失败，请稍后再试。",
      );
    }
  }

  async function handleSaveProfile() {
    if (!session) {
      return;
    }

    setIsSavingProfile(true);
    setErrorMessage(null);

    try {
      const updated = await updateWorkspace(session.accessToken, workspaceId, {
        module_config_json: mergeTrackingProfile(workspaceSnapshot, profileDraft),
      });
      setWorkspaceSnapshot(updated);
      setSettingsOpen(false);
      await refreshRuntimeState();
    } catch (error) {
      setErrorMessage(
        isApiClientError(error) ? error.message : "更新追踪设置时失败，请稍后再试。",
      );
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handleAskFollowUp(presetQuestion?: string) {
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
      setErrorMessage(
        isApiClientError(error) ? error.message : "这次追问没有成功，请稍后再试。",
      );
    } finally {
      setIsAsking(false);
    }
  }

  function goBack() {
    if (typeof window !== "undefined" && window.history.length > 1) {
      window.history.back();
      return;
    }
    window.location.href = "/";
  }

  if (!isReady) {
    return <div style={{ padding: 40 }}>正在进入 AI 热点追踪…</div>;
  }

  if (!session) {
    return <AuthRequired description="登录后才可以进入 AI 热点追踪。" />;
  }

  const activeFollowUps: AiFrontierFollowUpEntryRecord[] = activeRun?.follow_ups ?? [];
  const runtimeSummary = stateRecord?.latest_notify_reason ?? "系统会按当前节奏持续扫描，不会把平稳轮次刷成一堆记录。";

  return (
    <div
      style={{
        background:
          "radial-gradient(circle at 10% 10%, rgba(191, 219, 254, 0.44), transparent 28%), radial-gradient(circle at 88% 12%, rgba(224, 231, 255, 0.36), transparent 24%), #f7faff",
        height: "100svh",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "grid",
          gap: 16,
          gridTemplateRows: "auto auto minmax(0, 1fr)",
          height: "100svh",
          margin: "0 auto",
          maxWidth: 1760,
          padding: "26px 28px 22px",
        }}
      >
        <header
          style={{
            alignItems: "center",
            display: "flex",
            gap: 14,
            justifyContent: "space-between",
            minHeight: 44,
          }}
        >
          <div style={{ alignItems: "center", display: "flex", gap: 12 }}>
            <button onClick={goBack} style={ghostButtonStyle(false)} type="button">
              返回
            </button>
            <button
              aria-label="所有记录"
              onClick={() => setHistoryOpen(true)}
              style={iconButtonStyle(historyOpen)}
              type="button"
            >
              <span style={{ display: "grid", gap: 3, width: 15 }}>
                <span style={{ backgroundColor: "#0f172a", borderRadius: 999, height: 2, width: "100%" }} />
                <span style={{ backgroundColor: "#0f172a", borderRadius: 999, height: 2, width: "100%" }} />
                <span style={{ backgroundColor: "#0f172a", borderRadius: 999, height: 2, width: "100%" }} />
              </span>
            </button>
            <button
              aria-label="追踪设置"
              onClick={() => setSettingsOpen(true)}
              style={iconButtonStyle(settingsOpen)}
              type="button"
            >
              ⚙
            </button>
            <div style={{ display: "grid", gap: 4 }}>
              <strong style={{ color: "#0f172a", fontSize: 15, letterSpacing: "0.12em" }}>AI 热点追踪</strong>
              <span style={{ color: "#64748b", fontSize: 12 }}>
                面向大众 AI 用户的判断型简报
              </span>
            </div>
          </div>

          <div style={{ alignItems: "center", display: "flex", gap: 12 }}>
            {activeRun ? (
              <button
                onClick={() => setEvaluationMode(!evaluationMode)}
                style={ghostButtonStyle(false)}
                type="button"
              >
                {evaluationMode ? "返回简报" : "内部评测"}
              </button>
            ) : null}
            <button
              disabled={isRunning}
              onClick={() => void handleRunTracking()}
              style={primaryButtonStyle(isRunning)}
              type="button"
            >
              {isRunning ? "整理中…" : activeRun ? "获取新一轮" : "获取热点"}
            </button>
          </div>
        </header>

        {errorMessage ? (
          <div
            style={{
              backgroundColor: "rgba(185, 28, 28, 0.08)",
              border: "1px solid rgba(185, 28, 28, 0.14)",
              borderRadius: 18,
              color: "#991b1b",
              padding: "14px 16px",
            }}
          >
            {errorMessage}
          </div>
        ) : null}

        <section
          style={{
            ...surfaceStyle(),
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            padding: "18px 20px",
          }}
        >
          <RuntimeMeta label="关注方向" value={trackingProfile.enabled_categories.map((item) => CATEGORY_LABEL[item] ?? item).join(" · ")} />
          <RuntimeMeta label="扫描频率" value={CADENCE_LABEL[trackingProfile.cadence]} />
          <RuntimeMeta
            label="最近检查"
            value={isLoadingState ? "正在刷新…" : formatTime(stateRecord?.last_checked_at)}
          />
          <RuntimeMeta
            label="最近成功扫描"
            value={isLoadingState ? "正在刷新…" : formatTime(stateRecord?.last_successful_scan_at)}
          />
          <RuntimeMeta
            label="最近保存"
            value={isLoadingState ? "正在刷新…" : formatTime(stateRecord?.latest_saved_run_generated_at)}
          />
          <RuntimeMeta
            label="最近明显变化"
            value={isLoadingState ? "正在刷新…" : formatTime(stateRecord?.latest_meaningful_update_at)}
          />
          <RuntimeMeta
            label="下一次运行"
            value={trackingProfile.cadence === "manual" ? "仅手动" : formatTime(stateRecord?.next_due_at)}
          />
          <RuntimeMeta
            label="连续失败"
            value={String(stateRecord?.consecutive_failure_count ?? 0)}
          />
        </section>

        {!activeRun ? (
          <section
            style={{
              ...surfaceStyle(),
              alignItems: "center",
              display: "grid",
              gap: 22,
              justifyItems: "center",
              minHeight: 0,
              overflow: "hidden",
              padding: "48px 32px 42px",
              textAlign: "center",
            }}
          >
            <div style={{ display: "grid", gap: 18, justifyItems: "center", maxWidth: 960 }}>
              <span
                style={{
                  background: "linear-gradient(135deg, #0f172a 0%, #334155 48%, #2563eb 100%)",
                  backgroundClip: "text",
                  color: "transparent",
                  fontSize: "clamp(56px, 8vw, 104px)",
                  fontWeight: 800,
                  letterSpacing: "-0.08em",
                  lineHeight: 0.92,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                AI热点
              </span>
              <strong
                style={{
                  color: "#0f172a",
                  fontSize: "clamp(26px, 3.4vw, 44px)",
                  fontWeight: 700,
                  letterSpacing: "-0.04em",
                  lineHeight: 1.08,
                }}
              >
                最先看见变化的人，最先占据优势
              </strong>
              <p
                style={{
                  color: "#475569",
                  fontSize: 16,
                  lineHeight: 1.9,
                  margin: 0,
                  maxWidth: 720,
                }}
              >
                它会持续扫描高可信来源，筛出真正值得看的变化，并把结果收成一份可以继续追问的简报。
              </p>
            </div>

            <div
              style={{
                alignItems: "center",
                color: "#64748b",
                display: "flex",
                flexWrap: "wrap",
                gap: 16,
                justifyContent: "center",
              }}
            >
              {trackingProfile.enabled_categories.map((item) => (
                <span
                  key={item}
                  style={{
                    borderBottom: "1px solid rgba(148, 163, 184, 0.18)",
                    fontSize: 14,
                    fontWeight: 700,
                    paddingBottom: 6,
                  }}
                >
                  {CATEGORY_LABEL[item] ?? item}
                </span>
              ))}
            </div>

            <div style={{ color: "#64748b", fontSize: 14, lineHeight: 1.8 }}>
              {runtimeSummary}
            </div>
          </section>
        ) : evaluationMode ? (
          <section
            style={{
              display: "grid",
              gap: 18,
              gridTemplateColumns: "minmax(0, 1fr)",
              minHeight: 0,
              overflow: "hidden",
            }}
          >
            <div
              className={HIDDEN_SCROLL_CLASS}
              style={{
                ...surfaceStyle(),
                display: "grid",
                gap: 18,
                minHeight: 0,
                overflowY: "auto",
                padding: "24px 28px 32px",
              }}
            >
              <div style={{ display: "grid", gap: 10 }}>
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
                  <span style={priorityBadgeStyle(activeRun.delta.priority_level)}>
                    {PRIORITY_LABEL[activeRun.delta.priority_level]}
                  </span>
                  <span style={changeStateBadgeStyle(activeRun.delta.change_state)}>
                    {CHANGE_STATE_LABEL[activeRun.delta.change_state]}
                  </span>
                </div>
                <strong style={{ color: "#0f172a", fontSize: 30, lineHeight: 1.18 }}>
                  {activeRun.output.headline}
                </strong>
                <p style={{ color: "#475569", fontSize: 15, lineHeight: 1.85, margin: 0 }}>
                  这里只用于检查这一轮内部判断是否合理，不是面向普通用户的展示层。
                </p>
              </div>

              {isLoadingEvaluation ? (
                <div style={{ color: "#64748b", padding: "8px 0" }}>正在读取内部评测…</div>
              ) : evaluation ? (
                <>
                  <EvaluationSection
                    title="Replay 校准"
                    subtitle="这是固定回放样本，不依赖当前 run。它用来检查热点判断层有没有整体跑偏。"
                  >
                    {isLoadingReplayEvaluation ? (
                      <div style={{ color: "#64748b", fontSize: 14 }}>正在读取 replay 校准…</div>
                    ) : replayEvaluation ? (
                      <div style={{ display: "grid", gap: 14 }}>
                        <div
                          style={{
                            alignItems: "center",
                            display: "flex",
                            flexWrap: "wrap",
                            gap: 12,
                            justifyContent: "space-between",
                          }}
                        >
                          <div style={{ display: "grid", gap: 6 }}>
                            <strong style={{ color: "#0f172a", fontSize: 17 }}>
                              当前 replay suite {replayEvaluation.status === "pass" ? "通过" : "失败"}
                            </strong>
                            <span style={{ color: "#64748b", fontSize: 13 }}>
                              共 {replayEvaluation.total_case_count} 组 case · 通过{" "}
                              {replayEvaluation.passed_case_count} 组 · 失败{" "}
                              {replayEvaluation.failed_case_count} 组
                            </span>
                          </div>
                          <span
                            style={findingBadgeStyle(
                              replayEvaluation.status === "pass" ? "pass" : "fail",
                            )}
                          >
                            {replayEvaluation.status === "pass" ? "通过" : "失败"}
                          </span>
                        </div>

                        <div style={{ display: "grid", gap: 12 }}>
                          {replayEvaluation.cases.map((replayCase) => (
                            <div
                              key={replayCase.case_id}
                              style={{
                                backgroundColor: "rgba(255, 255, 255, 0.72)",
                                border: "1px solid rgba(148, 163, 184, 0.14)",
                                borderRadius: 18,
                                display: "grid",
                                gap: 12,
                                padding: "14px 16px",
                              }}
                            >
                              <div
                                style={{
                                  alignItems: "center",
                                  display: "flex",
                                  flexWrap: "wrap",
                                  gap: 10,
                                  justifyContent: "space-between",
                                }}
                              >
                                <div style={{ display: "grid", gap: 4 }}>
                                  <strong style={{ color: "#0f172a", fontSize: 15 }}>
                                    {replayCase.title}
                                  </strong>
                                  <span style={{ color: "#64748b", fontSize: 13, lineHeight: 1.7 }}>
                                    {replayCase.description}
                                  </span>
                                </div>
                                <span
                                  style={findingBadgeStyle(
                                    replayCase.status === "pass" ? "pass" : "fail",
                                  )}
                                >
                                  {replayCase.status === "pass" ? "通过" : "失败"}
                                </span>
                              </div>

                              <div style={{ display: "grid", gap: 10 }}>
                                {replayCase.steps.map((step) => (
                                  <div
                                    key={`${replayCase.case_id}-${step.label}`}
                                    style={{
                                      borderTop: "1px solid rgba(148, 163, 184, 0.12)",
                                      display: "grid",
                                      gap: 8,
                                      paddingTop: 10,
                                    }}
                                  >
                                    <div
                                      style={{
                                        alignItems: "center",
                                        display: "flex",
                                        flexWrap: "wrap",
                                        gap: 10,
                                        justifyContent: "space-between",
                                      }}
                                    >
                                      <strong style={{ color: "#0f172a", fontSize: 14 }}>
                                        {step.label}
                                      </strong>
                                      <div style={{ alignItems: "center", display: "flex", gap: 8 }}>
                                        <span style={{ color: "#64748b", fontSize: 12 }}>
                                          {CHANGE_STATE_LABEL[step.delta_change_state]}
                                          {step.notify_reason ? ` · ${step.notify_reason}` : ""}
                                        </span>
                                        <span
                                          style={findingBadgeStyle(
                                            step.status === "pass" ? "pass" : "fail",
                                          )}
                                        >
                                          {step.status === "pass" ? "通过" : "失败"}
                                        </span>
                                      </div>
                                    </div>
                                    {step.findings.some((finding) => finding.status !== "pass") ? (
                                      <div style={{ display: "grid", gap: 8 }}>
                                        {step.findings
                                          .filter((finding) => finding.status !== "pass")
                                          .map((finding) => (
                                            <div
                                              key={`${step.label}-${finding.code}`}
                                              style={{
                                                backgroundColor:
                                                  finding.status === "fail"
                                                    ? "rgba(185, 28, 28, 0.05)"
                                                    : "rgba(245, 158, 11, 0.08)",
                                                border:
                                                  finding.status === "fail"
                                                    ? "1px solid rgba(185, 28, 28, 0.10)"
                                                    : "1px solid rgba(245, 158, 11, 0.12)",
                                                borderRadius: 14,
                                                display: "grid",
                                                gap: 6,
                                                padding: "10px 12px",
                                              }}
                                            >
                                              <div
                                                style={{
                                                  alignItems: "center",
                                                  display: "flex",
                                                  gap: 8,
                                                  justifyContent: "space-between",
                                                }}
                                              >
                                                <strong style={{ color: "#0f172a", fontSize: 13 }}>
                                                  {finding.summary}
                                                </strong>
                                                <span style={findingBadgeStyle(finding.status)}>
                                                  {renderFindingStatusLabel(finding.status)}
                                                </span>
                                              </div>
                                            </div>
                                          ))}
                                      </div>
                                    ) : (
                                      <div style={{ color: "#64748b", fontSize: 12 }}>
                                        这一步的 replay 检查全部通过。
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div style={{ color: "#64748b", fontSize: 14 }}>当前还没有 replay 校准结果。</div>
                    )}
                  </EvaluationSection>

                  <EvaluationSection
                    title="判断检查"
                    subtitle="先看这一轮是否触发了核心判断护栏，再往下看细节。"
                  >
                    {evaluation.quality_checks.length ? (
                      <div style={{ display: "grid", gap: 12 }}>
                        {evaluation.quality_checks.map((finding) => (
                          <div
                            key={finding.code}
                            style={{
                              backgroundColor: "rgba(255, 255, 255, 0.72)",
                              border: "1px solid rgba(148, 163, 184, 0.14)",
                              borderRadius: 18,
                              display: "grid",
                              gap: 10,
                              padding: "14px 16px",
                            }}
                          >
                            <div
                              style={{
                                alignItems: "center",
                                display: "flex",
                                flexWrap: "wrap",
                                gap: 10,
                                justifyContent: "space-between",
                              }}
                            >
                              <strong style={{ color: "#0f172a", fontSize: 15 }}>
                                {finding.summary}
                              </strong>
                              <span style={findingBadgeStyle(finding.status)}>
                                {renderFindingStatusLabel(finding.status)}
                              </span>
                            </div>
                            {Object.keys(finding.details).length ? (
                              <div style={{ color: "#64748b", fontSize: 12, lineHeight: 1.8 }}>
                                {Object.entries(finding.details)
                                  .map(([key, value]) => `${key}: ${String(value)}`)
                                  .join(" · ")}
                              </div>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ color: "#64748b", fontSize: 14 }}>这一轮还没有生成判断检查结果。</div>
                    )}
                  </EvaluationSection>

                  <EvaluationSection
                    title="变化判断"
                    subtitle="看系统为什么把这一轮判成新增、延续、降温或平稳。"
                  >
                    <div
                      style={{
                        display: "grid",
                        gap: 14,
                        gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                      }}
                    >
                      <RuntimeMeta label="变化状态" value={CHANGE_STATE_LABEL[evaluation.delta.change_state]} />
                      <RuntimeMeta label="通知理由" value={evaluation.delta.notify_reason ?? "不触发提醒"} />
                      <RuntimeMeta
                        label="变化计数"
                        value={`新增 ${evaluation.delta.new_item_count} · 延续 ${evaluation.delta.continuing_item_count} · 降温 ${evaluation.delta.cooled_down_item_count}`}
                      />
                    </div>
                  </EvaluationSection>

                  <EvaluationSection
                    title="简报结果"
                    subtitle="确认最终给用户看到的简报，是否与内部判断一致。"
                  >
                    <div style={{ display: "grid", gap: 18 }}>
                      <div style={{ display: "grid", gap: 8 }}>
                        <strong style={{ color: "#0f172a", fontSize: 24 }}>{evaluation.output.headline}</strong>
                        <p style={{ color: "#334155", fontSize: 15, lineHeight: 1.8, margin: 0 }}>
                          {evaluation.output.summary}
                        </p>
                      </div>
                      <div style={{ display: "grid", gap: 14 }}>
                        {evaluation.output.signals.map((signal, index) => (
                          <div
                            key={`${signal.title}-${index}`}
                            style={{
                              borderBottom:
                                index === evaluation.output.signals.length - 1
                                  ? "none"
                                  : "1px solid rgba(148, 163, 184, 0.14)",
                              display: "grid",
                              gap: 8,
                              paddingBottom:
                                index === evaluation.output.signals.length - 1 ? 0 : 14,
                            }}
                          >
                            <strong style={{ color: "#0f172a", fontSize: 17 }}>{signal.title}</strong>
                            <span style={{ color: "#475569", fontSize: 14, lineHeight: 1.8 }}>{signal.summary}</span>
                            <span style={{ color: "#64748b", fontSize: 13, lineHeight: 1.8 }}>
                              {signal.why_now}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </EvaluationSection>

                  <EvaluationSection
                    title="排序结果"
                    subtitle="看哪几条 source item 被放到了更靠前的位置，以及原因。"
                  >
                    <div style={{ display: "grid", gap: 12 }}>
                      {evaluation.ranked_items.map((item) => (
                        <div
                          key={item.id}
                          style={{
                            borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
                            display: "grid",
                            gap: 8,
                            paddingBottom: 12,
                          }}
                        >
                          <div
                            style={{
                              alignItems: "center",
                              display: "flex",
                              gap: 10,
                              justifyContent: "space-between",
                            }}
                          >
                            <strong style={{ color: "#0f172a", fontSize: 15 }}>{item.title}</strong>
                            <span style={{ color: "#64748b", fontSize: 12 }}>
                              {item.rank_score.toFixed(2)}
                            </span>
                          </div>
                          <span style={{ color: "#475569", fontSize: 13, lineHeight: 1.7 }}>
                            {item.rank_reason}
                          </span>
                          <div style={{ color: "#64748b", fontSize: 12, lineHeight: 1.7 }}>
                            新颖度 {item.score_breakdown.novelty.toFixed(2)} · 新鲜度{" "}
                            {item.score_breakdown.freshness.toFixed(2)} · 可信度{" "}
                            {item.score_breakdown.authority.toFixed(2)} · 相关性{" "}
                            {item.score_breakdown.relevance.toFixed(2)} · 影响 {" "}
                            {item.score_breakdown.impact.toFixed(2)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </EvaluationSection>

                  <EvaluationSection
                    title="聚类结果"
                    subtitle="检查哪些来源被归并成同一个可读信号。"
                  >
                    <div style={{ display: "grid", gap: 12 }}>
                      {evaluation.clustered_signals.map((cluster: AiHotTrackerSignalClusterRecord) => (
                        <div
                          key={cluster.cluster_id}
                          style={{
                            borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
                            display: "grid",
                            gap: 6,
                            paddingBottom: 12,
                          }}
                        >
                          <strong style={{ color: "#0f172a", fontSize: 15 }}>{cluster.title}</strong>
                          <span style={{ color: "#475569", fontSize: 13 }}>
                            {cluster.priority_level} · {cluster.category} · {cluster.source_labels.join(" · ")}
                          </span>
                          <span style={{ color: "#64748b", fontSize: 12 }}>
                            {cluster.is_new ? "新增" : cluster.is_cooling ? "降温" : "延续"} ·
                            event {cluster.event_id}
                          </span>
                        </div>
                      ))}
                    </div>
                  </EvaluationSection>

                  <EvaluationSection
                    title="事件记忆"
                    subtitle="看系统是否在长期记住一个信号，而不是只看上一轮快照。"
                  >
                    <div style={{ display: "grid", gap: 12 }}>
                      {evaluation.event_memories.map((memory: AiHotTrackerSignalMemoryRecord) => (
                        <div
                          key={memory.event_id}
                          style={{
                            borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
                            display: "grid",
                            gap: 6,
                            paddingBottom: 12,
                          }}
                        >
                          <strong style={{ color: "#0f172a", fontSize: 15 }}>{memory.title}</strong>
                          <span style={{ color: "#475569", fontSize: 13 }}>
                            {memory.continuity_state} · {memory.activity_state} · {memory.latest_priority_level}
                          </span>
                          <span style={{ color: "#64748b", fontSize: 12 }}>
                            首次 {formatTime(memory.first_seen_at)} · 最近出现 {formatTime(memory.last_seen_at)}
                          </span>
                          <span style={{ color: "#64748b", fontSize: 12 }}>
                            连续轮次 {memory.streak_count}
                            {memory.cooling_since ? ` · 降温开始 ${formatTime(memory.cooling_since)}` : ""}
                            {memory.superseded_by_event_id
                              ? ` · 已被 ${memory.superseded_by_event_id} 替代`
                              : ""}
                          </span>
                          {memory.note ? (
                            <span style={{ color: "#475569", fontSize: 12, lineHeight: 1.75 }}>
                              {memory.note}
                            </span>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </EvaluationSection>

                  <EvaluationSection
                    title="来源失败"
                    subtitle="这里必须诚实暴露来源失败，不能用错误的兜底文案掩盖。"
                  >
                    {evaluation.source_failures.length ? (
                      <div style={{ display: "grid", gap: 10 }}>
                        {evaluation.source_failures.map((failure: AiHotTrackerSourceFailureRecord) => (
                          <div
                            key={`${failure.source_id}-${failure.message}`}
                            style={{
                              backgroundColor: "rgba(185, 28, 28, 0.05)",
                              border: "1px solid rgba(185, 28, 28, 0.12)",
                              borderRadius: 16,
                              color: "#991b1b",
                              display: "grid",
                              gap: 6,
                              padding: "12px 14px",
                            }}
                          >
                            <strong style={{ fontSize: 14 }}>{failure.source_label}</strong>
                            <span style={{ fontSize: 13, lineHeight: 1.7 }}>{failure.message}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ color: "#64748b", fontSize: 14 }}>这一轮没有来源失败。</div>
                    )}
                  </EvaluationSection>

                  <EvaluationSection
                    title="Agent 轨迹"
                    subtitle="看这一轮内部各角色做了什么。这里只做检查，不面向普通用户。"
                  >
                    <div style={{ display: "grid", gap: 12 }}>
                      {evaluation.agent_trace.map((trace, index) => (
                        <div
                          key={`${trace.role}-${index}`}
                          style={{
                            borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
                            display: "grid",
                            gap: 6,
                            paddingBottom: 12,
                          }}
                        >
                          <div
                            style={{
                              alignItems: "center",
                              display: "flex",
                              gap: 10,
                              justifyContent: "space-between",
                            }}
                          >
                            <strong style={{ color: "#0f172a", fontSize: 15 }}>{renderRoleLabel(trace.role)}</strong>
                            <span style={{ color: "#64748b", fontSize: 12 }}>{trace.status}</span>
                          </div>
                          <span style={{ color: "#475569", fontSize: 13, lineHeight: 1.75 }}>
                            {trace.summary}
                          </span>
                        </div>
                      ))}
                    </div>
                  </EvaluationSection>
                </>
              ) : null}
            </div>
          </section>
        ) : (
          <section
            style={{
              display: "grid",
              gap: 18,
              gridTemplateColumns: "minmax(0, 1.38fr) minmax(360px, 0.82fr)",
              minHeight: 0,
              overflow: "hidden",
            }}
          >
            <section
              style={{
                ...surfaceStyle(),
                display: "grid",
                gridTemplateRows: "auto minmax(0, 1fr)",
                minHeight: 0,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
                  display: "grid",
                  gap: 14,
                  padding: "26px 28px 20px",
                }}
              >
                <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
                  <span style={priorityBadgeStyle(activeRun.delta.priority_level)}>
                    {PRIORITY_LABEL[activeRun.delta.priority_level]}
                  </span>
                  <span style={changeStateBadgeStyle(activeRun.delta.change_state)}>
                    {CHANGE_STATE_LABEL[activeRun.delta.change_state]}
                  </span>
                  <span style={{ color: "#64748b", fontSize: 13 }}>
                    {formatTime(activeRun.generated_at)}
                  </span>
                </div>
                <div style={{ display: "grid", gap: 10 }}>
                  <strong
                    style={{
                      color: "#0f172a",
                      fontSize: "clamp(28px, 3.2vw, 44px)",
                      fontWeight: 800,
                      letterSpacing: "-0.05em",
                      lineHeight: 1.02,
                    }}
                  >
                    {activeRun.output.headline}
                  </strong>
                  <p
                    style={{
                      color: "#334155",
                      fontSize: 16,
                      lineHeight: 1.88,
                      margin: 0,
                      maxWidth: 900,
                    }}
                  >
                    {activeRun.output.summary}
                  </p>
                  <span style={{ color: "#64748b", fontSize: 13, lineHeight: 1.75 }}>
                    {activeRun.delta.notify_reason ?? runtimeSummary}
                  </span>
                </div>
              </div>

              <div
                className={HIDDEN_SCROLL_CLASS}
                style={{
                  display: "grid",
                  gap: 24,
                  minHeight: 0,
                  overflowY: "auto",
                  padding: "26px 28px 34px",
                }}
              >
                <section style={{ display: "grid", gap: 18 }}>
                  <span
                    style={{
                      color: "#64748b",
                      fontSize: 12,
                      fontWeight: 800,
                      letterSpacing: "0.12em",
                    }}
                  >
                    正在发生
                  </span>
                  <div style={{ display: "grid", gap: 18 }}>
                    {activeRun.output.signals.map((signal, index) => (
                      <div
                        key={`${signal.title}-${index}`}
                        style={{
                          borderTop: index === 0 ? "none" : "1px solid rgba(148, 163, 184, 0.14)",
                          paddingTop: index === 0 ? 0 : 18,
                        }}
                      >
                        <SignalItem
                          active={currentFocus?.label === signal.title}
                          onFocus={() =>
                            setCurrentFocus({
                              context: [signal.summary, signal.why_now, signal.impact].join("\n\n"),
                              label: signal.title,
                            })
                          }
                          signal={signal}
                          sourceItems={activeRun.source_items}
                        />
                      </div>
                    ))}
                  </div>
                </section>

                {activeRun.output.keep_watching.length ? (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.14)",
                      display: "grid",
                      gap: 16,
                      paddingTop: 22,
                    }}
                  >
                    <span
                      style={{
                        color: "#64748b",
                        fontSize: 12,
                        fontWeight: 800,
                        letterSpacing: "0.12em",
                      }}
                    >
                      继续关注
                    </span>
                    <div style={{ display: "grid", gap: 8 }}>
                      {activeRun.output.keep_watching.map((item, index) => (
                        <div
                          key={`${item.title}-${index}`}
                          style={{
                            borderTop: index === 0 ? "none" : "1px solid rgba(148, 163, 184, 0.14)",
                            paddingTop: index === 0 ? 0 : 12,
                          }}
                        >
                          <KeepWatchingItem
                            active={currentFocus?.label === item.title}
                            item={item}
                            onFocus={() =>
                              setCurrentFocus({
                                context: item.reason,
                                label: item.title,
                              })
                            }
                            sourceItems={activeRun.source_items}
                          />
                        </div>
                      ))}
                    </div>
                  </section>
                ) : null}

                {activeRun.output.blindspots.length ? (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.14)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span
                      style={{
                        color: "#64748b",
                        fontSize: 12,
                        fontWeight: 800,
                        letterSpacing: "0.12em",
                      }}
                    >
                      还需要补看的地方
                    </span>
                    <div style={{ display: "grid", gap: 10 }}>
                      {activeRun.output.blindspots.map((blindspot, index) => (
                        <div
                          key={`${blindspot}-${index}`}
                          style={{
                            borderLeft: "2px solid rgba(148, 163, 184, 0.34)",
                            color: "#475569",
                            fontSize: 14,
                            lineHeight: 1.8,
                            paddingLeft: 14,
                          }}
                        >
                          {blindspot}
                        </div>
                      ))}
                    </div>
                  </section>
                ) : null}

                {activeRun.output.reference_sources.length ? (
                  <section
                    style={{
                      borderTop: "1px solid rgba(148, 163, 184, 0.14)",
                      display: "grid",
                      gap: 14,
                      paddingTop: 22,
                    }}
                  >
                    <span
                      style={{
                        color: "#64748b",
                        fontSize: 12,
                        fontWeight: 800,
                        letterSpacing: "0.12em",
                      }}
                    >
                      参考来源
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
                ) : null}
              </div>
            </section>

            <aside
              style={{
                ...surfaceStyle(),
                display: "grid",
                gridTemplateRows: "auto auto minmax(0, 1fr) auto",
                minHeight: 0,
                overflow: "hidden",
                padding: "24px 22px 18px",
              }}
            >
              <div style={{ display: "grid", gap: 6 }}>
                <span
                  style={{
                    color: "#64748b",
                    fontSize: 12,
                    fontWeight: 800,
                    letterSpacing: "0.12em",
                  }}
                >
                  追问
                </span>
                <strong style={{ color: "#0f172a", fontSize: 18, lineHeight: 1.35 }}>
                  {currentFocus?.label ?? "整份简报"}
                </strong>
                <span style={{ color: "#64748b", fontSize: 13, lineHeight: 1.8 }}>
                  这里只围绕当前简报和它的来源回答，不会漂移成泛聊天。
                </span>
              </div>

              <div
                style={{
                  borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 8,
                  paddingBottom: 14,
                  paddingTop: 16,
                }}
              >
                {FOLLOW_UP_PRESETS.map((preset) => (
                  <button
                    disabled={isAsking}
                    key={preset}
                    onClick={() => void handleAskFollowUp(preset)}
                    style={{
                      backgroundColor: "rgba(241, 245, 249, 0.88)",
                      border: "1px solid rgba(148, 163, 184, 0.14)",
                      borderRadius: 999,
                      color: "#0f172a",
                      cursor: "pointer",
                      fontSize: 11,
                      fontWeight: 800,
                      padding: "7px 10px",
                    }}
                    type="button"
                  >
                    {preset}
                  </button>
                ))}
              </div>

              <div
                className={HIDDEN_SCROLL_CLASS}
                ref={followUpScrollRef}
                style={{
                  display: "grid",
                  gap: 14,
                  minHeight: 0,
                  overflowY: "auto",
                  padding: "18px 2px 18px 0",
                }}
              >
                {activeFollowUps.map((entry, index) => (
                  <div key={`${entry.question}-${index}`} style={{ display: "grid", gap: 10 }}>
                    <div style={{ display: "flex", justifyContent: "flex-end" }}>
                      <div
                        style={{
                          backgroundColor: "#0f172a",
                          borderRadius: "20px 20px 6px 20px",
                          color: "#f8fbff",
                          lineHeight: 1.72,
                          maxWidth: "88%",
                          padding: "11px 13px",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {entry.question}
                      </div>
                    </div>
                    <div style={{ display: "flex", justifyContent: "flex-start" }}>
                      <div style={{ display: "grid", gap: 6, maxWidth: "92%" }}>
                        <div
                          style={{
                            backgroundColor: "rgba(241, 245, 249, 0.92)",
                            border: "1px solid rgba(148, 163, 184, 0.14)",
                            borderRadius: "20px 20px 20px 6px",
                            color: "#334155",
                            lineHeight: 1.78,
                            padding: "11px 13px",
                            whiteSpace: "pre-wrap",
                          }}
                        >
                          {entry.answer}
                        </div>
                        {buildFollowUpGroundingSummary(entry) ? (
                          <span
                            style={{
                              color: "#94a3b8",
                              fontSize: 11,
                              lineHeight: 1.7,
                              paddingLeft: 4,
                            }}
                          >
                            回答依据：{buildFollowUpGroundingSummary(entry)}
                          </span>
                        ) : null}
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
                          lineHeight: 1.72,
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
                          lineHeight: 1.78,
                          maxWidth: "78%",
                          padding: "11px 13px",
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
                          lineHeight: 1.72,
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
                          lineHeight: 1.78,
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

                {!activeFollowUps.length && !pendingQuestion && !streamingReply ? (
                  <div style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.9 }}>
                    你可以围绕整份简报，也可以点选左侧某条信号后继续追问。
                  </div>
                ) : null}
              </div>

              <div
                style={{
                  borderTop: "1px solid rgba(148, 163, 184, 0.14)",
                  display: "grid",
                  gap: 10,
                  paddingTop: 16,
                }}
              >
                <textarea
                  onChange={(event) => setFollowUpInput(event.target.value)}
                  placeholder="继续追问当前简报"
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
                    onClick={() => void handleAskFollowUp()}
                    style={primaryButtonStyle(isAsking || !!pendingQuestion || !followUpInput.trim())}
                    type="button"
                  >
                    {isAsking ? "发送中…" : "发送"}
                  </button>
                </div>
              </div>
            </aside>
          </section>
        )}

        <div
          onClick={() => setHistoryOpen(false)}
          style={{
            backgroundColor: historyOpen ? "rgba(15, 23, 42, 0.16)" : "transparent",
            inset: 0,
            pointerEvents: historyOpen ? "auto" : "none",
            position: "fixed",
            transition: "background-color 220ms ease",
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
              transform: historyOpen ? "translateX(0)" : "translateX(-108%)",
              transition: "transform 220ms ease",
              width: 360,
            }}
          >
            <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
              <div style={{ display: "grid", gap: 4 }}>
                <strong style={{ color: "#0f172a", fontSize: 22 }}>所有记录</strong>
                <span style={{ color: "#64748b", fontSize: 12 }}>
                  {orderedRuns.length ? `${orderedRuns.length} 条已保存记录` : "还没有保存记录"}
                </span>
              </div>
              <button
                aria-label="关闭"
                onClick={() => setHistoryOpen(false)}
                style={iconButtonStyle(false)}
                type="button"
              >
                ×
              </button>
            </div>

            <div
              className={HIDDEN_SCROLL_CLASS}
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
                  <HistoryRow
                    active={activeRun?.id === run.id}
                    confirmDelete={deleteConfirmId === run.id}
                    key={run.id}
                    onCancelDelete={() => setDeleteConfirmId(null)}
                    onDeleteConfirm={() => void handleDeleteRun(run.id)}
                    onDeleteRequest={() => setDeleteConfirmId(run.id)}
                    onOpen={() => {
                      setActiveRunId(run.id);
                      setHistoryOpen(false);
                      setDeleteConfirmId(null);
                    }}
                    run={run}
                  />
                ))
              ) : (
                <div style={{ color: "#64748b", lineHeight: 1.8, padding: 18 }}>
                  主动获取过的热点简报会保存在这里。
                </div>
              )}
            </div>
          </aside>
        </div>

        <div
          onClick={() => setSettingsOpen(false)}
          style={{
            backgroundColor: settingsOpen ? "rgba(15, 23, 42, 0.16)" : "transparent",
            inset: 0,
            pointerEvents: settingsOpen ? "auto" : "none",
            position: "fixed",
            transition: "background-color 220ms ease",
            zIndex: 61,
          }}
        >
          <aside
            onClick={(event) => event.stopPropagation()}
            style={{
              backgroundColor: "rgba(248, 251, 255, 0.98)",
              borderLeft: "1px solid rgba(148, 163, 184, 0.18)",
              boxShadow: "-18px 0 40px rgba(15, 23, 42, 0.08)",
              display: "grid",
              gap: 22,
              height: "100%",
              maxWidth: "calc(100vw - 28px)",
              padding: "28px 22px 22px",
              position: "absolute",
              right: 0,
              top: 0,
              transform: settingsOpen ? "translateX(0)" : "translateX(108%)",
              transition: "transform 220ms ease",
              width: 380,
            }}
          >
            <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
              <div style={{ display: "grid", gap: 4 }}>
                <strong style={{ color: "#0f172a", fontSize: 22 }}>追踪设置</strong>
                <span style={{ color: "#64748b", fontSize: 12 }}>
                  这里只保留关注方向、频率和提醒阈值。
                </span>
              </div>
              <button
                aria-label="关闭"
                onClick={() => setSettingsOpen(false)}
                style={iconButtonStyle(false)}
                type="button"
              >
                ×
              </button>
            </div>

            <div className={HIDDEN_SCROLL_CLASS} style={{ display: "grid", gap: 18, minHeight: 0, overflowY: "auto" }}>
              <div style={{ display: "grid", gap: 8 }}>
                <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.08em" }}>
                  扫描频率
                </span>
                <div style={{ display: "grid", gap: 10 }}>
                  {(["manual", "daily", "twice_daily", "weekly"] as const).map((cadence) => (
                    <button
                      key={cadence}
                      onClick={() => setProfileDraft((current) => ({ ...current, cadence }))}
                      style={{
                        alignItems: "center",
                        backgroundColor:
                          profileDraft.cadence === cadence ? "rgba(15, 23, 42, 0.06)" : "rgba(255, 255, 255, 0.72)",
                        border: "1px solid rgba(148, 163, 184, 0.16)",
                        borderRadius: 18,
                        color: "#0f172a",
                        cursor: "pointer",
                        display: "flex",
                        fontSize: 14,
                        fontWeight: 700,
                        justifyContent: "space-between",
                        padding: "12px 14px",
                      }}
                      type="button"
                    >
                      <span>{CADENCE_LABEL[cadence]}</span>
                      {profileDraft.cadence === cadence ? <span>✓</span> : null}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.08em" }}>
                  关注方向
                </span>
                <div style={{ display: "grid", gap: 10 }}>
                  {Object.entries(CATEGORY_LABEL).map(([category, label]) => {
                    const active = profileDraft.enabled_categories.includes(category);
                    return (
                      <button
                        key={category}
                        onClick={() =>
                          setProfileDraft((current) => {
                            const nextCategories = active
                              ? current.enabled_categories.filter((item) => item !== category)
                              : [...current.enabled_categories, category];

                            return {
                              ...current,
                              enabled_categories: nextCategories.length
                                ? nextCategories
                                : current.enabled_categories,
                            };
                          })
                        }
                        style={{
                          alignItems: "center",
                          backgroundColor: active ? "rgba(15, 23, 42, 0.06)" : "rgba(255, 255, 255, 0.72)",
                          border: "1px solid rgba(148, 163, 184, 0.16)",
                          borderRadius: 18,
                          color: "#0f172a",
                          cursor: "pointer",
                          display: "flex",
                          fontSize: 14,
                          fontWeight: 700,
                          justifyContent: "space-between",
                          padding: "12px 14px",
                        }}
                        type="button"
                      >
                        <span>{label}</span>
                        {active ? <span>✓</span> : null}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div style={{ display: "grid", gap: 10 }}>
                <div style={{ display: "grid", gap: 4 }}>
                  <span style={{ color: "#64748b", fontSize: 12, fontWeight: 800, letterSpacing: "0.08em" }}>
                    提醒阈值
                  </span>
                  <span style={{ color: "#475569", fontSize: 13, lineHeight: 1.7 }}>
                    至少出现多少条中高优先级新增变化，系统才会把自动轮次保存成一条新记录。
                  </span>
                </div>
                <input
                  max={10}
                  min={1}
                  onChange={(event) =>
                    setProfileDraft((current) => ({
                      ...current,
                      alert_threshold: Math.min(10, Math.max(1, Number(event.target.value) || 1)),
                    }))
                  }
                  style={{ width: "100%" }}
                  type="range"
                  value={profileDraft.alert_threshold}
                />
                <strong style={{ color: "#0f172a", fontSize: 22 }}>{profileDraft.alert_threshold}</strong>
              </div>
            </div>

            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                onClick={() => setSettingsOpen(false)}
                style={ghostButtonStyle(false)}
                type="button"
              >
                取消
              </button>
              <button
                disabled={isSavingProfile}
                onClick={() => void handleSaveProfile()}
                style={primaryButtonStyle(isSavingProfile)}
                type="button"
              >
                {isSavingProfile ? "保存中…" : "保存设置"}
              </button>
            </div>
          </aside>
        </div>

        <style jsx global>{`
          .${HIDDEN_SCROLL_CLASS} {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }

          .${HIDDEN_SCROLL_CLASS}::-webkit-scrollbar {
            display: none;
            height: 0;
            width: 0;
          }
        `}</style>
      </div>
    </div>
  );
}

