"use client";

import type { CSSProperties, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import { getWorkbenchPanelHref, type WorkbenchPanelId } from "../../lib/navigation";
import type {
  JobHiringPacketContinuationDraft,
  JobTaskType,
  ModuleType,
  SupportCaseContinuationDraft,
  SupportTaskType,
  Workspace,
} from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import ChatPanel from "../chat/chat-panel";
import DocumentManager from "../documents/document-manager";
import EvalManager from "../evals/eval-manager";
import JobAssistantActionPanel from "../job/job-assistant-action-panel";
import JobHiringWorkbenchSection from "../job/job-hiring-workbench-section";
import PublicDemoWorkbenchContinuityNote from "../public-demo/public-demo-workbench-continuity-note";
import ResearchAssistantPanel from "../research/research-assistant-panel";
import SupportCaseWorkbenchSection from "../support/support-case-workbench-section";
import SupportCopilotPanel from "../support/support-copilot-panel";
import SectionCard from "../ui/section-card";
import MetricsPanel from "./metrics-panel";
import ObservabilityPanel from "./observability-panel";

type WorkspaceWorkbenchPanelProps = {
  workspaceId: string;
  initialPanel?: WorkbenchPanelId;
};

type SupportingSurface = "documents" | "tasks" | "analytics" | null;
type RequestedActionKey =
  | "support:ticket_summary"
  | "support:reply_draft"
  | "job:jd_summary"
  | "job:resume_match"
  | "research:open"
  | null;

type SupportingSurfaceMeta = {
  title: string;
  description: string;
  width?: string;
};

type FocusMeta = {
  assistantLabel: string;
  workflowLabel: string;
  introTitle: string;
  introBody: string;
  defaultTaskLabel: string;
  placeholder: string;
  promptSuggestions: string[];
  outputHeading: string;
  outputDescription: string;
  analyticsDescription: string;
  headerLead: string;
};

type QuickAction = {
  key: RequestedActionKey;
  label: string;
  description: string;
};

type DocumentStatusSummary = {
  totalCount: number;
  readyCount: number;
  hasFailed: boolean;
  latestDocumentTitle: string | null;
};

type ConversationStatusSummary = {
  entryCount: number;
  isSubmitting: boolean;
  currentDraft: string;
  lastTraceId: string | null;
};

const MODULE_PRODUCT_NAMES: Record<ModuleType, string> = {
  research: "Research Assistant",
  support: "Support Copilot",
  job: "Job Assistant",
};

const pillButtonStyle: CSSProperties = {
  alignItems: "center",
  backgroundColor: "#ffffff",
  border: "1px solid #cbd5e1",
  borderRadius: 999,
  color: "#0f172a",
  display: "inline-flex",
  fontWeight: 700,
  justifyContent: "center",
  minHeight: 40,
  padding: "0 14px",
};

const sideCardStyle: CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #dbe4f0",
  borderRadius: 20,
  display: "grid",
  gap: 14,
  padding: 18,
};

function getModuleDisplayName(moduleType?: string | null): string {
  if (!moduleType) {
    return "未配置模块";
  }

  return MODULE_PRODUCT_NAMES[moduleType as ModuleType] ?? moduleType;
}

function getSupportingSurface(initialPanel?: WorkbenchPanelId): SupportingSurface {
  if (initialPanel === "documents") {
    return "documents";
  }
  if (initialPanel === "tasks") {
    return "tasks";
  }
  if (initialPanel === "analytics") {
    return "analytics";
  }
  return null;
}

