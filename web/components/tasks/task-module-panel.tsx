"use client";

import { useCallback, useEffect, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import type { Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import JobAssistantPanel from "../job/job-assistant-panel";
import JobHiringWorkbenchSection from "../job/job-hiring-workbench-section";
import PublicDemoWorkbenchContinuityNote from "../public-demo/public-demo-workbench-continuity-note";
import ResearchAssistantPanel from "../research/research-assistant-panel";
import SupportCaseWorkbenchSection from "../support/support-case-workbench-section";
import SupportCopilotPanel from "../support/support-copilot-panel";
import SectionCard from "../ui/section-card";

type TaskModulePanelProps = {
  workspaceId: string;
};

const MODULE_PRODUCT_NAMES: Record<string, string> = {
  research: "Research Assistant",
  support: "Support Copilot",
  job: "Job Assistant",
};

function getModuleDisplayName(moduleType: string): string {
  return MODULE_PRODUCT_NAMES[moduleType] ?? moduleType;
}

export default function TaskModulePanel({ workspaceId }: TaskModulePanelProps) {
  const { session, isReady } = useAuthSession();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    if (!session) {
      setWorkspace(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      setWorkspace(await getWorkspace(session.accessToken, workspaceId));
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载工作区模块");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  if (!isReady) {
    return <SectionCard title="模块任务">正在加载会话...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能运行场景任务。" />;
  }

  if (isLoading) {
    return <SectionCard title="模块任务">正在加载工作区模块...</SectionCard>;
  }

  if (errorMessage) {
    return (
      <SectionCard title="模块任务" description="任务面板依赖当前工作区的模块配置。">
        <p style={{ color: "#b91c1c", margin: 0 }}>{errorMessage}</p>
      </SectionCard>
    );
  }

  if (workspace?.module_type === "support") {
    return (
      <>
        <PublicDemoWorkbenchContinuityNote moduleType="support" />
        <SupportCaseWorkbenchSection
          workspaceId={workspaceId}
          accessToken={session.accessToken}
          onOpenTask={(taskId) => {
            if (typeof window !== "undefined") {
              window.location.hash = `task-${taskId}`;
            }
          }}
        />
        <SupportCopilotPanel workspaceId={workspaceId} />
      </>
    );
  }

  if (workspace?.module_type === "job") {
    return (
      <>
        <PublicDemoWorkbenchContinuityNote moduleType="job" />
        <JobHiringWorkbenchSection
          workspaceId={workspaceId}
          accessToken={session.accessToken}
          onOpenTask={(taskId) => {
            if (typeof window !== "undefined") {
              window.location.hash = `job-task-${taskId}`;
            }
          }}
        />
        <JobAssistantPanel workspaceId={workspaceId} />
      </>
    );
  }

  if (workspace?.module_type === "research") {
    return <ResearchAssistantPanel workspaceId={workspaceId} />;
  }

  return (
    <SectionCard title="模块任务" description="随着各场景继续深化，这里会逐步收成更明确的模块专属任务体验。">
      <p>
        当前工作区配置的是 <strong>{getModuleDisplayName(workspace?.module_type ?? "unknown")}</strong>。
        这个模块的专属任务面板暂时还不可用。
      </p>
    </SectionCard>
  );
}
