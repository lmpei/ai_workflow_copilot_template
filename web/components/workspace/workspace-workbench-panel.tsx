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
  ResearchAnalysisRunStatus,
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

type ChatModeOption = {
  value: "rag" | "research_tool_assisted";
  label: string;
  description: string;
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
  chatModes?: ChatModeOption[];
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
  latestAnalysisRunId: string | null;
  latestAnalysisRunStatus: ResearchAnalysisRunStatus | null;
  latestAnalysisRunQuestion: string | null;
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
    return "Module not configured";
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
      workflowLabel: "Research Workflow",
      introTitle: "Start from one research question",
      introBody: "Pick one prompt or type your own question, then start the analysis.",
      defaultTaskLabel: "Form the next research judgment from current material",
      placeholder:
        "For example: summarize the strongest market signals in the current material and tell me what evidence is still missing before we can make a formal conclusion.",
      promptSuggestions: [
        "Summarize the most important findings in the current material.",
        "Tell me which missing material would unblock the next research step.",
        "Point out which conclusions are still weak and need more verification.",
      ],
      outputHeading: "Formal outputs",
      outputDescription: "After one analysis pass, turn it into a research summary or a formal report.",
      analyticsDescription: "Open trace, readiness, and deeper analysis only when you need to explain the process.",
      headerLead: "Move this research pass forward through material, analysis, and final output.",
      chatModes: [
        {
          value: "rag",
          label: "Standard analysis",
          description: "Use the current material directly for one grounded analysis pass.",
        },
        {
          value: "research_tool_assisted",
          label: "Tool-assisted pilot",
          description: "Create a background analysis run, inspect the tool steps, and keep the research workflow visible while it executes.",
        },
      ],
    };
  }

  if (workspace.module_type === "support") {
    return {
      assistantLabel: "Support Copilot",
      workflowLabel: "Support workflow",
      introTitle: "Clarify the case first",
      introBody: "Start from one key question, confirm facts and evidence, then decide whether to summarize, reply, or escalate.",
      defaultTaskLabel: "Advance the next support judgment from the current case",
      placeholder:
        "For example: summarize the most important facts in this case and tell me whether we should continue follow-up, draft a reply, or prepare escalation.",
      promptSuggestions: [
        "Summarize the core issue and evidence in this case.",
        "If we need to reply now, what still needs confirmation first?",
        "Is this case better suited for follow-up or escalation right now?",
      ],
      outputHeading: "Case outputs",
      outputDescription: "After one pass, generate a ticket summary, a reply draft, or continue the current case.",
      analyticsDescription: "Open analysis only when you need trace, readiness, or deeper explanation.",
      headerLead: "Move the support work forward through facts, response quality, and escalation decisions.",
    };
  }

  return {
    assistantLabel: "Job Assistant",
    workflowLabel: "Hiring workflow",
    introTitle: "Clarify the role and candidate pool first",
    introBody: "Start from one hiring question, then decide whether to review candidates or refresh the shortlist.",
    defaultTaskLabel: "Form the next hiring judgment from the current packet",
    placeholder:
      "For example: summarize the biggest judgment risk in this hiring packet and tell me whether we should review more candidates or refresh the shortlist.",
    promptSuggestions: [
      "Summarize the biggest judgment risk in this hiring packet.",
      "If we need to move the shortlist forward now, what material is still missing?",
      "Based on the current material, what should we verify first about the role and candidate pool?",
    ],
    outputHeading: "Formal outputs",
    outputDescription: "After one pass, generate a role summary, review candidates, or refresh the shortlist.",
    analyticsDescription: "Open analysis only when you need trace, readiness, or explanation for a result.",
    headerLead: "Move the hiring work forward through role context, candidate evidence, and shortlist decisions.",
  };
}

function getQuickActions(workspace: Workspace | null): QuickAction[] {
  if (!workspace || workspace.module_type === "research") {
    return [
      {
        key: "research:open",
        label: "Generate research summary or report",
        description: "Turn the current analysis into a formal research output.",
      },
    ];
  }

  if (workspace.module_type === "support") {
    return [
      {
        key: "support:ticket_summary",
        label: "Generate ticket summary",
        description: "Summarize the case, evidence, and next decision.",
      },
      {
        key: "support:reply_draft",
        label: "Generate reply draft",
        description: "Draft a response from the current grounded material.",
      },
    ];
  }

  return [
    {
      key: "job:jd_summary",
      label: "Generate role summary",
      description: "Clarify role requirements, context, and gaps.",
    },
    {
      key: "job:resume_match",
      label: "Review candidates or refresh shortlist",
      description: "Continue the current packet and move shortlist work forward.",
    },
  ];
}