function getFocusMeta(workspace: Workspace | null): FocusMeta {
  if (!workspace || workspace.module_type === "research") {
    return {
      assistantLabel: "Research Assistant",
      workflowLabel: "研究工作流",
      introTitle: "从一个研究问题开始",
      introBody: "先点一个快捷提示词，或直接输入问题，然后开始分析。",
      defaultTaskLabel: "围绕当前资料形成研究判断",
      placeholder: "例如：请基于当前资料总结最重要的市场信号，并指出还缺哪些证据才能形成正式结论。",
      promptSuggestions: [
        "请先总结当前资料里最重要的研究发现。",
        "请告诉我现在最缺哪些资料，才能继续往下分析。",
        "请判断这批资料里有哪些结论还不够稳，需要进一步核对。",
      ],
      outputHeading: "正式输出",
      outputDescription: "确认判断后，再生成研究摘要或正式报告。",
      analyticsDescription: "需要解释过程时，再进入 trace、readiness 与分析。",
      headerLead: "围绕资料、分析过程和正式输出推进这一轮研究。",
    };
  }

  if (workspace.module_type === "support") {
    return {
      assistantLabel: "Support Copilot",
      workflowLabel: "Support 流程",
      introTitle: "先把 case 判断清楚",
      introBody: "从一个关键问题开始，确认事实与证据，再决定是否生成摘要、回复或继续升级。",
      defaultTaskLabel: "围绕当前 case 推进下一步判断",
      placeholder: "例如：请先总结这个 case 当前最关键的事实，再告诉我应该继续跟进、生成回复还是升级处理。",
      promptSuggestions: [
        "请先总结当前 case 的核心问题和证据。",
        "如果现在要直接回复客户，最需要先确认什么？",
        "这个 case 现在更适合继续跟进，还是应该准备升级？",
      ],
      outputHeading: "Case 产出",
      outputDescription: "完成一轮判断后，再生成工单摘要、回复草稿或继续已有 case。",
      analyticsDescription: "需要复盘 trace、readiness 或评测时再打开分析。",
      headerLead: "围绕 case 事实、回复和升级路径推进这一轮支持工作。",
    };
  }

  return {
    assistantLabel: "Job Assistant",
    workflowLabel: "招聘判断流程",
    introTitle: "先把岗位和候选池判断清楚",
    introBody: "从一个招聘判断问题开始，再决定是继续评审候选人还是刷新 shortlist。",
    defaultTaskLabel: "围绕当前招聘包形成下一步判断",
    placeholder: "例如：请先总结这个招聘包当前最大的判断风险，再告诉我应该继续评审候选人还是刷新 shortlist。",
    promptSuggestions: [
      "请先总结这个招聘包当前最大的判断风险。",
      "如果现在要继续推进 shortlist，最缺什么材料？",
      "基于现有资料，这个岗位和候选池最值得先核对什么？",
    ],
    outputHeading: "正式判断",
    outputDescription: "确认判断后，再生成岗位摘要、评审候选人或刷新 shortlist。",
    analyticsDescription: "分析只在需要解释结果、trace 或 readiness 时才展开。",
    headerLead: "围绕岗位要求、候选池和 shortlist 推进这一轮招聘判断。",
  };
}

function getQuickActions(workspace: Workspace | null): QuickAction[] {
  if (!workspace || workspace.module_type === "research") {
    return [
      {
        key: "research:open",
        label: "生成研究摘要 / 报告",
        description: "把当前分析整理成正式研究输出。",
      },
    ];
  }

  if (workspace.module_type === "support") {
    return [
      {
        key: "support:ticket_summary",
        label: "生成工单摘要",
        description: "梳理 case 的问题、证据与判断。",
      },
      {
        key: "support:reply_draft",
        label: "生成回复草稿",
        description: "基于当前资料生成回复草稿。",
      },
    ];
  }

  return [
    {
      key: "job:jd_summary",
      label: "生成岗位摘要",
      description: "收清岗位要求、背景和缺口。",
    },
    {
      key: "job:resume_match",
      label: "评审候选人 / 刷新 shortlist",
      description: "继续当前招聘包并推进 shortlist。",
    },
  ];
}

function getSupportingSurfaceMeta(surface: SupportingSurface, moduleType?: string | null): SupportingSurfaceMeta {
  if (surface === "documents") {
    return {
      title: "资料库",
      description: "这里只在需要补资料、检查状态或手动重建索引时展开。",
      width: "min(560px, 100vw)",
    };
  }

  if (surface === "tasks") {
    if (moduleType === "support") {
      return {
        title: "Case 产出与跟进",
        description: "继续已有 case，或生成工单摘要和回复草稿。",
        width: "min(660px, 100vw)",
      };
    }

    if (moduleType === "job") {
      return {
        title: "招聘判断与 shortlist",
        description: "继续已有招聘包，或推进岗位对齐、候选人评审和 shortlist。",
        width: "min(660px, 100vw)",
      };
    }

    return {
      title: "正式研究输出",
      description: "这里保留研究摘要和正式报告等结构化产出。",
      width: "min(660px, 100vw)",
    };
  }

  if (surface === "analytics") {
    return {
      title: "分析与轨迹",
      description: "这里只在需要解释系统行为时展开，不和主流程争夺注意力。",
      width: "min(620px, 100vw)",
    };
  }

  return {
    title: "主工作台",
    description: "当前只显示主分析流程。",
  };
}

