"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import {
  getWorkbenchPanelHref,
  workbenchPanels,
  type WorkbenchPanelId,
} from "../../lib/navigation";
import type { ModuleType, Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import ChatPanel from "../chat/chat-panel";
import DocumentManager from "../documents/document-manager";
import PublicDemoWorkbenchContinuityNote from "../public-demo/public-demo-workbench-continuity-note";
import ResearchAssistantPanel from "../research/research-assistant-panel";
import SupportCaseWorkbenchSection from "../support/support-case-workbench-section";
import SupportCopilotPanel from "../support/support-copilot-panel";
import SectionCard from "../ui/section-card";
import JobAssistantActionPanel from "../job/job-assistant-action-panel";
import JobHiringWorkbenchSection from "../job/job-hiring-workbench-section";
import type { JobHiringPacketContinuationDraft, SupportCaseContinuationDraft } from "../../lib/types";

type WorkspaceWorkbenchPanelProps = {
  workspaceId: string;
  initialPanel?: WorkbenchPanelId;
};

const MODULE_PRODUCT_NAMES: Record<ModuleType, string> = {
  research: "Research Assistant",
  support: "Support Copilot",
  job: "Job Assistant",
};

function getModuleDisplayName(moduleType?: string | null): string {
  if (!moduleType) {
    return "未配置模块";
  }

  return MODULE_PRODUCT_NAMES[moduleType as ModuleType] ?? moduleType;
}

function getDefaultPanel(moduleType?: string | null): WorkbenchPanelId {
  if (moduleType === "support" || moduleType === "job") {
    return "tasks";
  }

  return "documents";
}

function getWorkbenchGuidance(workspace: Workspace | null) {
  if (!workspace) {
    return "先从你当前最需要的区域开始：补材料、验证回答，或者直接执行任务。";
  }

  if (workspace.module_type === "support") {
    return "如果这是已有问题，直接切到“任务”区域，从 Support case 工作台继续。第一次演示时，再按文档 -> 对话 -> 任务的顺序走一遍。";
  }

  if (workspace.module_type === "job") {
    return "如果这是已有招聘包，直接切到“任务”区域，从 Job hiring packet 工作台继续。第一次演示时，再按文档 -> 对话 -> 任务的顺序走一遍。";
  }

  return "Research 最适合先确认材料，再用对话验证 grounded 回答，最后进入任务生成结构化结果。";
}

function getPanelDescription(panelId: WorkbenchPanelId) {
  return workbenchPanels.find((panel) => panel.id === panelId)?.description ?? "";
}

function SupportTaskWorkbench({ workspaceId }: { workspaceId: string }) {
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
        workspaceId={workspaceId}
      />
    </>
  );
}

function JobTaskWorkbench({ workspaceId }: { workspaceId: string }) {
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
        workspaceId={workspaceId}
      />
    </>
  );
}

function ResearchTaskWorkbench({ workspaceId }: { workspaceId: string }) {
  return <ResearchAssistantPanel workspaceId={workspaceId} />;
}

function TaskWorkbenchByModule({ workspaceId, workspace }: { workspaceId: string; workspace: Workspace | null }) {
  if (!workspace) {
    return <SectionCard title="任务">正在加载当前模块...</SectionCard>;
  }

  if (workspace.module_type === "support") {
    return <SupportTaskWorkbench workspaceId={workspaceId} />;
  }

  if (workspace.module_type === "job") {
    return <JobTaskWorkbench workspaceId={workspaceId} />;
  }

  return <ResearchTaskWorkbench workspaceId={workspaceId} />;
}

export default function WorkspaceWorkbenchPanel({ workspaceId, initialPanel }: WorkspaceWorkbenchPanelProps) {
  const router = useRouter();
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentPanel, setCurrentPanel] = useState<WorkbenchPanelId>(initialPanel ?? "documents");

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
      setCurrentPanel((current) => initialPanel ?? current ?? getDefaultPanel(loadedWorkspace.module_type));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作台信息");
    } finally {
      setIsLoading(false);
    }
  }, [initialPanel, session, workspaceId]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  useEffect(() => {
    if (initialPanel) {
      setCurrentPanel(initialPanel);
    }
  }, [initialPanel]);

  const guidance = useMemo(() => getWorkbenchGuidance(workspace), [workspace]);
  const moduleDisplayName = getModuleDisplayName(workspace?.module_type);

  const handleSelectPanel = (panelId: WorkbenchPanelId) => {
    setCurrentPanel(panelId);
    router.replace(getWorkbenchPanelHref(workspaceId, panelId), { scroll: false });
  };

  if (!isReady) {
    return <SectionCard title="工作台">正在加载工作台...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能进入工作区工作台。" />;
  }

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <SectionCard
        title="主工作台"
        description="文档、对话和任务现在都在同一个工作区页面里完成。你不需要先判断自己该进哪个页面，只需要切到当前要用的区域。"
      >
        <div style={{ display: "grid", gap: 14 }}>
          <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10 }}>
            <span
              style={{
                backgroundColor: "#0f172a12",
                borderRadius: 999,
                color: "#0f172a",
                fontSize: 12,
                fontWeight: 700,
                padding: "4px 10px",
                textTransform: "uppercase",
              }}
            >
              {moduleDisplayName}
            </span>
            {workspace?.module_config_json.guided_demo === true ? (
              <span style={{ color: "#475569", fontSize: 14 }}>这是一个引导演示工作区。</span>
            ) : null}
          </div>
          <p style={{ color: "#334155", margin: 0 }}>{guidance}</p>
          {errorMessage ? <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p> : null}
        </div>
      </SectionCard>

      <SectionCard title="选择当前区域" description="只打开你现在需要的区域。需要切换时，直接在这里换，不用离开工作台。">
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          }}
        >
          {workbenchPanels.map((panel) => {
            const isActive = panel.id === currentPanel;
            return (
              <button
                key={panel.id}
                onClick={() => handleSelectPanel(panel.id)}
                style={{
                  backgroundColor: isActive ? "#0f172a" : "#ffffff",
                  border: `1px solid ${isActive ? "#0f172a" : "#cbd5e1"}`,
                  borderRadius: 16,
                  color: isActive ? "#ffffff" : "#0f172a",
                  cursor: "pointer",
                  display: "grid",
                  gap: 6,
                  padding: 16,
                  textAlign: "left",
                }}
                type="button"
              >
                <strong>{panel.label}</strong>
                <span style={{ color: isActive ? "#e2e8f0" : "#475569", fontSize: 13 }}>{panel.description}</span>
              </button>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard
        title={`当前区域：${workbenchPanels.find((panel) => panel.id === currentPanel)?.label ?? currentPanel}`}
        description={getPanelDescription(currentPanel)}
      >
        {isLoading && !workspace ? <p>正在加载工作台内容...</p> : null}
        {!isLoading && currentPanel === "documents" ? <DocumentManager variant="compact" workspaceId={workspaceId} /> : null}
        {!isLoading && currentPanel === "chat" ? <ChatPanel workspaceId={workspaceId} /> : null}
        {!isLoading && currentPanel === "tasks" ? <TaskWorkbenchByModule workspace={workspace} workspaceId={workspaceId} /> : null}
      </SectionCard>
    </div>
  );
}