function getSupportingSurfaceMeta(surface: SupportingSurface, moduleType?: string | null): SupportingSurfaceMeta {
  if (surface === "documents") {
    return {
      title: "Document library",
      description: "Open this only when you need to upload more material, inspect status, or reindex manually.",
      width: "min(560px, 100vw)",
    };
  }

  if (surface === "tasks") {
    if (moduleType === "support") {
      return {
        title: "Case outputs and follow-up",
        description: "Continue an existing case or generate summary and reply outputs.",
        width: "min(660px, 100vw)",
      };
    }

    if (moduleType === "job") {
      return {
        title: "Hiring review and shortlist",
        description: "Continue the current hiring packet or advance candidate review and shortlist work.",
        width: "min(660px, 100vw)",
      };
    }

    return {
      title: "Formal research outputs",
      description: "Keep research summaries and formal reports here instead of on the main work surface.",
      width: "min(660px, 100vw)",
    };
  }

  if (surface === "analytics") {
    return {
      title: "Analysis and traces",
      description: "Open this only when you need to explain system behavior, not as the default workspace path.",
      width: "min(620px, 100vw)",
    };
  }

  return {
    title: "Main workbench",
    description: "The primary surface stays on the main workflow.",
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
    return <SectionCard title="Formal outputs">Loading module output surface...</SectionCard>;
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
        <strong style={{ color: "#0f172a" }}>This drawer keeps trace, readiness, eval, and metrics together.</strong>
        <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>
          Use it when you need to explain system behavior, then close it and return to the main workflow.
        </p>
      </section>

      <CollapsibleAnalyticsSection description="See top-line workspace metrics, latency, and cost." open title="Metrics overview">
        <MetricsPanel workspaceId={workspaceId} />
      </CollapsibleAnalyticsSection>

      <CollapsibleAnalyticsSection description="Open readiness and eval detail only when you need deeper quality review." title="Readiness and evals">
        <EvalManager workspaceId={workspaceId} />
      </CollapsibleAnalyticsSection>

      <CollapsibleAnalyticsSection description="Inspect recent traces, task execution, and error detail." title="Trace and execution detail">
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
              Supporting surface
            </span>
            <strong style={{ color: "#0f172a", fontSize: 18 }}>{title}</strong>
            <p style={{ color: "#475569", margin: 0 }}>{description}</p>
          </div>
          <button onClick={onClose} type="button">
            Close
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
    latestAnalysisRunId: null,
    latestAnalysisRunStatus: null,
    latestAnalysisRunQuestion: null,
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
      setErrorMessage(isApiClientError(error) ? error.message : "Unable to load the workspace.");
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
    if (conversationStatus.latestAnalysisRunStatus === "pending") {
      return "Background analysis queued";
    }
    if (conversationStatus.latestAnalysisRunStatus === "running") {
      return "Background analysis running";
    }
    if (conversationStatus.latestAnalysisRunStatus === "degraded") {
      return "Analysis completed with honest degradation";
    }
    if (conversationStatus.latestAnalysisRunStatus === "completed") {
      return "Background analysis completed";
    }
    if (conversationStatus.latestAnalysisRunStatus === "failed") {
      return "Background analysis failed";
    }
    if (conversationStatus.isSubmitting) {
      return "Analysis in progress";
    }
    if (conversationStatus.entryCount > 0) {
      return "Initial conclusion available";
    }
    if (documentStatus.totalCount > 0) {
      return "Material ready for analysis";
    }
    return "Waiting for material";
  }, [conversationStatus.entryCount, conversationStatus.isSubmitting, conversationStatus.latestAnalysisRunStatus, documentStatus.totalCount]);

  const currentTaskLabel = useMemo(() => {
    const latestRunQuestion = conversationStatus.latestAnalysisRunQuestion?.trim();
    if (latestRunQuestion) {
      return latestRunQuestion.length > 54 ? `${latestRunQuestion.slice(0, 54)}...` : latestRunQuestion;
    }
    const draft = conversationStatus.currentDraft.trim();
    if (!draft) {
      return focusMeta.defaultTaskLabel;
    }
    return draft.length > 54 ? `${draft.slice(0, 54)}...` : draft;
  }, [conversationStatus.currentDraft, conversationStatus.latestAnalysisRunQuestion, focusMeta.defaultTaskLabel]);

  const outputStatus = useMemo(() => {
    if (hasOpenedFormalOutput) {
      return "Formal output surface opened";
    }
    if (conversationStatus.latestAnalysisRunStatus === "completed" || conversationStatus.latestAnalysisRunStatus === "degraded") {
      return "Ready to package the latest background run";
    }
    if (conversationStatus.entryCount > 0) {
      return "Ready to package a formal output";
    }
    return "Complete one analysis pass first";
  }, [conversationStatus.entryCount, conversationStatus.latestAnalysisRunStatus, hasOpenedFormalOutput]);

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
    return <SectionCard title="Workbench">Loading workspace...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="Sign in before entering the workspace workbench." />;
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
              <span style={{ color: "#475569", fontSize: 14 }}>Workspace: {workspace?.name ?? workspaceId}</span>
              {workspace?.module_config_json.guided_demo === true ? (
                <span style={{ color: "#475569", fontSize: 14 }}>Guided demo workspace</span>
              ) : null}
              {isLoading ? <span style={{ color: "#64748b", fontSize: 14 }}>Refreshing workspace context...</span> : null}
            </div>
            <h1 style={{ color: "#0f172a", fontSize: 30, margin: 0 }}>{focusMeta.workflowLabel}</h1>
            <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{focusMeta.headerLead}</p>
            {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
          </div>

          <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
            <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 16, display: "grid", gap: 4, padding: 14 }}>
              <span style={{ color: "#64748b", fontSize: 12, fontWeight: 700 }}>Current task</span>
              <strong style={{ color: "#0f172a", lineHeight: 1.5 }}>{currentTaskLabel}</strong>
            </div>
            <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 16, display: "grid", gap: 4, padding: 14 }}>
              <span style={{ color: "#64748b", fontSize: 12, fontWeight: 700 }}>Current stage</span>
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
          outputTitle="Analysis flow and conclusions"
          placeholder={focusMeta.placeholder}
          primaryActionLabel="Start analysis"
          suggestedPrompts={focusMeta.promptSuggestions}
          modes={focusMeta.chatModes}
          supportsBackgroundRuns={workspace?.module_type === "research"}
          workflowLabel={focusMeta.workflowLabel}
          workspaceId={workspaceId}
        />

        <aside style={{ display: "grid", gap: 14 }}>
          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Run state</div>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>Current workflow state</strong>
            </div>
            <div style={{ display: "grid", gap: 10 }}>
              <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
                <span style={{ color: "#64748b", fontSize: 12 }}>Material</span>
                <strong style={{ color: "#0f172a" }}>
                  {documentStatus.totalCount === 0
                    ? "No connected material yet"
                    : `${documentStatus.totalCount} documents connected, ${documentStatus.readyCount} ready for direct use`}
                </strong>
                {documentStatus.latestDocumentTitle ? (
                  <span style={{ color: "#475569", fontSize: 13 }}>Latest: {documentStatus.latestDocumentTitle}</span>
                ) : null}
              </div>
              <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
                <span style={{ color: "#64748b", fontSize: 12 }}>Trace state</span>
                <strong style={{ color: "#0f172a" }}>{stageStatus}</strong>
                {conversationStatus.latestAnalysisRunId ? (
                  <span style={{ color: "#475569", fontSize: 13 }}>Latest run: {conversationStatus.latestAnalysisRunId}</span>
                ) : null}
                {conversationStatus.lastTraceId ? (
                  <span style={{ color: "#475569", fontSize: 13 }}>Latest trace: {conversationStatus.lastTraceId}</span>
                ) : (
                  <span style={{ color: "#475569", fontSize: 13 }}>A trace id will appear here after analysis starts.</span>
                )}
              </div>
              <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 14, display: "grid", gap: 4, padding: 12 }}>
                <span style={{ color: "#64748b", fontSize: 12 }}>Formal output</span>
                <strong style={{ color: "#0f172a" }}>{outputStatus}</strong>
                <span style={{ color: "#475569", fontSize: 13 }}>{focusMeta.outputDescription}</span>
              </div>
            </div>
          </section>

          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Current material</div>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>Document intake</strong>
            </div>
            <DocumentManager onOpenLibrary={() => setSurface("documents")} onStatusChange={setDocumentStatus} variant="dock" workspaceId={workspaceId} />
          </section>

          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Analysis entry</div>
              <strong style={{ color: "#0f172a", fontSize: 18 }}>Trace, readiness, and deeper analysis</strong>
              <p style={{ color: "#475569", lineHeight: 1.7, margin: 0 }}>{focusMeta.analyticsDescription}</p>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              <button onClick={() => setSurface("analytics")} style={pillButtonStyle} type="button">
                Open trace and readiness
              </button>
            </div>
          </section>

          <section style={sideCardStyle}>
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ color: "#64748b", fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>Formal outputs</div>
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