function getRequestedSupportTaskType(action: RequestedActionKey): SupportTaskType | null {
  if (action === "support:ticket_summary") {
    return "ticket_summary";
  }
  if (action === "support:reply_draft") {
    return "reply_draft";
  }
  return null;
}

function getRequestedJobTaskType(action: RequestedActionKey): JobTaskType | null {
  if (action === "job:jd_summary") {
    return "jd_summary";
  }
  if (action === "job:resume_match") {
    return "resume_match";
  }
  return null;
}

function SupportTaskWorkbench({ requestedAction, workspaceId }: { requestedAction: RequestedActionKey; workspaceId: string }) {
  const { session } = useAuthSession();
  const [continuationDraft, setContinuationDraft] = useState<SupportCaseContinuationDraft | null>(null);

  if (!session) {
    return null;
  }

  return (
    <>
      <PublicDemoWorkbenchContinuityNote moduleType="support" />
      <SupportCaseWorkbenchSection
        accessToken={session.accessToken}
        onContinueCase={(draft) => setContinuationDraft(draft)}
        onOpenTask={(taskId) => {
          if (typeof window !== "undefined") {
            window.location.hash = `task-${taskId}`;
          }
        }}
        workspaceId={workspaceId}
      />
      <SupportCopilotPanel
        continuationDraft={continuationDraft}
        onContinuationHandled={() => setContinuationDraft(null)}
        requestedTaskType={getRequestedSupportTaskType(requestedAction)}
        workspaceId={workspaceId}
      />
    </>
  );
}

function JobTaskWorkbench({ requestedAction, workspaceId }: { requestedAction: RequestedActionKey; workspaceId: string }) {
  const { session } = useAuthSession();
  const [continuationDraft, setContinuationDraft] = useState<JobHiringPacketContinuationDraft | null>(null);

  if (!session) {
    return null;
  }

  return (
    <>
      <PublicDemoWorkbenchContinuityNote moduleType="job" />
      <JobHiringWorkbenchSection
        accessToken={session.accessToken}
        onContinuePacket={(draft) => setContinuationDraft(draft)}
        onOpenTask={(taskId) => {
          if (typeof window !== "undefined") {
            window.location.hash = `job-task-${taskId}`;
          }
        }}
        workspaceId={workspaceId}
      />
      <JobAssistantActionPanel
        continuationDraft={continuationDraft}
        onContinuationHandled={() => setContinuationDraft(null)}
        requestedTaskType={getRequestedJobTaskType(requestedAction)}
        workspaceId={workspaceId}
      />
    </>
  );
}

function ResearchTaskWorkbench({ workspaceId }: { workspaceId: string }) {
  return <ResearchAssistantPanel workspaceId={workspaceId} />;
}

function TaskWorkbenchByModule({
  requestedAction,
  workspace,
  workspaceId,
}: {
  requestedAction: RequestedActionKey;
  workspace: Workspace | null;
  workspaceId: string;
}) {
  if (!workspace) {
    return <SectionCard title="正式输出">正在加载当前模块...</SectionCard>;
  }

  if (workspace.module_type === "support") {
    return <SupportTaskWorkbench requestedAction={requestedAction} workspaceId={workspaceId} />;
  }

  if (workspace.module_type === "job") {
    return <JobTaskWorkbench requestedAction={requestedAction} workspaceId={workspaceId} />;
  }

  return <ResearchTaskWorkbench workspaceId={workspaceId} />;
}

function CollapsibleAnalyticsSection({
  children,
  description,
  open = false,
  title,
}: {
  children: ReactNode;
  description: string;
  open?: boolean;
  title: string;
}) {
  return (
    <details
      open={open}
      style={{
        backgroundColor: "#ffffff",
        border: "1px solid #dbe4f0",
        borderRadius: 18,
        padding: 14,
      }}
    >
      <summary style={{ color: "#0f172a", cursor: "pointer", fontWeight: 700 }}>{title}</summary>
      <p style={{ color: "#475569", lineHeight: 1.7, margin: "10px 0 14px" }}>{description}</p>
      {children}
    </details>
  );
}

