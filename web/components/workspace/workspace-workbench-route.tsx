"use client";

import { useCallback, useEffect, useState } from "react";

import { getWorkspace, isApiClientError } from "../../lib/api";
import type { Workspace } from "../../lib/types";
import AuthRequired from "../auth/auth-required";
import { useAuthSession } from "../auth/use-auth-session";
import AiHotTrackerWorkspace from "../research/ai-hot-tracker-workspace";
import SectionCard from "../ui/section-card";
import WorkspacePageShell from "./workspace-page-shell";
import WorkspaceWorkbenchPanel from "./workspace-workbench-panel";

type WorkspaceWorkbenchRouteProps = {
  initialPanel?: string;
  workspaceId: string;
};

export default function WorkspaceWorkbenchRoute({ initialPanel, workspaceId }: WorkspaceWorkbenchRouteProps) {
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
      const loadedWorkspace = await getWorkspace(session.accessToken, workspaceId);
      setWorkspace(loadedWorkspace);
    } catch (error) {
      setErrorMessage(isApiClientError(error) ? error.message : "无法加载这个工作区。");
    } finally {
      setIsLoading(false);
    }
  }, [session, workspaceId]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  if (!isReady) {
    return <SectionCard title="工作区">正在加载工作区...</SectionCard>;
  }

  if (!session) {
    return <AuthRequired description="登录后才能查看工作区内容。" />;
  }

  if (!workspace) {
    return <SectionCard title="工作区">{isLoading ? "正在加载工作区..." : errorMessage ?? "暂时无法读取工作区。"}</SectionCard>;
  }

  if (workspace.module_type === "research") {
    return <AiHotTrackerWorkspace workspace={workspace} workspaceId={workspaceId} />;
  }

  return (
    <WorkspacePageShell
      description="这是当前工作区的主工作台。对话是主中心，资料、动作和分析只在需要时以辅助视图方式唤出。"
      page="workbench"
      title="工作台"
      workspaceId={workspaceId}
    >
      <WorkspaceWorkbenchPanel initialPanel={initialPanel} workspaceOverride={workspace} workspaceId={workspaceId} />
    </WorkspacePageShell>
  );
}