function SupportingAnalyticsSurface({ workspaceId }: { workspaceId: string }) {
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <section
        style={{
          backgroundColor: "#eff6ff",
          border: "1px solid #bfdbfe",
          borderRadius: 18,
          display: "grid",
          gap: 8,
          padding: 16,
        }}
      >
        <strong style={{ color: "#0f172a" }}>这里保留 trace、readiness、评测与指标。</strong>
        <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
          这些入口用来解释系统行为，而不是替代主分析流程。看完后可以直接关闭抽屉，回到左侧继续工作。
        </p>
      </section>

      <CollapsibleAnalyticsSection description="快速查看当前工作区的指标、成本和成功率。" open title="指标概览">
        <MetricsPanel workspaceId={workspaceId} />
      </CollapsibleAnalyticsSection>

      <CollapsibleAnalyticsSection description="需要复盘质量或查看评测结果时再展开。" title="readiness 与评测">
        <EvalManager workspaceId={workspaceId} />
      </CollapsibleAnalyticsSection>

      <CollapsibleAnalyticsSection description="查看最近的 trace、任务执行和错误细节。" title="trace 与执行细节">
        <ObservabilityPanel workspaceId={workspaceId} />
      </CollapsibleAnalyticsSection>
    </div>
  );
}

function SupportingSurfaceDrawer({
  children,
  description,
  onClose,
  title,
  width = "min(520px, 100vw)",
}: {
  children: ReactNode;
  description: string;
  onClose: () => void;
  title: string;
  width?: string;
}) {
  return (
    <div
      onClick={onClose}
      style={{
        backgroundColor: "rgba(15, 23, 42, 0.42)",
        backdropFilter: "blur(4px)",
        inset: 0,
        position: "fixed",
        zIndex: 60,
      }}
    >
      <aside
        onClick={(event) => event.stopPropagation()}
        style={{
          background: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,1) 100%)",
          borderLeft: "1px solid #dbe4f0",
          boxShadow: "-18px 0 54px rgba(15, 23, 42, 0.18)",
          height: "100%",
          overflowY: "auto",
          padding: 22,
          position: "absolute",
          right: 0,
          top: 0,
          width,
        }}
      >
        <div
          style={{
            alignItems: "flex-start",
            backdropFilter: "blur(8px)",
            backgroundColor: "rgba(255,255,255,0.92)",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            gap: 16,
            justifyContent: "space-between",
            marginBottom: 18,
            paddingBottom: 16,
            position: "sticky",
            top: 0,
            zIndex: 1,
          }}
        >
          <div style={{ display: "grid", gap: 6 }}>
            <span
              style={{
                color: "#0f172a",
                fontSize: 11,
                fontWeight: 800,
                letterSpacing: 0.8,
                textTransform: "uppercase",
              }}
            >
              辅助面
            </span>
            <strong style={{ color: "#0f172a", fontSize: 18 }}>{title}</strong>
            <p style={{ color: "#475569", margin: 0 }}>{description}</p>
          </div>
          <button onClick={onClose} type="button">
            关闭
          </button>
        </div>
        {children}
      </aside>
    </div>
  );
}

export default function WorkspaceWorkbenchPanel({ workspaceId, initialPanel }: WorkspaceWorkbenchPanelProps) {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [supportingSurface, setSupportingSurface] = useState<SupportingSurface>(getSupportingSurface(initialPanel));
  const [requestedAction, setRequestedAction] = useState<RequestedActionKey>(null);
  const [documentStatus, setDocumentStatus] = useState<DocumentStatusSummary>({
    totalCount: 0,
    readyCount: 0,
    hasFailed: false,
    latestDocumentTitle: null,
  });
  const [conversationStatus, setConversationStatus] = useState<ConversationStatusSummary>({
    entryCount: 0,
    isSubmitting: false,
    currentDraft: "",
    lastTraceId: null,
  });
  const [hasOpenedFormalOutput, setHasOpenedFormalOutput] = useState(false);

  const loadWorkspace = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const loadedWorkspace = await getWorkspace(session.accessToken, workspaceId);
      setWorkspace(loadedWorkspace);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作台信息。");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  useEffect(() => {
    setSupportingSurface(getSupportingSurface(initialPanel));
  }, [initialPanel]);

  const moduleDisplayName = getModuleDisplayName(workspace?.module_type);
  const focusMeta = useMemo(() => getFocusMeta(workspace), [workspace]);
  const quickActions = useMemo(() => getQuickActions(workspace), [workspace]);
  const surfaceMeta = useMemo(
    () => getSupportingSurfaceMeta(supportingSurface, workspace?.module_type),
    [supportingSurface, workspace?.module_type],
  );

  const stageStatus = useMemo(() => {
    if (conversationStatus.isSubmitting) {
      return "分析进行中";
    }
    if (conversationStatus.entryCount > 0) {
      return "已形成初步结论";
    }
    if (documentStatus.totalCount > 0) {
      return "资料已接入，等待开始分析";
    }
    return "等待接入资料";
  }, [conversationStatus.entryCount, conversationStatus.isSubmitting, documentStatus.totalCount]);

  const currentTaskLabel = useMemo(() => {
    const draft = conversationStatus.currentDraft.trim();
    if (!draft) {
      return focusMeta.defaultTaskLabel;
    }
    return draft.length > 54 ? `${draft.slice(0, 54)}...` : draft;
  }, [conversationStatus.currentDraft, focusMeta.defaultTaskLabel]);

  const outputStatus = useMemo(() => {
    if (hasOpenedFormalOutput) {
      return "已打开正式输出面";
    }
    if (conversationStatus.entryCount > 0) {
      return "可以整理正式输出";
    }
    return "先完成一轮分析";
  }, [conversationStatus.entryCount, hasOpenedFormalOutput]);

  const setSurface = (surface: SupportingSurface) => {
    setSupportingSurface(surface);
    const href = surface ? getWorkbenchPanelHref(workspaceId, surface) : `/workspaces/${workspaceId}`;
    router.replace(href, { scroll: false });
  };

  const openActionSurface = (actionKey: RequestedActionKey) => {
    setRequestedAction(actionKey);
    setHasOpenedFormalOutput(true);
    setSurface("tasks");
  };

  const closeSurface = () => {
    setSupportingSurface(null);
  };

  if (!isReady) {
    return <SectionCard title="工作台">正在加载工作台...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能进入工作区工作台。" />;
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <section
        style={{
          background: "linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,1) 100%)",
          border: "1px solid #dbe4f0",
          borderRadius: 24,
          boxShadow: "0 22px 48px rgba(15, 23, 42, 0.08)",
          display: "grid",
          gap: 14,
          padding: 18,
        }}
      >
        <div style={{ alignItems: "start", display: "grid", gap: 14, gridTemplateColumns: "minmax(0, 1fr) minmax(320px, 420px)" }}>
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 8 }}>
              <span
                style={{
                  backgroundColor: "#0f172a",
                  borderRadius: 999,
                  color: "#f8fafc",
                  fontSize: 12,
                  fontWeight: 700,
                  padding: "4px 10px",
                  textTransform: "uppercase",
                }}
              >
                {moduleDisplayName}
              </span>
              <span style={{ color: "#475569", fontSize: 14 }}>工作区：{workspace?.name ?? workspaceId}</span>
              {workspace?.module_config_json.guided_demo === true ? (
                <span style={{ color: "#475569", fontSize: 14 }}>引导演示工作区</span>
              ) : null}
              {isLoading ? <span style={{ color: "#64748b", fontSize: 14 }}>正在同步工作区信息...</span> : null}
            </div>
            <h1 style={{ color: "#0f172a", fontSize: 30, margin: 0 }}>{focusMeta.workflowLabel}</h1>
            <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{focusMeta.headerLead}</p>
            {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          </div>

          <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
            <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 16, display: "grid", gap: 4, padding: 14 }}>
              <span style={{ color: "#64748b", fontSize: 12, fontWeight: 700 }}>当前任务</span>
              <strong style={{ color: "#0f172a", lineHeight: 1.5 }}>{currentTaskLabel}</strong>
            </div>
            <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 16, display: "grid", gap: 4, padding: 14 }}>
              <span style={{ color: "#64748b", fontSize: 12, fontWeight: 700 }}>当前阶段状态</span>
              <strong style={{ color: "#0f172a", lineHeight: 1.5 }}>{stageStatus}</strong>
            </div>
          </div>
        </div>
      </section>

      <div
        style={{
          alignItems: "start",
          display: "grid",
          gap: 18,
          gridTemplateColumns: "minmax(0, 1.52fr) minmax(300px, 0.68fr)",
        }}
      >
        <ChatPanel
          assistantLabel={focusMeta.assistantLabel}
          introBody={focusMeta.introBody}
          introTitle={focusMeta.introTitle}
          onStatusChange={setConversationStatus}
          outputTitle="分析过程与结论"
          placeholder={focusMeta.placeholder}
          primaryActionLabel="开始分析"
          suggestedPrompts={focusMeta.promptSuggestions}
          workflowLabel={focusMeta.workflowLabel}
          workspaceId={workspaceId}
        />

        <aside style={{ display: "grid", gap: 14 }}>
          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>运行状态</div>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>当前研究状态</strong>
            </div>
            <div style={{ display: "grid", gap: 10 }}>
              <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
                <span style={{ color: "#64748b", fontSize: 12 }}>资料状态</span>
                <strong style={{ color: "#0f172a" }}>
                  {documentStatus.totalCount === 0
                    ? "还没有接入资料"
                    : `已接入 ${documentStatus.totalCount} 份资料，${documentStatus.readyCount} 份可直接使用`}
                </strong>
                {documentStatus.latestDocumentTitle ? (
                  <span style={{ color: "#475569", fontSize: 13 }}>最近资料：{documentStatus.latestDocumentTitle}</span>
                ) : null}
              </div>
              <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
                <span style={{ color: "#64748b", fontSize: 12 }}>agent 状态</span>
                <strong style={{ color: "#0f172a" }}>{stageStatus}</strong>
                {conversationStatus.lastTraceId ? (
                  <span style={{ color: "#475569", fontSize: 13 }}>最近 trace：{conversationStatus.lastTraceId}</span>
                ) : (
                  <span style={{ color: "#475569", fontSize: 13 }}>开始分析后，这里会记录最近的 trace。</span>
                )}
              </div>
              <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
                <span style={{ color: "#64748b", fontSize: 12 }}>正式输出</span>
                <strong style={{ color: "#0f172a" }}>{outputStatus}</strong>
                <span style={{ color: "#475569", fontSize: 13 }}>{focusMeta.outputDescription}</span>
              </div>
            </div>
          </section>

          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>当前资料</div>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>资料接入</strong>
            </div>
            <DocumentManager onOpenLibrary={() => setSurface("documents")} onStatusChange={setDocumentStatus} variant="dock" workspaceId={workspaceId} />
          </section>

          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>分析入口</div>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>trace、readiness 与分析</strong>
              <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{focusMeta.analyticsDescription}</p>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              <button onClick={() => setSurface("analytics")} style={pillButtonStyle} type="button">
                查看 trace / readiness
              </button>
            </div>
          </section>

          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>正式输出</div>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>{focusMeta.outputHeading}</strong>
              <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{focusMeta.outputDescription}</p>
            </div>
            <div style={{ display: "grid", gap: 10 }}>
              {quickActions.map((action) => (
                <button
                  key={action.key ?? action.label}
                  onClick={() => openActionSurface(action.key)}
                  style={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #cbd5e1",
                    borderRadius: 16,
                    color: "#0f172a",
                    display: "grid",
                    gap: 4,
                    justifyContent: "start",
                    minHeight: 0,
                    padding: 14,
                    textAlign: "left",
                  }}
                  type="button"
                >
                  <strong>{action.label}</strong>
                  <span style={{ color: "#475569", fontSize: 13 }}>{action.description}</span>
                </button>
              ))}
            </div>
          </section>
        </aside>
      </div>

      {supportingSurface ? (
        <SupportingSurfaceDrawer
          description={surfaceMeta.description}
          onClose={closeSurface}
          title={surfaceMeta.title}
          width={surfaceMeta.width}
        >
          {supportingSurface === "documents" ? <DocumentManager variant="compact" workspaceId={workspaceId} /> : null}
          {supportingSurface === "tasks" ? (
            <TaskWorkbenchByModule requestedAction={requestedAction} workspace={workspace} workspaceId={workspaceId} />
          ) : null}
          {supportingSurface === "analytics" ? <SupportingAnalyticsSurface workspaceId={workspaceId} /> : null}
        </SupportingSurfaceDrawer>
      ) : null}
    </div>
  );
}
